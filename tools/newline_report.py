"""Report LF, CRLF, and CR line endings without changing a file."""

import argparse
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
    parser.add_argument("file", type=Path)
    args = parser.parse_args(argv)
    try:
        with args.file.open("rb") as stream:
            report = inspect_stream(stream)
    except OSError as error:
        print("Unable to read file: {}".format(error), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
