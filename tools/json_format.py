"""Validate and format JSON from a UTF-8 file or standard input."""

import argparse
from contextlib import nullcontext
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


def format_records(stream, sort_keys=False):
    """Yield one compact JSON record per input line, with numbered errors."""
    for number, line in enumerate(stream, 1):
        try:
            yield format_json(line, sort_keys=sort_keys, compact=True)
        except (ValueError, RecursionError) as error:
            raise ValueError("line {}: {}".format(number, error)) from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="-", help="input path, or - for stdin (default)")
    parser.add_argument("--sort-keys", action="store_true", help="sort object keys recursively")
    parser.add_argument("--compact", action="store_true", help="omit optional whitespace")
    parser.add_argument("--check", action="store_true", help="validate without printing the document")
    parser.add_argument("--json-lines", action="store_true",
                        help="process one JSON value per line; output compact records")
    args = parser.parse_args(argv)
    try:
        context = nullcontext(sys.stdin) if args.file == "-" else Path(args.file).open(encoding="utf-8")
        with context as stream:
            outputs = (format_records(stream, sort_keys=args.sort_keys) if args.json_lines else
                       [format_json(stream.read(), sort_keys=args.sort_keys, compact=args.compact)])
            for output in outputs:
                if not args.check:
                    sys.stdout.write(output)
    except (OSError, UnicodeError) as error:
        print("Unable to read JSON or write output: {}".format(error), file=sys.stderr)
        return 2
    except (ValueError, RecursionError) as error:
        print("Invalid JSON: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
