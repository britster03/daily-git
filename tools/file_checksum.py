"""Compute or verify a file's SHA-256 digest using bounded memory."""

import argparse
import hashlib
import hmac
import re
import sys
from pathlib import Path


def sha256_file(path):
    """Return a hexadecimal SHA-256 digest, reading one MiB at a time."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--expect", help="expected 64-character SHA-256 hex digest")
    args = parser.parse_args(argv)
    if args.expect is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", args.expect):
        parser.error("--expect must contain exactly 64 hexadecimal characters")
    try:
        actual = sha256_file(args.file)
    except OSError as error:
        print("Unable to read file: {}".format(error), file=sys.stderr)
        return 2
    if args.expect is None:
        print(actual)
        return 0
    if hmac.compare_digest(actual, args.expect.lower()):
        print("OK: checksum matches")
        return 0
    print("MISMATCH: actual SHA-256 is {}".format(actual), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
