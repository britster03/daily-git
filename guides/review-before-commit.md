# Review exactly what you are about to commit

Git keeps the working directory separate from the staging area. A commit records
the staged version of each file, which can differ from the version in your editor.

## Inspect the changes

```sh
git status --short
git diff
git diff --cached
```

`git diff` shows tracked edits that are not staged. `git diff --cached` shows what
the next commit will contain. Newly created, untracked files appear in status but
do not appear in either diff until you stage them.

## Stage one coherent change

```sh
git add -p
git add path/to/new-file.py
git diff --cached --stat
git diff --cached --check
git diff --cached
```

Interactive staging lets you select individual hunks of tracked files. Stage new
files explicitly. The whitespace check catches issues such as trailing spaces;
it does not replace tests or reviewing the content for credentials.

If you edit a file again after staging it, stage the new edits too if they belong
in this commit. Otherwise they remain in your working directory for later.

## Remove a file from the staging area

For a repository that already has a commit:

```sh
git restore --staged path/to/file.py
```

This leaves the working file intact. Before a repository's very first commit,
use `git rm --cached -- path/to/file.py` to unstage a newly added file instead.

Run the relevant tests, review the staged diff once more, and commit with a
message that describes the change:

```sh
git commit -m "Fix parsing of empty input"
git status --short
```

A clean final status means there are no outstanding tracked edits or untracked
files. Ignored files are not shown by default.
