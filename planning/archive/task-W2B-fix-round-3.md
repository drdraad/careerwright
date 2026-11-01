# Task W2B fix round 3 of 5

You fix what remains of Task W2, slice W2B (Careerwright L0, branch `l0-local-release`, HEAD
267a83f). Rounds 1 and 2 made every suggestion travel through a named essential skill, with a
whole phrase in one skill label, no work-style-only search and no alphabetical cuts. Round 2's
re-review found the named cases defensible, but common, generic answers still scatter, and a
few honesty gaps remain. This is the last matching round before session W2: what remains after
it goes on the product owner's sheet, not into round 4.

## Read first (all in `.superpowers/sdd/l0-sprint-tasks/`)
1. `implementer-contract.md`
2. `task-W2B-rereview-2.md` in full (finding IDs below are its own)
3. `task-W2B-fix-round-2.md` (rulings that still bind, as amended below) and the "Fix round 2"
   section of `task-W2B-report.md`
4. As needed: ADR 0007 (as amended), `docs/requirements-register.md` rows DIV1-02, DIV1-08,
   DIV1-10, REC1-03; plan section 4; CLAUDE.md invariants

## Controller rulings
- **N-I1, honest emptiness:** adopt the re-review's fix. An answer whose every search found
  nothing is named, in plain words, on full and short slates ("“Repairing physical objects”
  isn't how ESCO names any skill, so it found no work."); work style keeps its own note; on the
  live path, name an answer only when every query citing it found nothing. Add the
  `missed_answers_named` check to DSC-01, DSC-03 and the patients case.
- **N-I2, generic answers:** adopt the re-review's rule, provisional. A search too general to
  find work on its own (it reaches more than 50 occupations, or more than 5 different skills
  none of which names exactly its words) finds no work by itself; it may still add weight to
  work another answer found. The slate says so in plain words ("“Writing reports” is part of
  217 kinds of work in ESCO, too many to choose from. Say what the reports are about."). The
  two thresholds are named constants, recorded in ADR 0007 as provisional for the product owner
  at session W2. Where this stops a phrase a test or the prompt uses as its example ("planning
  shifts"), choose another phrase that still finds work, and disclose each change.
- **N-I3, rule 2 narrowed:** work style that is one word ("structured", "collaborative",
  "practical") is not searched; a longer work-style answer is searched under rule 1 and N-I2
  like any other ("working outdoors" reaches work through "work in outdoor conditions"). Reword
  the work-style note so it never claims an answer is not about the work. Bring DIV1-10 and
  REC1-03's rows up to date.
- **N-M4, order:** order by how specific the reaching search was (fewer occupations reached)
  before the share of essential skills, so a specific answer's work comes before a generic
  one's.

## Fix now
N-I1, N-I2, N-I3 and N-M4 as ruled; N-M1 (never cut inside an exact tie: extend the join's
best-30 and the search's 120 cut to the end of the tied group, with a unit test each); N-M2
(carry each search's and join's reach into `beyond_pool_limit`, "at least" where IDs aren't
kept; say what the join keeps); N-M3 (DSC-07 and DSC-08 get a task that finds work under rule 1;
`test_discovery.py:172` asserts the deeper note's words); the connection's article on a plural
ESCO title ("a warehouse operators for clothing"); register DIV1-08's case count. Report P01–P05
and the re-review's example answers before and after (its table, plus "working outdoors").

## Then
- `make check`; then `make acceptance` once before the final commit (check `pgrep -fl "make
  acceptance"` first). If a known flake recurs (the durable-runs shutdown hang, or W2A's phone
  strip test `world.spec.ts:273`), re-run once and report both runs exactly; do not change those
  tests.
- Hard rules: Edit/Write only for source changes (no scripts that rewrite files; the project's
  own generators are fine); stage explicit paths; never `answers-2.md`; never `.env`,
  `~/.nessa`, `~/.careerwright`; no live model call; no web request; no Docker pull of an
  uncached image; no headed browser or window on the product owner's screen; leave
  `spikes/world` unchanged; no subagents; never push. DBOS `application_version` stays
  `careerwright-l0-1`. Disclose every changed test input or assertion, with why.
- Append a "Fix round 3" section to `task-W2B-report.md`. Reply with only the short contract.
