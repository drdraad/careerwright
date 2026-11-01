# Task W2B fix round 2 of 5

You fix what remains of Task W2, slice W2B (Careerwright L0, branch `l0-local-release`, HEAD
e8c0bfb). Fix round 1 (e8c0bfb) fixed most findings; its re-review found the slate still reads
as arbitrary keyword matching, which the product owner rejected ("arbitrary matching on
keywords"; they would be "very disappointed" to see it). This round makes every suggestion
defensible to a person, even at the cost of fewer suggestions.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`
2. `task-W2B-rereview-1.md` in full: "The question that matters", "The smallest rule…", the
   new issues I-A and I-B, the Minors, and "The implementer's other concerns"
3. `task-W2B-fix-round-1.md` (rulings that still bind) and both sections of
   `task-W2B-report.md`
4. As needed: `task-W2B-review.md`, ADR 0007 (as amended), plan section 4, CLAUDE.md invariants

## Controller rulings (the re-review's three rules, adopted)
1. **Whole phrase, one skill:** a phrase reaches a skill only when every content word of the
   phrase (stemmed, stop words dropped) is in that one skill's label. Drop the any-word pass.
   Tighten the evaluation check `searched_through_skills` to every content word, so it would
   fail on what the product owner rejected.
2. **Work style does not retrieve destinations** (it says how someone likes to work, not a
   skill): skip a query whose `based_on` answers are all work style. No setting or flag: ADR
   0007 records it as provisional, for session W2 to confirm or reverse.
3. **Never cut ties alphabetically:** a search keeps every occupation it reaches up to the pool
   bound; equal scores order by the share of the occupation's essential skills the person's
   answers reach, the title only as the last tie-break, and that order reaches the slate's own
   ordering (`slate.py`) too.
- **The discovery prompt:** a new prompt version asks the model for short phrases in ESCO's
  skill wording. No live call to validate it (R5): say in the report that it is untested live.
- **Honest emptiness:** where the rules leave a slate small or empty (P01, "looking after
  people", P02's pool of 12), the slate gives its plain reasons. DIV1-02's pool target is soft
  ("where evidence permits"): change the integration assertion to check the bound and, below
  the target, the reason; update register row DIV1-02 and DSC-12 (`fewer_has_reason`). Disclose
  each changed assertion in the report with why.

## Fix now
- The three rules and the prompt, as ruled; P01–P05 and the re-review's example phrases
  ("looking after people", "caring for patients, giving injections", "teaching children, writing
  stories", "designing websites, writing code") before and after, in the report.
- **I-A:** a why-line never names another occupation's skill as this one's (the folded sound
  editor / sound designer case): a regression test on that case.
- **I-B:** resolved by rule 3, with a test that fails on alphabetical cuts.
- The re-review's Minors: a title several occupations share is not joined over the union of
  their skills (the slate asks the person to choose, as the first slate already does); P04's
  closest titles order by words matched first; the 120 pool limit exercised by a test again and
  DIV1-02 brought up to date; a moved or re-added answer does not count as new.

## Then
- `make check`; then `make acceptance` once before the final commit (check `pgrep -fl "make
  acceptance"` first). If a known flake recurs (the durable-runs shutdown hang, or W2A's phone
  strip test `world.spec.ts:273`), re-run once and report both runs exactly; do not change
  those tests.
- Hard rules: Edit/Write only for source changes (no scripts that rewrite files; the
  project's own generators are fine); stage explicit paths; never `answers-2.md`; never `.env`,
  `~/.nessa`, `~/.careerwright`; no live model call; no web request, and no Docker pull of an
  image that isn't already cached; no headed browser or window on the product owner's screen;
  leave `spikes/world` unchanged; no subagents; never push. DBOS `application_version` stays
  `careerwright-l0-1`.
- Append a "Fix round 2" section to `task-W2B-report.md`. Reply with only the short contract.
