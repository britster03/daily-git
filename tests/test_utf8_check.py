import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.utf8_check import check_stream


class Utf8CheckTests(unittest.TestCase):
    def run_stdin(self, data):
        script = Path(__file__).resolve().parents[1] / 'tools' / 'utf8_check.py'
        return subprocess.run([sys.executable, str(script), '-'], input=data,
                              capture_output=True, timeout=10,
                              env=dict(os.environ, PYTHONIOENCODING='ascii:surrogateescape'))

    def test_stdin_valid_empty_and_unicode(self):
        for data in [b'', ('café ' + chr(0x1F680)).encode('utf-8')]:
            with self.subTest(data=data):
                result = self.run_stdin(data)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), dict(valid=True, offset=None, reason=None))
                self.assertEqual(result.stderr, b'')

    def test_stdin_invalid_and_truncated_sequence(self):
        for data in [b'ab\xff', b'ab\xe2\x82']:
            with self.subTest(data=data):
                result = self.run_stdin(data)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(json.loads(result.stdout)['offset'], 2)

    def test_stdin_character_spanning_default_chunk_boundary(self):
        data = b'a' * (1024 * 1024 - 1) + '☃'.encode('utf-8')
        result = self.run_stdin(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_stdin(data + b'\xff')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['offset'], len(data))

    def test_literal_dash_file_does_not_read_stdin(self):
        script = Path(__file__).resolve().parents[1] / 'tools' / 'utf8_check.py'
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / '-').write_bytes(b'valid file')
            result = subprocess.run([sys.executable, str(script), './-'], cwd=directory,
                                    input=b'\xff', capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['valid'])

    def test_valid_sequences_across_boundaries(self):
        for data in [b'', b'ASCII\x00', ('café ☃ ' + chr(0x1F680)).encode(), b'\xef\xbb\xbfhello']:
            for size in range(1, 8):
                with self.subTest(data=data, size=size):
                    self.assertEqual(check_stream(io.BytesIO(data), size),
                                     dict(valid=True, offset=None, reason=None))

    def test_invalid_offsets_match_strict_decoder(self):
        for invalid in [b'\xff', b'\x80', b'\xc0\xaf', b'\xed\xa0\x80',
                        b'\xf4\x90\x80\x80', b'\xe2\x82', b'\xe2x']:
            for prefix in [b'', b'ab', b'a' * 15]:
                data = prefix + invalid
                try:
                    data.decode('utf-8')
                except UnicodeDecodeError as error:
                    expected = error.start
                else:
                    self.fail('Fixture must be invalid')
                for size in range(1, 8):
                    with self.subTest(data=data, size=size):
                        result = check_stream(io.BytesIO(data), size)
                        self.assertFalse(result['valid'])
                        self.assertEqual(result['offset'], expected)
                        self.assertTrue(result['reason'])

    def test_cli_status_and_preserved_file(self):
        script = Path(__file__).resolve().parents[1] / 'tools' / 'utf8_check.py'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.txt'
            for data, code in [(b'good', 0), (b'bad\xff', 1)]:
                path.write_bytes(data)
                result = subprocess.run([sys.executable, str(script), str(path)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(json.loads(result.stdout)['valid'], code == 0)
                self.assertEqual(path.read_bytes(), data)
            path.unlink()
            result = subprocess.run([sys.executable, str(script), str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
