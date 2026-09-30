# Diagnose why Git still tracks an ignored file

`.gitignore` affects untracked paths. Adding a pattern does not remove a file
that is already in Git's index. Diagnose a specific path before changing it:

```sh
git ls-files -- path/to/generated.log
git check-ignore -v --no-index -- path/to/generated.log
```

The first command prints the path if it is tracked. The second shows matching
ignore rules even for tracked files; without `--no-index`, tracked files are
normally omitted. `check-ignore` exits with code 1 when nothing is ignored,
which is a normal result rather than a command failure.

To stop tracking a generated file while retaining your local copy, add the
appropriate ignore rule, then run:

```sh
git rm --cached -- path/to/generated.log
git add .gitignore
git diff --cached
```

Review and commit the staged deletion and ignore rule together. Do not add `-f`
if Git refuses: inspect staged and working changes first. This removes the file
from future snapshots, not old commits. Other checkouts updating to that commit
may have their previously tracked copy removed, so coordinate if they need it.
Ignoring a committed credential does not remove it from history or revoke it.

## Verify the behavior in a temporary repository

Run this POSIX-shell example anywhere. It leaves your current checkout alone
and prints the temporary repository's path for inspection:

```sh
(
set -eu
ignore_demo=$(mktemp -d)
printf 'Example repository: %s\n' "$ignore_demo"
cd "$ignore_demo"
git init -q
git config user.name 'Ignore Example'
git config user.email 'ignore@example.invalid'
git config commit.gpgsign false
printf 'generated output\n' > generated.log
git add generated.log
git commit -qm 'Track example output'
printf '/generated.log\n' > .gitignore
test "$(git ls-files -- generated.log)" = generated.log
git check-ignore -v --no-index -- generated.log
git rm --cached -- generated.log
test -f generated.log
test -z "$(git ls-files -- generated.log)"
git check-ignore -q -- generated.log
git add .gitignore
git commit -qm 'Ignore generated output'
test -z "$(git status --porcelain)"
printf 'Verified: file remains locally and is no longer tracked.\n'
)
```

The leading slash in `/generated.log` anchors the rule to the directory
containing this `.gitignore`. A rule like `*.log` is broader; prefer a specific
path when only one generated artifact should be ignored.
