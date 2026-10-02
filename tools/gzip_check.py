"""Read a gzip file to completion to verify its compressed data and trailers."""

import argparse
import gzip
import json
import sys
import zlib


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    args = parser.parse_args(argv)
    try:
        with open(args.file, "rb") as raw:
            if raw.read(2) != b"\x1f\x8b":
                raise gzip.BadGzipFile("missing gzip signature")
            raw.seek(0)
            size = 0
            with gzip.GzipFile(fileobj=raw) as stream:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
    except (gzip.BadGzipFile, EOFError, zlib.error) as error:
        print("Invalid gzip: {}".format(error), file=sys.stderr)
        return 1
    except OSError as error:
        print("Unable to read gzip: {}".format(error), file=sys.stderr)
        return 2
    print(json.dumps({"valid": True, "uncompressed_bytes": size}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
