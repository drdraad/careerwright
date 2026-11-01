# Task W2B fix round 4 of 5

You fix what remains of Task W2, slice W2B (Careerwright L0, branch `l0-local-release`, HEAD
392bc64). Round 3 did everything ruled; its re-review found two notes that tell the person
something untrue, and four small gaps. This round is wording, labels and tests only. Matching
rules, thresholds and ranking do not change.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`
2. `task-W2B-rereview-3.md`, "New findings" and "Changed tests and inputs" (finding IDs below
   are its own)
3. `task-W2B-report.md`, section "# Fix round 3" (line 750 on), for what round 3 built
4. As needed: `task-W2B-fix-round-3.md` (rulings that still bind), ADR 0007 (as amended)

## Fix now
- **I1:** the missed-answer note and the too-general note say what was checked: skills ESCO
  lists as essential for an occupation (the re-review's wording, or plainer, is fine). A test
  on "taking pictures" (or another case the re-review names) that the note no longer claims
  ESCO has no such skill. Update ADR 0007's quoted wording.
- **I2:** the join note names its real measure (the share of essential skills in common, not
  the count). Update the Vitest string and the ADR quote.
- **M1:** on the live path, the too-general note never asks the person to say more about an
  answer the model searched too generally. Point it at the search instead, in plain words.
- **M2:** one domain test of `_missed_notes` and `_general_note` with a model's queries
  (several queries citing one answer; a query citing a task and a one-word style, where the
  style keeps its own note as ADR 0007 says). Pure functions, no database.
- **M3:** make `tests/integration/test_evaluation.py:209` a real check (give the specific and
  the general answer the same channel), or, if that cannot work, disclose why.
- **M4:** the web marks a search that only added weight (the API's `too_general` flag) under
  "Found by these searches", and does not count it in "found by N searches of ESCO". Plain
  words, no new colour. Any new string goes through the existing vocabulary pattern.
- **The plural title** in `explain`'s `try_it` ("someone who works as warehouse operators for
  clothing"): use the same fix as the connection's article.

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
- Append a "Fix round 4" section to `task-W2B-report.md`. Reply with only the short contract.
