#!/usr/bin/env bash
# Usage: make-brief.sh ID  -> writes task-ID-brief.md = shared preamble + "## Task ID:" section
# IDs may carry a letter suffix (6b, 7b, 13a); the heading must be "## Task <ID>:" exactly,
# so Task 7 never swallows Task 7b.
set -euo pipefail
cd "$(dirname "$0")/.."
WS=planning
PLAN=docs/plan/l0-sprint-tasks.md
id=$1
out=$WS/task-$id-brief.md
section=$(awk -v id="$id" '
  /^```/ { infence = !infence }
  !infence && /^## / { intask = (index($0, "## Task " id ":") == 1) }
  intask { print }
' $PLAN)
[ -n "$section" ] || { echo "Task $id not found in $PLAN" >&2; exit 3; }
# The preamble: everything before the first task card ("Always read", the Global
# Constraints, Environment facts, Standing rulings). Controller state lives in
# planning/controller-state.md and is never copied; the guard stops at its old headings too.
{ awk '/^## (Task |Order, dependencies|Current position)/{exit} {print}' $PLAN; printf '%s\n' "$section"; } > $out
echo "$PWD/$out ($(wc -l < $out | tr -d ' ') lines)"
