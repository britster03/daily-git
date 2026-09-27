# Replace a generated text file without exposing partial output

Opening an existing file with mode `w` truncates it immediately. If generation
fails halfway through, readers can see incomplete output and the old contents
are already gone. For a generated report or configuration snapshot, write a
temporary file beside the destination, then replace the destination only after
the complete output has been written successfully.

This Python 3.8+ function implements that pattern for UTF-8 text in a trusted
directory on a filesystem supporting atomic replacement:

```python
import os
import tempfile
from pathlib import Path


def atomic_write_text(destination, text):
    destination = Path(destination).absolute()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=destination.parent, prefix=".atomic-", suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
```

Call it after generating and validating the full content, for example:

```python
atomic_write_text("report.txt", "Completed: 12 jobs\nFailed: 0 jobs\n")
```

The destination directory must already exist. The temporary file is closed
before replacement, which also avoids trying to rename an open temporary file
on platforms that disallow it. Keeping it in the same directory avoids a
cross-filesystem move. If writing, encoding, flushing, or replacement fails,
the error reaches the caller and cleanup attempts to remove the temporary file.
The old destination remains intact when failure occurs before replacement.

## What this guarantees and what it does not

Where replacement is atomic, a new reader opening the destination sees the old
complete file or the new complete file, rather than a half-written version.
Readers that already hold the old file open may continue reading its old content.

This pattern is not a lock: two writers can each produce complete output, with
the last successful replacement winning. It does not make a read-modify-write
operation safe against lost updates. Use coordination or a transactional store
when writers need to merge changes.

`fsync` requests that the temporary file's data reach storage, but this example
does not sync the parent directory after replacement. Atomic visibility is not
a promise that the new directory entry survives power loss. Filesystem and
platform behavior matter, especially on network storage.

The replacement is a new file. It does not preserve the previous file's owner,
permissions, ACLs, or extended attributes; on POSIX systems the temporary file
normally starts with mode 0600. A destination symlink is replaced rather than
followed. Use this example for generated files whose metadata you control, not
as a universal configuration editor. A forced process termination can also
leave the temporary file behind because `finally` cannot always run.
