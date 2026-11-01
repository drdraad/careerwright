# Task W2B fix round 5 of 5 (the last)

You fix what remains of Task W2, slice W2B (Careerwright L0, branch `l0-local-release`, HEAD
b2aa090). Round 4 did everything asked. Its re-review found that the missed-answer note can
still give a false reason, and three small gaps. This is the last fix round: wording, the web
count and tests only. Matching rules, thresholds and ranking do not change.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`
2. `task-W2B-rereview-4.md`, "New findings" (finding IDs below are its own)
3. `task-W2B-report.md`, sections "# Fix round 3" and "# Fix round 4", for what was built
4. As needed: `task-W2B-fix-round-4.md`, ADR 0007 (as amended)

## Controller ruling (binds every note and label in this slice)
Three rounds in a row found a note whose claim about what ESCO contains was false in some
case. So: **a note says what the search did, never what ESCO contains.** A claim about the
search is true by construction. For example: "No main name of a skill ESCO lists as essential
holds all the words of “Operating farm machinery”, so it found no work." Keep it plain and
short. Apply the rule to the missed note, the too-general note ("none of them just that") and
any other slate note or web line that makes a claim about ESCO's contents. Check each one and
list them in the report.

## Fix now
- **I1:** as ruled. A full-release test on "operating farm machinery" that the note's words
  hold (it says what the search read). Update ADR 0007's quotes.
- **M1:** a model's too-general note asks for a narrower search only when no other search
  citing that answer found work. Add the case to `test_slate.py:533`.
- **M2:** the web's "found by N searches of ESCO" counts only searches that reached something
  (`!query.too_general && query.reach > 0`); test the singular and the plural.
- **M3:** `missed_answers_named` treats a one-word work style named in a "found no work" note
  as wrong; assert that case fails.

## Then
- `make check`; then `make acceptance` once before the final commit (check `pgrep -fl "make
  acceptance"` first). If a known flake recurs (the durable-runs shutdown hang, or W2A's phone
  strip test `world.spec.ts:273`), re-run once and report both runs exactly; do not change those
  tests.
- Hard rules: Edit/Write only for source changes (no scripts that rewrite files; the project's
  own generators are fine); stage explicit paths; never `answers-2.md`; never `.env`,
  `~/.nessa`, `~/.careerwright`; no live model call; no web request; no Docker pull of an
  uncached image; no headed browser or window on the product owner's screen; leave
  `spikes/world` and the running `careerwright-l0-*` stack alone; no subagents; never push.
  DBOS `application_version` stays `careerwright-l0-1`. Disclose every changed test input or
  assertion, with why.
- Append a "Fix round 5" section to `task-W2B-report.md`. Reply with only the short contract.
