# Locate invalid UTF-8 in a file

Before processing a text export, validate its encoding without modifying it:

```sh
python3 tools/utf8_check.py export.txt
```

To validate output from another program without creating a temporary file, pass
`-` to read raw bytes from standard input:

```sh
printf '%s' 'plain text' | python3 tools/utf8_check.py -
python3 tools/utf8_check.py - < export.txt
```

Input is decoded strictly as UTF-8 regardless of the terminal's encoding or
`PYTHONIOENCODING`. The same JSON report, byte offsets, and exit codes apply to
files and pipes. An empty stream is valid. Use `./-` for a file literally named
`-`; omitting the input argument is an error rather than an implicit stdin read.

In Bash or Zsh, enable `set -o pipefail` when the producer's exit status matters.
A producer can fail after emitting valid UTF-8, and the validator cannot detect
that failure from its bytes. The validator stops at the first invalid sequence,
so a producer may receive a broken-pipe error when additional output is pending.

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
