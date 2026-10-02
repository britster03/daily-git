# Daily Git

A growing collection of small developer tools and practical programming guides.
Each addition should solve a concrete problem, include a working example, and be
easy to use without extra dependencies.

## Guides

- [Test command-line tool behavior](guides/test-command-line-tools.md)
- [Stop tracking an ignored generated file](guides/git-ignore-tracked-files.md)
- [Review exactly what you are about to commit](guides/review-before-commit.md)
- [Find a regression with Git bisect](guides/find-regression-with-bisect.md)
- [Run subprocesses safely from Python](guides/python-subprocess.md)
- [Replace generated files atomically](guides/atomic-file-updates.md)

## Tools

- [Gzip integrity checker](guides/gzip-check.md): verify compressed data without
  writing extracted files. Requires Python 3.8 or later.
- [UTF-8 validator](guides/utf8-check.md): locate invalid bytes in files or pipes with
  bounded memory. Requires Python 3.8 or later.
- [File comparison](guides/compare-files.md): locate the first differing byte
  in two files using bounded memory. Requires Python 3.8 or later.
- [Line-ending inspector](guides/line-endings.md): report LF, CRLF, mixed endings,
  and missing final newlines without rewriting files. Requires Python 3.8 or later.
- [File checksum](guides/file-checksum.md): compute or verify SHA-256, SHA-512, or BLAKE2b digests
  without loading the entire file into memory. Requires Python 3.8 or later.
- [JSON formatter](guides/json-format.md): validate and format JSON or stream
  JSON Lines records, with duplicate-key detection. Requires Python 3.8 or later.

## Contributing

Keep each commit focused on one useful improvement. Include usage instructions
for tools and meaningful tests for their behavior. Prefer Python's standard
library for small command-line utilities. Avoid empty commits, repeated content,
and date-only changes.

Run the Python tests from the repository root:

```sh
python3 -m unittest discover -s tests -v
```
