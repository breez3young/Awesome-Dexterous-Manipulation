#!/usr/bin/env bash
# Publish generated discovery data only. Codex owns the single review PR.
set -euo pipefail

BOT_BRANCH="${BOT_BRANCH:-bot/dexterous-watch}"
DATA_DIR="${DATA_DIR:-.}"
: "${PREVIOUS_BOT_SHA?Set the inspected candidate SHA (empty if the branch is new)}"

if [ "$BOT_BRANCH" != 'bot/dexterous-watch' ]; then
  printf 'Refusing to write outside the dedicated candidate branch.\n' >&2
  exit 1
fi

files=("$DATA_DIR/candidates.json" "$DATA_DIR/watch.json")
git add -- "${files[@]}"
if git diff --cached --quiet HEAD -- "${files[@]}"; then
  printf 'No discovery changes to save.\n'
  exit 0
fi
if [ -n "$PREVIOUS_BOT_SHA" ] && git diff --cached --quiet "$PREVIOUS_BOT_SHA" -- "${files[@]}"; then
  printf 'The candidate branch already contains this report.\n'
  exit 0
fi

git checkout -b "$BOT_BRANCH"
# Limit the commit to generated data even if something else was staged.
git -c user.name='github-actions[bot]' \
    -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
    commit --only -m 'chore: update dexterous paper discovery queue' -- "${files[@]}"
# Rebuild from the checked-out default branch, keeping queued discoveries from
# the previous scan. Reject the push if the remote changed since inspection.
git push "--force-with-lease=refs/heads/$BOT_BRANCH:$PREVIOUS_BOT_SHA" origin "HEAD:refs/heads/$BOT_BRANCH"
printf 'Candidates saved for Codex. No discovery pull request is created.\n'
