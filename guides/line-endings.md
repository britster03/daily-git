# Inspect line endings without rewriting a file

Unexpected whole-file diffs can come from a change between LF and CRLF endings.
Inspect the bytes before changing editor settings or normalizing the file:

```sh
python3 tools/newline_report.py "path/to/file.txt"
```

Use `-` to inspect raw bytes from a pipe or redirected standard input:

```sh
printf 'first\r\nsecond\n' | python3 tools/newline_report.py -
python3 tools/newline_report.py - --expect lf --require-final-newline < source.py
```

Piped input preserves CR and LF bytes exactly and supports the same policy flags
and JSON report as files. Use `./-` for a file literally named `-`. In Bash or
Zsh, enable `set -o pipefail` when an upstream producer's failure must also fail
the pipeline; a valid report alone cannot establish that the producer succeeded.

The tool requires Python 3.8 or later. It prints a JSON report containing:

| Field | Meaning |
| --- | --- |
| `bytes` | Total bytes read |
| `lf` | LF endings that are not part of CRLF |
| `crlf` | CRLF pairs, each counted once |
| `cr` | CR endings that are not part of CRLF |
| `lines` | Endings plus a final unterminated line, if present |
| `ends_with_newline` | Whether the last byte is CR or LF; false for empty files |
| `mixed_endings` | Whether more than one ending style occurs |

For example, the bytes `a\r\nb\nlast` have one CRLF, one LF, three lines,
and no final newline. A file containing only one newline has one line, not two.
The count can differ from `wc -l`, which counts LF bytes rather than logical
lines under these rules.

The input is opened read-only and processed in one-MiB chunks; CRLF pairs split
across chunk boundaries are handled correctly. Exit code 0 means the report was
produced (even for mixed endings); code 2 means an input or argument error.

## Enforce a policy in a script or CI job

```sh
python3 tools/newline_report.py source.py --expect lf --require-final-newline
```

`--expect lf` rejects CRLF and standalone CR endings. Choose `crlf` or `cr`
instead when that is your project's required style. This checks every ending,
so a file with mixed styles fails. A file with no endings passes the style check;
use `--require-final-newline` to reject nonempty files without a final newline.
Empty files pass both checks.

The JSON report still goes to standard output. Policy failures add explanations
on standard error and exit with code 1; both violations are reported when both
checks fail. Code 0 means the requested checks passed, and code 2 still denotes
an input or argument error. The checks never rewrite the input. These policies
use the same raw-byte rules and encoding limitations as the report below.

This is a raw-byte inspection tool for UTF-8 and other ASCII-compatible text.
It does not detect encodings or decode UTF-16/UTF-32, and binary data may contain
bytes that resemble line endings. It reports what is on disk, which can differ
from Git's stored version when checkout conversion is enabled. It does not
modify the file or your Git settings.
