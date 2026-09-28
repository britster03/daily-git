import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.compare_files import compare_files


class CompareFilesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.left = Path(self.directory.name) / "left file.bin"
        self.right = Path(self.directory.name) / "right file.bin"

    def test_equal_empty_and_binary_files(self):
        for data in [b"", bytes(range(256)) * 100]:
            with self.subTest(length=len(data)):
                self.left.write_bytes(data)
                self.right.write_bytes(data)
                result = compare_files(self.left, self.right, chunk_size=7)
                self.assertEqual(result, dict(equal=True, offset=None, left_byte=None, right_byte=None))

    def test_first_difference_across_boundaries(self):
        for offset in [0, 6, 7, 8, 20]:
            with self.subTest(offset=offset):
                a = b"a" * 21
                b = a[:offset] + b"b" + a[offset + 1:]
                self.left.write_bytes(a)
                self.right.write_bytes(b)
                self.assertEqual(compare_files(self.left, self.right, 7),
                                 dict(equal=False, offset=offset, left_byte=97, right_byte=98))

    def test_prefix_and_eof_in_both_directions(self):
        for prefix in [b"", b"abc", b"a" * 7]:
            with self.subTest(length=len(prefix)):
                self.left.write_bytes(prefix)
                self.right.write_bytes(prefix + b"x")
                self.assertEqual(compare_files(self.left, self.right, 7),
                                 dict(equal=False, offset=len(prefix), left_byte=None, right_byte=120))
                self.assertEqual(compare_files(self.right, self.left, 7),
                                 dict(equal=False, offset=len(prefix), left_byte=120, right_byte=None))

    def test_earlier_difference_wins_over_length(self):
        self.left.write_bytes(b"abc")
        self.right.write_bytes(b"axcd")
        self.assertEqual(compare_files(self.left, self.right)["offset"], 1)

    def test_cli_exit_codes_and_no_modifications(self):
        script = Path(__file__).resolve().parents[1] / "tools" / "compare_files.py"
        def run():
            return subprocess.run([sys.executable, str(script), str(self.left), str(self.right)],
                                  capture_output=True, text=True)
        self.left.write_bytes(b"same")
        self.right.write_bytes(b"same")
        self.assertEqual(run().returncode, 0)
        self.right.write_bytes(b"different")
        result = run()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["offset"], 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(self.left.read_bytes(), b"same")
        self.assertEqual(self.right.read_bytes(), b"different")
        self.right.unlink()
        result = run()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Unable to compare files", result.stderr)


if __name__ == "__main__":
    unittest.main()
