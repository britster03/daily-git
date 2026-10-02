import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.newline_report import inspect_stream


class NewlineReportTests(unittest.TestCase):
    def test_stdin_preserves_line_endings_and_policy_status(self):
        script = Path(__file__).resolve().parents[1] / 'tools/newline_report.py'
        for data, code in [(b'', 0), (b'a\n', 0), (b'a\r\nb\n', 1), (b'last', 1)]:
            with self.subTest(data=data):
                result = subprocess.run([sys.executable, str(script), '-', '--expect', 'lf',
                                         '--require-final-newline'], input=data, capture_output=True)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(json.loads(result.stdout), inspect_stream(io.BytesIO(data)))

    def test_literal_dash_path(self):
        script = Path(__file__).resolve().parents[1] / 'tools/newline_report.py'
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / '-').write_bytes(b'file\r\n')
            result = subprocess.run([sys.executable, str(script), './-'], cwd=directory,
                                    input=b'stdin\n', capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['crlf'], 1)

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

    def test_cli_line_ending_policies(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "newline_report.py"
        cases = [
            (b"a\n", ["--expect", "lf", "--require-final-newline"], 0),
            (b"a\r\n", ["--expect", "crlf"], 0),
            (b"a\r", ["--expect", "cr"], 0),
            (b"a\r\nb\n", ["--expect", "lf"], 1),
            (b"a\n", ["--expect", "crlf"], 1),
            (b"a\r\nlast", ["--expect", "lf", "--require-final-newline"], 1),
            (b"last", ["--expect", "lf"], 0),
            (b"last", ["--require-final-newline"], 1),
            (b"", ["--expect", "lf", "--require-final-newline"], 0),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            for data, flags, expected in cases:
                with self.subTest(data=data, flags=flags):
                    path.write_bytes(data)
                    result = subprocess.run([sys.executable, str(script), str(path), *flags],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, expected, result.stderr)
                    self.assertEqual(json.loads(result.stdout)["bytes"], len(data))
                    self.assertEqual(bool(result.stderr), bool(expected))
                    self.assertEqual(path.read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
