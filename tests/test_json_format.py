import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.json_format import format_json


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "json_format.py"


class JsonFormatTests(unittest.TestCase):
    def test_pretty_print(self):
        self.assertEqual(format_json('{"b":2,"a":1}'), '{\n  "b": 2,\n  "a": 1\n}\n')

    def test_recursive_sort_and_compact(self):
        self.assertEqual(
            format_json('{"z":{"b":2,"a":1},"a":[]}', sort_keys=True, compact=True),
            '{"a":[],"z":{"a":1,"b":2}}\n',
        )

    def test_scalar_roots_and_unicode(self):
        for source in ['null', 'true', '42', '"café"', '[1,"\u2603"]']:
            with self.subTest(source=source):
                self.assertEqual(json.loads(format_json(source)), json.loads(source))

    def test_duplicate_keys_including_nested_and_escaped(self):
        for source in ['{"a":1,"a":2}', '{"outer":{"x":1,"x":2}}', r'{"a":1,"\u0061":2}']:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, "duplicate object key"):
                format_json(source)

    def test_same_key_in_separate_objects_is_valid(self):
        self.assertEqual(format_json('[{"a":1},{"a":2}]', compact=True), '[{"a":1},{"a":2}]\n')

    def test_rejects_non_standard_numbers(self):
        for source in ['NaN', 'Infinity', '-Infinity', '[NaN]', '1e999']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                format_json(source)

    def test_rejects_invalid_syntax(self):
        for source in ['', '{"a":1,}', '// comment\n{}', '{} {}']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                format_json(source)


class JsonFormatCliTests(unittest.TestCase):
    def run_cli(self, *args, source=""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], input=source,
            capture_output=True, text=True, check=False,
        )

    def test_stdin(self):
        for args in [[], ['-']]:
            with self.subTest(args=args):
                result = self.run_cli(*args, '--compact', '--sort-keys', source='{"b":2,"a":1}')
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '{"a":1,"b":2}\n', ''))

    def test_file_remains_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample with spaces.json"
            original = '{"message":"café"}'.encode('utf-8')
            path.write_bytes(original)
            result = self.run_cli(str(path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {"message": "café"})
            self.assertEqual(path.read_bytes(), original)

    def test_invalid_input_has_no_stdout(self):
        result = self.run_cli(source='{"a":1,"a":2}')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertIn('duplicate object key', result.stderr)

    def test_missing_file_and_bad_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            result = self.run_cli(str(path))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('Unable to read JSON', result.stderr)
            path.write_bytes(b'\xff')
            result = self.run_cli(str(path))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('Unable to read JSON', result.stderr)


if __name__ == "__main__":
    unittest.main()
