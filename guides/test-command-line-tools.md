# Test a command-line tool's observable behavior

Function tests can miss argument parsing, exit codes, encoding, and accidental
output. Add a few subprocess tests that run the real entry point. Assert the
contract a caller depends on: return status, stdout, stderr, and file contents.

This complete example exercises this repository's checksum tool. Save it as a
temporary Python file outside the repository and run it with Python 3.8+ **from
the repository root**:

```python
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path("tools/file_checksum.py").resolve()


class ChecksumContractTests(unittest.TestCase):
    def run_tool(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, arguments)],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )

    def test_success_preserves_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "file with spaces.bin"
            path.write_bytes(b"abc")
            result = self.run_tool(path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout,
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad\n")
            self.assertEqual(result.stderr, "")
            self.assertEqual(path.read_bytes(), b"abc")

    def test_missing_file_is_a_read_error(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_tool(Path(directory) / "missing.bin")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertIn("Unable to read file", result.stderr)


if __name__ == "__main__":
    unittest.main()
```

`sys.executable` selects the interpreter running the tests. The absolute script
path keeps the command valid if a test changes the child's working directory.
Argument lists preserve filenames containing spaces without shell escaping.
Each test creates its own temporary directory, so it does not depend on existing
files or leave fixtures behind after success or an assertion failure.

The known `abc` digest is an independent expected result. Computing expected
values by calling the function under test would hide shared mistakes. For
structured JSON output, parse it and assert meaningful fields rather than
comparing indentation. Error text can vary by operating system: assert stable
prefixes instead of complete OS-generated messages.

The example deliberately omits `check=True` so tests can inspect expected
nonzero statuses. A timeout turns a hang into a test error, and subprocess
failures still provide captured diagnostics. Keep timeouts generous enough for
slower CI machines; do not test performance with fragile wall-clock thresholds.

Keep most edge cases in fast function tests, and use subprocess tests for the
public CLI contract. For binary input/output, omit `text=True` and use bytes.
If behavior depends on locale or environment variables, provide the relevant
environment explicitly so the test can reproduce that condition.
