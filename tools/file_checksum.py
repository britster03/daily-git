"""Compute or verify a file or standard input's checksum."""

import argparse
import hashlib
import hmac
import re
import sys
from pathlib import Path


def checksum_stream(stream, algorithm="sha256"):
    """Hash a binary stream in one-MiB chunks without closing it."""
    digest = hashlib.new(algorithm)
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def sha256_stream(stream):
    """Preserve the SHA-256 stream helper for existing callers."""
    return checksum_stream(stream)


def checksum_file(path, algorithm="sha256"):
    with Path(path).open("rb") as stream:
        return checksum_stream(stream, algorithm)


def sha256_file(path):
    """Return a hexadecimal SHA-256 digest, reading one MiB at a time."""
    return checksum_file(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="input file, or - to read binary standard input")
    parser.add_argument("--algorithm", choices=("sha256", "sha512", "blake2b"),
                        default="sha256", help="hash algorithm (default: sha256)")
    parser.add_argument("--expect", help="expected hexadecimal digest for the selected algorithm")
    args = parser.parse_args(argv)
    expected_length = hashlib.new(args.algorithm).digest_size * 2
    if args.expect is not None and not re.fullmatch(r"[0-9a-fA-F]{%d}" % expected_length, args.expect):
        parser.error("--expect must contain exactly {} hexadecimal characters".format(expected_length))
    try:
        actual = (checksum_stream(sys.stdin.buffer, args.algorithm) if args.file == "-"
                  else checksum_file(args.file, args.algorithm))
    except OSError as error:
        print("Unable to read file: {}".format(error), file=sys.stderr)
        return 2
    if args.expect is None:
        print(actual)
        return 0
    if hmac.compare_digest(actual, args.expect.lower()):
        print("OK: checksum matches")
        return 0
    label = {"sha256": "SHA-256", "sha512": "SHA-512", "blake2b": "BLAKE2b"}[args.algorithm]
    print("MISMATCH: actual {} is {}".format(label, actual), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
