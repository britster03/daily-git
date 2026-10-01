"""Validate a file as UTF-8 and report the first invalid sequence's byte offset."""

import argparse
import codecs
from contextlib import nullcontext
import json
import sys
from pathlib import Path


def check_stream(stream, chunk_size=1024 * 1024):
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    consumed = 0
    while True:
        chunk = stream.read(chunk_size)
        pending = len(decoder.getstate()[0])
        try:
            decoder.decode(chunk, final=not chunk)
        except UnicodeDecodeError as error:
            return {"valid": False, "offset": consumed - pending + error.start,
                    "reason": error.reason}
        consumed += len(chunk)
        if not chunk:
            return {"valid": True, "offset": None, "reason": None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="input file, or - for binary standard input")
    args = parser.parse_args(argv)
    try:
        context = nullcontext(sys.stdin.buffer) if args.file == "-" else Path(args.file).open("rb")
        with context as stream:
            report = check_stream(stream)
    except OSError as error:
        print("Unable to read file: {}".format(error), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
