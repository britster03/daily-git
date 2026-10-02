# Verify a gzip download without extracting a file

```sh
python3 tools/gzip_check.py download.gz
```

The Python 3.8+ tool decompresses in one-MiB chunks and discards the output,
checking compressed data and gzip trailers by reading to the end. It reports
JSON with `valid: true` and the total `uncompressed_bytes` on success. It never
writes an extracted file or changes the archive.

Exit status 0 means verification succeeded; 1 means invalid gzip (including
truncated data, a bad checksum, or missing signature); 2 means an input or
argument error. Failures produce diagnostics on stderr and no success report.
Concatenated gzip members are supported and their output sizes are added.
An empty gzip member is valid; a zero-byte input file is not a gzip archive.

Verification bounds output-buffer memory but must decompress the entire input,
so highly compressed files may require considerable CPU time. There is no time
or output-size limit. Use unchanged regular files. This checks gzip integrity,
not publisher authenticity or the validity of the uncompressed content. It
follows Python's gzip parser, including acceptance of trailing zero padding.
