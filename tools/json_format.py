"""Validate and format JSON from a UTF-8 file or standard input."""

import argparse
import json
import sys
from pathlib import Path


def unique_object(pairs):
    """Reject duplicate keys instead of silently discarding earlier values."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate object key: {!r}".format(key))
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("non-standard numeric value: {}".format(value))


def format_json(source, sort_keys=False, compact=False):
    """Validate JSON and return its normalized representation with a newline."""
    value = json.loads(
        source, object_pairs_hook=unique_object, parse_constant=reject_constant
    )
    return json.dumps(
        value,
        indent=None if compact else 2,
        separators=(",", ":") if compact else None,
        sort_keys=sort_keys,
        allow_nan=False,
    ) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="-", help="input path, or - for stdin (default)")
    parser.add_argument("--sort-keys", action="store_true", help="sort object keys recursively")
    parser.add_argument("--compact", action="store_true", help="omit optional whitespace")
    args = parser.parse_args(argv)
    try:
        source = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print("Unable to read JSON: {}".format(error), file=sys.stderr)
        return 2
    try:
        output = format_json(source, sort_keys=args.sort_keys, compact=args.compact)
    except (ValueError, RecursionError) as error:
        print("Invalid JSON: {}".format(error), file=sys.stderr)
        return 1
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
