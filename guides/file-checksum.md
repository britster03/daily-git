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

## Hash piped input

Pass `-` to hash standard input as raw bytes, without decoding text or changing
line endings. This also works with `--expect`:

```sh
printf '%s' 'abc' | python3 tools/file_checksum.py -
python3 tools/file_checksum.py - --expect ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad < sample.bin
```

The first command prints the digest used in the second example; verification
succeeds when `sample.bin` contains exactly the three bytes `abc`. Input is still
read in bounded chunks, including when it comes from a pipe. An empty stream has
the SHA-256 digest of an empty file. Use `./-` to hash a file literally named `-`.
In Bash or Zsh, enable `set -o pipefail` when you also need to detect a failed
upstream command: the checksum tool cannot tell whether a producer exited early.

## Exit codes

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
