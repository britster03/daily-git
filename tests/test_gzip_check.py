import gzip
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class GzipCheckTests(unittest.TestCase):
    def test_integrity_and_exit_status(self):
        script = Path(__file__).resolve().parents[1] / 'tools/gzip_check.py'
        payload = b'abc' * 500000
        valid = gzip.compress(payload)
        damaged = bytearray(valid)
        damaged[-8] ^= 1
        cases = [(valid, 0, len(payload)), (gzip.compress(b''), 0, 0),
                 (gzip.compress(b'a') + gzip.compress(b'bc'), 0, 3),
                 (bytes(damaged), 1, None), (valid[:-4], 1, None),
                 (b'', 1, None), (b'not gzip', 1, None),
                 (valid + b'garbage', 1, None)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.gz'
            for data, code, size in cases:
                with self.subTest(code=code, size=size, length=len(data)):
                    path.write_bytes(data)
                    result = subprocess.run([sys.executable, str(script), str(path)],
                                            capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, code, result.stderr)
                    self.assertEqual(path.read_bytes(), data)
                    if code == 0:
                        self.assertEqual(json.loads(result.stdout)['uncompressed_bytes'], size)
                    else:
                        self.assertEqual(result.stdout, '')
                        self.assertIn('Invalid gzip', result.stderr)
            path.unlink()
            result = subprocess.run([sys.executable, str(script), str(path)], capture_output=True)
            self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
