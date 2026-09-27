import contextlib
import hashlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.file_checksum import main, sha256_file, sha256_stream


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "file_checksum.py"


class FileChecksumTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "sample with spaces.bin"

    def run_cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main([str(self.path), *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_known_digest(self):
        self.path.write_bytes(b"abc")
        expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        self.assertEqual(sha256_file(self.path), expected)
        self.assertEqual(self.run_cli(), (0, expected + "\n", ""))

    def test_empty_file(self):
        self.path.write_bytes(b"")
        self.assertEqual(sha256_file(self.path), hashlib.sha256(b"").hexdigest())

    def test_multiple_chunks_of_binary_data(self):
        data = bytes(range(256)) * 10000
        self.path.write_bytes(data)
        self.assertEqual(sha256_file(self.path), hashlib.sha256(data).hexdigest())

    def test_uppercase_expected_digest(self):
        self.path.write_bytes(b"abc")
        code, stdout, stderr = self.run_cli("--expect", hashlib.sha256(b"abc").hexdigest().upper())
        self.assertEqual((code, stdout, stderr), (0, "OK: checksum matches\n", ""))

    def test_mismatch(self):
        self.path.write_bytes(b"abc")
        code, stdout, stderr = self.run_cli("--expect", "0" * 64)
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("MISMATCH", stderr)

    def test_missing_file(self):
        code, stdout, stderr = self.run_cli()
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("Unable to read file", stderr)

    def test_directory_input(self):
        self.path.mkdir()
        self.assertEqual(self.run_cli()[0], 2)

    def test_invalid_expected_digest(self):
        for value in ["", "abc", "g" * 64, "0" * 65]:
            with self.subTest(value=value), self.assertRaises(SystemExit) as raised:
                self.run_cli("--expect", value)
            self.assertEqual(raised.exception.code, 2)

    def test_stream_reads_bounded_chunks_and_leaves_stream_open(self):
        class BoundedStream(io.BytesIO):
            def read(self, size=-1):
                if not 0 < size <= 1024 * 1024:
                    raise AssertionError("unbounded read")
                return super().read(size)

        data = b"abc" * 1000000
        with BoundedStream(data) as stream:
            self.assertEqual(sha256_stream(stream), hashlib.sha256(data).hexdigest())
            self.assertFalse(stream.closed)

    def test_binary_stdin_including_empty_input(self):
        for data in [b"", bytes(range(256)) * 10000]:
            with self.subTest(length=len(data)):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "-"], input=data, capture_output=True
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.decode(), hashlib.sha256(data).hexdigest() + "\n")

    def test_stdin_verification(self):
        for expected, code in [(hashlib.sha256(b"abc").hexdigest(), 0), ("0" * 64, 1)]:
            with self.subTest(code=code):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "-", "--expect", expected],
                    input=b"abc", capture_output=True,
                )
                self.assertEqual(result.returncode, code, result.stderr)

    def test_literal_dash_filename(self):
        (Path(self.directory.name) / "-").write_bytes(b"file contents")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "./-"], cwd=self.directory.name,
            input=b"different stdin", capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.decode(), hashlib.sha256(b"file contents").hexdigest() + "\n")

    def test_additional_algorithms_for_files_and_stdin(self):
        data = b"abc"
        self.path.write_bytes(data)
        for algorithm in ["sha512", "blake2b"]:
            with self.subTest(algorithm=algorithm):
                expected = hashlib.new(algorithm, data).hexdigest()
                self.assertEqual(self.run_cli("--algorithm", algorithm), (0, expected + "\n", ""))
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "-", "--algorithm", algorithm,
                     "--expect", expected.upper()], input=data, capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, b"OK: checksum matches\n")
                code, stdout, stderr = self.run_cli("--algorithm", algorithm, "--expect", "0" * 128)
                self.assertEqual((code, stdout), (1, ""))
                self.assertIn("MISMATCH", stderr)

    def test_digest_length_matches_algorithm(self):
        for algorithm, length in [("sha256", 128), ("sha512", 64), ("blake2b", 64)]:
            with self.subTest(algorithm=algorithm), self.assertRaises(SystemExit) as raised:
                self.run_cli("--algorithm", algorithm, "--expect", "0" * length)
            self.assertEqual(raised.exception.code, 2)

    def test_unsupported_algorithm(self):
        with self.assertRaises(SystemExit) as raised:
            self.run_cli("--algorithm", "not-a-hash")
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
