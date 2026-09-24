# Compute and verify a file checksum

Use a SHA-256 checksum to detect whether two copies of a file have the same
contents, or to compare a download against a digest from a trusted publisher.
The tool reads in one-MiB chunks, so it can process large files without holding
the entire file in memory. Files are opened for reading only.

From the repository root, compute a digest:

```sh
python3 tools/file_checksum.py "path/to/download.zip"
```

The output is a single lowercase hexadecimal digest. To verify a known digest:

```sh
python3 tools/file_checksum.py "path/to/download.zip" --expect YOUR_64_CHARACTER_SHA256
```

Replace the placeholder with the actual digest. Uppercase hex is accepted too.

Exit codes are useful in shell scripts:

| Code | Meaning |
| --- | --- |
| 0 | Digest printed, or expected digest matched |
| 1 | Expected digest did not match |
| 2 | File could not be read, or arguments were invalid |

A digest verifies contents against your reference; it does not establish who
created a file. Obtain reference checksums from a trusted source, and avoid
hashing a file while another process is modifying it. Symbolic links are followed.

Run the tests:

```sh
python3 -m unittest discover -s tests -v
```
