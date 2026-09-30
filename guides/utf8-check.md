# Locate invalid UTF-8 in a file

Before processing a text export, validate its encoding without modifying it:

```sh
python3 tools/utf8_check.py export.txt
```

This Python 3.8+ tool reads one-MiB chunks with an incremental strict decoder.
Multi-byte characters split across chunks are handled correctly. Memory usage
does not grow with the file size. Processing stops at the first invalid sequence.

Valid input produces `{"valid": true, "offset": null, "reason": null}`.
Invalid input produces `valid: false`, a zero-based byte offset, and the decoder's
reason. The offset points to the start of the invalid sequence, which can be
before the byte that revealed the error. An incomplete sequence at end-of-file
is also invalid. The report is formatted as JSON on standard output.

| Exit code | Meaning |
| --- | --- |
| 0 | Valid UTF-8, including an empty file |
| 1 | Invalid UTF-8; inspect the report |
| 2 | Input or argument error |

Overlong encodings, encoded surrogate code points, and code points above
U+10FFFF are rejected. A UTF-8 byte-order mark is accepted as U+FEFF; an
application such as the JSON formatter may impose stricter rules. NUL bytes and
control characters can be valid UTF-8, so success does not prove that the file
is readable prose, valid JSON, or safe input for another program. This tool does
not guess alternate encodings, normalize Unicode, or repair corrupt data.

Use an unchanged regular file while checking. Files are opened read-only and
symbolic links are followed. To investigate line-ending issues separately, use
the [line-ending inspector](line-endings.md).
