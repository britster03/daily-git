import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.utf8_check import check_stream


class Utf8CheckTests(unittest.TestCase):
    def test_valid_sequences_across_boundaries(self):
        for data in [b'', b'ASCII\x00', 'café ☃ U0001f680'.encode(), b'\xef\xbb\xbfhello']:
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
