import contextlib
import hashlib
import io
import tempfile
import unittest
from pathlib import Path

from tools.file_checksum import main, sha256_file


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


if __name__ == "__main__":
    unittest.main()
