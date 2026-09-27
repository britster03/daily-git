# Inspect line endings without rewriting a file

Unexpected whole-file diffs can come from a change between LF and CRLF endings.
Inspect the bytes before changing editor settings or normalizing the file:

```sh
python3 tools/newline_report.py "path/to/file.txt"
```

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

This is a raw-byte inspection tool for UTF-8 and other ASCII-compatible text.
It does not detect encodings or decode UTF-16/UTF-32, and binary data may contain
bytes that resemble line endings. It reports what is on disk, which can differ
from Git's stored version when checkout conversion is enabled. It does not
modify the file or your Git settings.
