#!/usr/bin/env bash
# Usage: review-pkg.sh BASE HEAD  -> writes review-<b>..<h>.diff excluding lockfiles/generated/data
set -euo pipefail
cd "$(dirname "$0")/.."
WS=planning
b=$(git rev-parse --short "$1"); h=$(git rev-parse --short "$2")
out="$PWD/$WS/review-$b..$h.diff"
EX=(':(exclude)**/uv.lock' ':(exclude)uv.lock' ':(exclude)**/pnpm-lock.yaml' ':(exclude)pnpm-lock.yaml'
    ':(exclude)**/generated/**' ':(exclude)**/*.woff2' ':(exclude)**/*.woff' ':(exclude)**/*.ttf'
    ':(exclude)**/*.png' ':(exclude)**/*.jpg' ':(exclude)**/*.zip' ':(exclude)*.docx')
{
  echo "# Review package: $b..$h"; echo
  echo "## Commits"; git log --oneline "$1..$2"; echo
  echo "## Files changed (all, incl. excluded)"; git diff --stat=160 "$1..$2"; echo
  echo "## Excluded from diff below: lockfiles, **/generated/**, fonts, images, zips"; echo
  echo "## Diff"; git diff -U8 "$1..$2" -- . "${EX[@]}"
} > "$out"
echo "$out ($(wc -l < "$out" | tr -d ' ') lines)"
