# Locate the first byte difference between two files

A checksum can tell you whether a copy matches an expected digest. When you have
both files and need to locate a discrepancy, compare their bytes directly:

```sh
python3 tools/compare_files.py original.bin copy.bin
```

The tool requires Python 3.8 or later, uses no external packages, and opens both
files read-only. It reads one-MiB chunks and stops at the first difference,
without loading the complete files into memory or relying on hash values.

For files containing `abc` and `axc`, the JSON output is:

```json
{
  "equal": false,
  "offset": 1,
  "left_byte": 98,
  "right_byte": 120
}
```

`offset` is zero-based: the first byte is at offset 0. Byte values are decimal
integers from 0 to 255. If one file ends before the other, its byte value is
`null` at the first extra byte's offset. Equal files return `equal: true` and
`null` for the other three fields. Two empty files compare equal.

| Exit code | Meaning |
| --- | --- |
| 0 | Contents are identical |
| 1 | Contents differ; JSON identifies the first difference |
| 2 | Input could not be read, or arguments were invalid |

Errors go to standard error. A difference is a normal comparison result, so its
report goes to standard output with no error message. Quote paths containing
spaces, and use `--` before filenames beginning with a dash.

The comparison is byte-for-byte: text encoding, line-ending style, and Unicode
normalization are not ignored. File metadata such as permissions is not compared.
Use regular files that are not being modified during the comparison; this tool
does not create a snapshot or lock writers. Symbolic links are followed. Special
files such as named pipes may block and are outside the intended use.
