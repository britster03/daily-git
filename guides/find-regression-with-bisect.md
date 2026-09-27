# Find the commit that introduced a regression

When the current version fails but an older version works, `git bisect` narrows
the interval by checking commits between those two points. A reliable test lets
Git perform the search automatically.

## Use it on a project

Start with a clean working tree (`git status --short`) and identify a known-good
commit. Replace `GOOD_COMMIT` below with that commit's hash or tag:

```sh
git bisect start
git bisect bad HEAD
git bisect good GOOD_COMMIT
git bisect run python3 /absolute/path/to/regression_check.py
git bisect log
git bisect reset
```

Keep the regression check outside the checkout so it remains available when Git
switches to old commits. Run it manually against both endpoints first: it must
pass on the good version and fail on the bad version for the intended reason.
Use a small deterministic check that exercises the bug, and install the
dependencies needed by the versions being tested.

For `git bisect run`, exit code 0 means good, 1–127 means bad except for 125,
and 125 means the commit cannot be tested and should be skipped. Codes 128 or
higher abort the search. Be careful with shell failures: a missing command can
exit with 127 and incorrectly label a commit as bad. Check prerequisites first.

Without an automated check, omit `git bisect run`, inspect each selected commit,
then use `git bisect good`, `git bisect bad`, or `git bisect skip`. Repeat until
Git reports the first bad commit. Skipping commits may leave several candidates
instead of one definitive answer.

Save the first bad hash and, if useful, the output of `git bisect log` before
resetting. `git bisect reset` ends the session and returns to your original
checkout; it does not undo the regression. Inspect the reported diff and make
the fix on your normal development branch. An intermittent failure or a bug
that disappears and returns can make the search misleading.

## Try a complete example

Paste this block into a POSIX shell with Git and Python 3 installed. It runs in
a subshell, creates a new temporary repository, and leaves your current repository
untouched. The temporary path is printed so you can inspect it afterward.

```sh
(
set -eu
bisect_demo=$(mktemp -d)
printf 'Example repository: %s\n' "$bisect_demo"
cd "$bisect_demo"
git init -q
git config user.name 'Bisect Example'
git config user.email 'bisect@example.invalid'
git config commit.gpgsign false

printf 'def add(a, b):\n    return a + b\n' > calc.py
git add calc.py
git commit -qm 'Implement addition'
good_commit=$(git rev-parse HEAD)

printf 'A tiny calculator example.\n' > README.md
git add README.md
git commit -qm 'Document calculator'

printf 'def add(a, b):\n    return a - b\n' > calc.py
git add calc.py
git commit -qm 'Introduce arithmetic regression'
expected_bad=$(git rev-parse HEAD)

printf '\nSupports two operands.\n' >> README.md
git add README.md
git commit -qm 'Expand calculator documentation'
starting_commit=$(git rev-parse HEAD)

git bisect start HEAD "$good_commit"
git bisect run python3 -B -c 'from calc import add; assert add(2, 3) == 5'
test "$(git rev-parse refs/bisect/bad)" = "$expected_bad"
git bisect log
git bisect reset
test "$(git rev-parse HEAD)" = "$starting_commit"
printf 'Verified: found the regression and restored the original checkout.\n'
)
```

The expected first bad commit is **Introduce arithmetic regression**, even
though a later documentation commit is at the tip. Assertion failures during
the search are expected: they are how the test marks a version as bad. The
example checks `refs/bisect/bad` because `HEAD` can remain on the last tested
commit, which may be good. Python's
`-B` flag prevents bytecode cache files from being written in this fresh example.
