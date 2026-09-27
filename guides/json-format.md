# Validate and format JSON

Use `tools/json_format.py` to check a JSON configuration or make an API response
easier to read. It requires Python 3.8 or later and no external packages.

From the repository root:

```sh
python3 tools/json_format.py config.json
printf '%s' '{"b":2,"a":1}' | python3 tools/json_format.py --sort-keys
python3 tools/json_format.py config.json --compact > compact.json
```

The input file is opened for reading only. Output goes to standard output, with
a trailing newline. Always redirect to a **different file**: shell redirection
would truncate the input before the tool could read it if you used the same path.
Omit the input path, or use `-`, to read standard input.

By default, output uses two-space indentation and retains the input order of
object keys. `--sort-keys` sorts keys recursively; `--compact` removes optional
whitespace. Unicode characters are escaped in output and retain their value
when the JSON is parsed.

## Validate without printing the document

Use `--check` in a script or CI step when you need an exit status without dumping
the formatted configuration into a log:

```sh
python3 tools/json_format.py config.json --check
printf '%s' '{"enabled":true}' | python3 tools/json_format.py --check
```

Valid input produces no output and exits with code 0. Invalid input still reports
the reason on standard error and exits with code 1; unreadable files exit with
code 2. The input file is never reformatted. This checks validity, not whether
the existing whitespace or key order matches a style. Formatting flags are
accepted with `--check`, but their output is suppressed. Validation follows the
same numeric and memory limits as formatting. Error messages can include key
names or file paths, so `--check` is not a general log-redaction mechanism.

## Validation behavior

The tool rejects malformed JSON, trailing commas, comments, multiple top-level
values, duplicate object keys (including nested objects), and the non-standard
numeric values `NaN`, `Infinity`, and `-Infinity`. For example:

```sh
printf '%s' '{"port":8000,"port":9000}' | python3 tools/json_format.py
```

This exits with code 1 and reports the duplicate `port` key on standard error.
No formatted JSON is emitted on validation failure. Keys may repeat in separate
objects; only repeated keys within the same object are rejected. Arrays and
scalar values such as `null` are valid top-level JSON.

| Exit code | Meaning |
| --- | --- |
| 0 | JSON validated (and formatted unless `--check` is used) |
| 1 | JSON is invalid or cannot be represented by the formatter |
| 2 | Input could not be read, or command arguments were invalid |

Files must use UTF-8 without a byte-order mark. The complete document is loaded
into memory. Decimal numbers use Python's floating-point representation, so the
tool is unsuitable for preserving exact decimal precision or the original
spelling of numbers. Values that overflow to infinity (for example `1e999`) are
rejected. This is a formatter and syntax check, not a JSON Schema validator.

Run its focused tests with:

```sh
python3 -m unittest discover -s tests -p 'test_json_format.py' -v
```
