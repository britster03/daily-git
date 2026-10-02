"""Report LF, CRLF, and CR line endings without changing a file."""

import argparse
from contextlib import nullcontext
import json
import sys
from pathlib import Path


def inspect_stream(stream, chunk_size=1024 * 1024):
    """Inspect raw bytes with bounded memory, including split CRLF pairs."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    size = lf = cr = crlf = 0
    previous_cr = False
    final_byte = None
    for chunk in iter(lambda: stream.read(chunk_size), b""):
        size += len(chunk)
        lf += chunk.count(b"\n")
        cr += chunk.count(b"\r")
        crlf += chunk.count(b"\r\n")
        if previous_cr and chunk.startswith(b"\n"):
            crlf += 1
        previous_cr = chunk.endswith(b"\r")
        final_byte = chunk[-1]
    lf -= crlf
    cr -= crlf
    ends_with_newline = final_byte in (10, 13)
    return {
        "bytes": size,
        "lf": lf,
        "crlf": crlf,
        "cr": cr,
        "lines": lf + crlf + cr + int(size > 0 and not ends_with_newline),
        "ends_with_newline": ends_with_newline,
        "mixed_endings": sum(count > 0 for count in (lf, crlf, cr)) > 1,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="input file, or - for binary standard input")
    parser.add_argument("--expect", choices=("lf", "crlf", "cr"),
                        help="fail if any line ending uses another style")
    parser.add_argument("--require-final-newline", action="store_true",
                        help="fail when a nonempty file lacks a final newline")
    args = parser.parse_args(argv)
    try:
        context = nullcontext(sys.stdin.buffer) if args.file == "-" else Path(args.file).open("rb")
        with context as stream:
            report = inspect_stream(stream)
    except OSError as error:
        print("Unable to read file: {}".format(error), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    failed = False
    if args.expect and any(report[style] for style in ("lf", "crlf", "cr") if style != args.expect):
        print("Unexpected line ending: expected only {}".format(args.expect.upper()), file=sys.stderr)
        failed = True
    if args.require_final_newline and report["bytes"] and not report["ends_with_newline"]:
        print("Missing final newline", file=sys.stderr)
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
