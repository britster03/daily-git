# Validate a JSON Lines export before using it

Different checks answer different questions. A matching checksum confirms bytes
against a trusted reference; valid UTF-8 confirms encoding; JSON validation checks
syntax and duplicate keys. None alone establishes that records meet your application's
schema or contain correct business data.

For an existing export, run these commands from the repository root:

```sh
python3 tools/utf8_check.py events.jsonl
python3 tools/newline_report.py events.jsonl --expect lf --require-final-newline
python3 tools/json_format.py events.jsonl --json-lines --check
```

The newline requirement is a project policy, not a JSON Lines syntax requirement.
The JSON tool accepts a final record without a trailing newline. If the publisher
provides a checksum, verify it with `file_checksum.py --expect` too. For gzip
exports, `gzip_check.py` verifies compression integrity before you examine the
decompressed contents. Each extra pass reads the file again; choose checks that
answer an actual question in your workflow.

## Try a complete workflow in a temporary directory

Paste this into a POSIX shell from the repository root. It creates a tiny export,
checks it, normalizes key order, and verifies the normalized bytes against an
independently written expected file:

```sh
(
set -eu
export_demo=$(mktemp -d)
trap 'rm -rf -- "$export_demo"' EXIT
printf '%s\n' '{"z":2,"a":1}' '{"a":3}' > "$export_demo/events.jsonl"
python3 tools/utf8_check.py "$export_demo/events.jsonl"
python3 tools/newline_report.py "$export_demo/events.jsonl" --expect lf --require-final-newline
python3 tools/json_format.py "$export_demo/events.jsonl" --json-lines --check
python3 tools/json_format.py "$export_demo/events.jsonl" --json-lines --sort-keys > "$export_demo/normalized.jsonl"
printf '%s\n' '{"a":1,"z":2}' '{"a":3}' > "$export_demo/expected.jsonl"
python3 tools/compare_files.py "$export_demo/expected.jsonl" "$export_demo/normalized.jsonl" --quiet
printf 'Verified: normalized output matches expected records.\n'
)
```

Every tool reads its input without rewriting it. The formatter's output goes to
a separate temporary path: redirecting to the source path would truncate it
before Python starts. A failing command stops this example and removes its
temporary directory. In a production job, keep failed inputs and diagnostics
where appropriate for investigation.

JSON Lines formatting may emit earlier valid records before a later record fails.
Check the formatter's exit status before publishing its output, even if an earlier
validation pass succeeded: the source may have changed in between. For a stable
handoff, use an immutable input and publish a completed temporary output via the
[atomic replacement pattern](atomic-file-updates.md). The formatter uses binary
floating-point numbers, so it is unsuitable for preserving exact decimal precision.
