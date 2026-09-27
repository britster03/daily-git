import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.newline_report import inspect_stream


class NewlineReportTests(unittest.TestCase):
    def test_endings_across_chunk_boundaries(self):
        data = b"a\r\nb\nc\rd\r\nlast"
        expected = dict(bytes=len(data), lf=1, crlf=2, cr=1, lines=5,
                        ends_with_newline=False, mixed_endings=True)
        for size in range(1, len(data) + 1):
            with self.subTest(size=size):
                self.assertEqual(inspect_stream(io.BytesIO(data), size), expected)

    def test_empty_and_single_lines(self):
        for data, lines, ends in [(b"", 0, False), (b"abc", 1, False),
                                  (b"\n", 1, True), (b"\r", 1, True),
                                  (b"\r\n", 1, True), (b"a\n\n", 2, True)]:
            with self.subTest(data=data):
                report = inspect_stream(io.BytesIO(data), 1)
                self.assertEqual(report["lines"], lines)
                self.assertEqual(report["ends_with_newline"], ends)
                self.assertFalse(report["mixed_endings"])

    def test_repeated_cr_before_lf(self):
        report = inspect_stream(io.BytesIO(b"\r\r\n"), 1)
        self.assertEqual((report["cr"], report["crlf"], report["lf"]), (1, 1, 0))

    def test_binary_bytes_are_not_decoded(self):
        report = inspect_stream(io.BytesIO(b"\xff\x00\n"))
        self.assertEqual(report["bytes"], 3)
        self.assertEqual(report["lf"], 1)

    def test_cli_and_missing_file(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "newline_report.py"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "line endings.txt"
            original = b"a\r\nb\n"
            path.write_bytes(original)
            result = subprocess.run([sys.executable, str(script), str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["mixed_endings"])
            self.assertEqual(path.read_bytes(), original)
            path.unlink()
            result = subprocess.run([sys.executable, str(script), str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertIn("Unable to read file", result.stderr)


if __name__ == "__main__":
    unittest.main()
