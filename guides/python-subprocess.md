# Run command-line tools from Python without shell quoting bugs

Pass the executable and each argument as separate list elements to
`subprocess.run`. Spaces, semicolons, and dollar signs inside an argument remain
data when `shell=False` (the default). Do not build a command by concatenating
user input into a shell string, and do not add shell quotes inside list elements.

This complete Python 3.8+ example sends strings to a child Python process and
checks that they arrive unchanged:

```python
import json
import subprocess
import sys


def echo_arguments(values):
    result = subprocess.run(
        [sys.executable, "-c",
         "import json, sys; print(json.dumps(sys.argv[1:]))", *values],
        shell=False,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=5,
    )
    return json.loads(result.stdout)


values = ["report with spaces.txt", "semi;colon", "$(echo unexpected)", "café"]
assert echo_arguments(values) == values
print("All arguments arrived unchanged.")
```

The `-c` program is a fixed, trusted string; values go in subsequent arguments,
never interpolated into Python source. `sys.executable` uses the same interpreter
as the parent. When calling other tools, choose a trusted executable path or
ensure `PATH` resolves to the program you intend to run.

## Handle the three main failure cases

- `subprocess.CalledProcessError`: `check=True` saw a nonzero exit status. Inspect
  `returncode` and captured `stderr` to diagnose the tool's failure.
- `subprocess.TimeoutExpired`: the time limit elapsed. `run` kills and waits for
  the direct child before raising; it does not promise to kill descendants.
- `OSError` (including `FileNotFoundError`): the process could not be started,
  for example because the executable was missing or not executable.

Let these exceptions reach a caller that can decide whether to retry, report a
failure, or stop. Avoid catching every exception and returning an empty string:
that makes failure indistinguishable from valid empty output. Do not indiscriminately
log command arguments or captured output when they can contain credentials.

## A list prevents shell parsing, not tool-specific options

A filename beginning with `-` can still be interpreted as an option by the child
program. Use its documented end-of-options marker where supported. For example,
`["git", "diff", "--", path]` treats `path` as a pathspec rather than a Git option.
Other programs have different argument rules; list arguments do not override them.

For a working directory, use `cwd=directory` instead of prepending `cd ... &&`.
To provide standard input, use `input=payload`. Shell constructs such as `>`,
`|`, `*`, and `~` do not expand in an argument list: open output files explicitly
or connect processes deliberately when you need those behaviors.

`capture_output=True` holds output in memory. For large or unbounded output,
direct stdout/stderr to file objects or consume streams incrementally instead.
