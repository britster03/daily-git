"""Compare files byte-for-byte and report the first differing offset."""

import argparse
import json
import sys
from pathlib import Path


def compare_files(left_path, right_path, chunk_size=1024 * 1024):
    """Compare binary files with bounded memory, stopping at the first difference."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    offset = 0
    with Path(left_path).open("rb") as left, Path(right_path).open("rb") as right:
        while True:
            a, b = left.read(chunk_size), right.read(chunk_size)
            if a != b:
                shared = min(len(a), len(b))
                index = next((i for i in range(shared) if a[i] != b[i]), shared)
                return {"equal": False, "offset": offset + index,
                        "left_byte": a[index] if index < len(a) else None,
                        "right_byte": b[index] if index < len(b) else None}
            if not a:
                return {"equal": True, "offset": None, "left_byte": None, "right_byte": None}
            offset += len(a)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--quiet", action="store_true", help="suppress the comparison report; retain read errors")
    args = parser.parse_args(argv)
    try:
        result = compare_files(args.left, args.right)
    except OSError as error:
        print("Unable to compare files: {}".format(error), file=sys.stderr)
        return 2
    if not args.quiet:
        print(json.dumps(result, indent=2))
    return 0 if result["equal"] else 1


if __name__ == "__main__":
    sys.exit(main())
