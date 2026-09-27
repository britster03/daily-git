# Daily Git

A growing collection of small developer tools and practical programming guides.
Each addition should solve a concrete problem, include a working example, and be
easy to use without extra dependencies.

## Guides

- [Review exactly what you are about to commit](guides/review-before-commit.md)
- [Find a regression with Git bisect](guides/find-regression-with-bisect.md)

## Tools

- [Line-ending inspector](guides/line-endings.md): report LF, CRLF, mixed endings,
  and missing final newlines without rewriting files. Requires Python 3.8 or later.
- [File checksum](guides/file-checksum.md): compute or verify a SHA-256 digest
  without loading the entire file into memory. Requires Python 3.8 or later.
- [JSON formatter](guides/json-format.md): validate and format JSON from a file
  or standard input, with duplicate-key detection. Requires Python 3.8 or later.

## Contributing

Keep each commit focused on one useful improvement. Include usage instructions
for tools and meaningful tests for their behavior. Prefer Python's standard
library for small command-line utilities. Avoid empty commits, repeated content,
and date-only changes.

Run the Python tests from the repository root:

```sh
python3 -m unittest discover -s tests -v
```
