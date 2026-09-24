# Daily Git

A growing collection of small developer tools and practical programming guides.
Each addition should solve a concrete problem, include a working example, and be
easy to use without extra dependencies.

## Guides

- [Review exactly what you are about to commit](guides/review-before-commit.md)

## Contributing

Keep each commit focused on one useful improvement. Include usage instructions
for tools and meaningful tests for their behavior. Prefer Python's standard
library for small command-line utilities. Avoid empty commits, repeated content,
and date-only changes.

Run the Python tests from the repository root:

```sh
python3 -m unittest discover -s tests -v
```
