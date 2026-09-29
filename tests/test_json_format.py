import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.json_format import format_json, format_records


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "json_format.py"


class JsonFormatTests(unittest.TestCase):
    def test_records_are_processed_lazily(self):
        records = format_records(iter(['{"a":1}\n', 'broken\n']))
        self.assertEqual(next(records), '{"a":1}\n')
        with self.assertRaisesRegex(ValueError, 'line 2:'):
            next(records)

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

    def test_json_lines_normalizes_records(self):
        result = self.run_cli('--json-lines', '--sort-keys',
                              source=' {"z":2, "a":1}\r\n[1, 2]\nnull')
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, '{"a":1,"z":2}\n[1,2]\nnull\n', ''))

    def test_json_lines_errors_include_record_number(self):
        for bad in ['\n', '  \n', '{"x":1,"x":2}\n', 'NaN\n', '1e999\n', '{} {}\n']:
            with self.subTest(bad=bad):
                result = self.run_cli('--json-lines', source='{}\n' + bad + 'true\n')
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, '{}\n')
                self.assertIn('line 2:', result.stderr)

    def test_json_lines_check_and_empty_stream(self):
        for source in ['', '{}\ntrue\n']:
            with self.subTest(source=source):
                result = self.run_cli('--json-lines', '--check', source=source)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        result = self.run_cli('--json-lines', '--check', source='{}\nbroken\n')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertIn('line 2:', result.stderr)

    def test_json_lines_file_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'records.jsonl'
            original = b'{ "a":1 }\n[true]\n'
            path.write_bytes(original)
            result = self.run_cli(str(path), '--json-lines')
            self.assertEqual((result.returncode, result.stdout), (0, '{"a":1}\n[true]\n'))
            self.assertEqual(path.read_bytes(), original)

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

    def test_check_is_silent_for_valid_stdin(self):
        for flags in [['--check'], ['--check', '--compact', '--sort-keys']]:
            with self.subTest(flags=flags):
                result = self.run_cli(*flags, source='{"token":"keep out of logs"}')
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def test_check_keeps_validation_rules(self):
        for source in ['{"a":1,"a":2}', 'NaN', '1e999', '{broken', '']:
            with self.subTest(source=source):
                result = self.run_cli('--check', source=source)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, '')
                self.assertIn('Invalid JSON', result.stderr)

    def test_check_file_is_not_reformatted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            original = b'{  "b":2, "a":1  }'
            path.write_bytes(original)
            result = self.run_cli(str(path), '--check')
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
            self.assertEqual(path.read_bytes(), original)

    def test_check_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli(str(Path(directory) / 'missing.json'), '--check')
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('Unable to read JSON', result.stderr)

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
