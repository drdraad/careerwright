# Task W2B fix round 1 of 5

You fix Task W2, slice W2B (Careerwright L0, branch `l0-local-release`). W2B was built in
f70f88d (BASE c84729e) and reviewed. You are a fresh implementer: the original report tells you
what was built and why.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`
2. `task-W2B-review.md` in full (finding IDs below are its own)
3. `task-W2B-dispatch.md` (the controller's decisions that still bind) and `task-W2B-report.md`
4. `task-W2-brief.md` and `task-W2-slices.md` as needed; CLAUDE.md invariants; plan section 4
   ("The first ten seconds", "Revelations are earned") and SW.5; ADR 0007 (as amended), 0014.

## Controller rulings
- **I1 and I2, one change:** every search that is not the person's own title (task,
  transferable and work-style) runs on an essential-skills-only vector: a suggestion is
  reached only through an essential skill whose label holds the person's words, and its
  why-line names that skill. No hidden labels, ISCO group labels or descriptions in that
  vector. Build it at import, backfill it for the held release in a forward migration, and
  match a model query to the person's own titles with `concept_key`. Add the review's DSC case
  (a proposer query that is a plural of the role) and an evaluation check that a task-channel
  suggestion's matched words sit in one of its essential skills. Record P01's and P02's slates
  before and after in the report: whether work-style words should retrieve at all goes on
  session W2's sheet (W2D), not decided here. Amend ADR 0007 decision 13 to match.
- **I3:** the strength run reads only the answers the turn's decision added; `no_quotable_answer`
  when none is quotable; a test that a decline is not re-proposed on a later turn. Nothing new
  stored. (Resolves M9.)
- **I4:** the demo's strength is scripted: a small fixed table (answer phrase → ESCO skill URI)
  for the demo journey's known answers, still passed through `check_strength`, labelled; none
  otherwise. No word-overlap heuristic.
- **I5:** when every-word matching finds no title, the type-ahead returns the occupations whose
  labels match the most typed words, flagged `partial: true`, so the interface can ask "ESCO
  doesn't list that title. Is it one of these?". The person chooses; nothing is joined by
  words. Test on P01, P04 and P05's own titles. Regenerate the client.
- **M5:** keep the label the person picked (an alternative label stays theirs) while resolving
  by its URI.
- **Carried, not fixed here:** M6's session W2 sheet (W2D; but state now in ADR 0007 why the
  minimum is 3), M7 (W2C), M8 (final review).

## Fix now
I1–I5 as ruled; M1 (time the occupation with the most essential skills and single letters
"a", "s", "c"; record the numbers); M2 (no connection unless the role names exactly one
occupation); M3 (a complete run with no readable output is `INTERNAL_ERROR`, not "none
found"); M4 (the listed tests); M5 as ruled.

## Then
- `make check`; then `make acceptance` once before the final commit. The controller may still
  have its own `make acceptance` running when you start: before yours, check with
  `pgrep -fl "make acceptance"` and wait until none is running. If the crash-recovery test in
  `test_durable_runs.py` hangs on worker shutdown again, re-run `make acceptance` once and
  report both runs exactly; do not change that test.
- Hard rules: Edit/Write only for source changes (no scripts that rewrite files, not even for
  string replacements; the project's own generators are fine); stage explicit paths; never
  `answers-2.md`; never `.env`, `~/.nessa`, `~/.careerwright`; no live model call, no web
  request; no headed browser or window on the product owner's screen; leave `spikes/world`
  unchanged; no subagents; never push. DBOS `application_version` stays `careerwright-l0-1`.
- Append a "Fix round 1" section to `task-W2B-report.md` (each finding: what changed, the test
  that proves it, the before/after slates). Reply with only the short contract.
