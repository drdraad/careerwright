# Task 6g slice B: report (implementer, worktree 6gb, branch wt-6gb)

Status: DONE_WITH_CONCERNS. Head c8d47b0, a fast-forward of `claude/confident-ramanujan-ux3saw`
(1f03a02).

Commits:
- d82c349 Muse proposes up to six Aim higher title ideas and reads the qualifications (discovery-queries-5)
- 64624fb code confirms Muse's title ideas and places them; Aim higher ranks work found by a title first
- b12bec2 Sam's and Maya's cases show Muse's confirmed ideas in Aim higher; their live-only checks
- e7b332a the Aim higher tier helper is private to the slate
- c8d47b0 ADR 0007's amendment, ADR 0015's line and the register rows

## What I built

1. **Muse's Aim higher ideas** (`profile/discovery.py`, prompt `discovery-queries-5`, keeping
   slice E's dash line). `DiscoveryOutput.aim_higher` (required in the strict schema): up to six
   titles, each quoting 1 to 3 answers, checked as title ideas are (bounded, the dash check,
   no inferred characteristic, each title once across hypotheses and Aim higher ideas). The
   model now reads the qualifications with their status (`DiscoveryInput.qualifications`,
   rendered as answers with `status`); the prompt says "never treat an expected one as
   achieved", and a title may quote a qualification by name. Qualifications alone never start a
   discovery. Bounds: output 2,000 tokens (was 1,500), prompt 10,000 bytes (was 8,000), so an
   attempt reserves $0.0037 on the test model, $0.053 on Spark, $0.196 on Wonder, from the
   registry. Older sealed inputs and proposals read with none. The demo proposer proposes none.
2. **Code confirms and places** (`profile/exploration.py`, `slate.py`, `horizons.py`). Every
   title idea (hypotheses `h1`..., then Aim higher ideas `a1`...) goes through one rule: an
   ESCO label joins the pool and is placed by level like any occupation; a title only the UK
   job-title index lists becomes a slate entry (`ListedTitle`), never in the pool, placed by
   every ISCO-08 group ONS codes it to (`place_title`: only when they agree on level and set);
   otherwise not yet found (Research this role, live). One reranker weighs both kinds. **The
   rule within Aim higher:** work found by a title (a confirmed idea, the person's own title, or
   a join) ranks before work only searches found. Listed titles honour kind-of-work exclusions
   (counted), the salary floor's counts (pay unknown, kept) and the AI filter (unscored).
   One whose groups disagree, or that lost its set's three, stays in the list beside the slate.
3. **Making a listed idea a target** through the profile's one write path (the save, as a
   researched title is). `stays_current` now counts the discovery's own title ideas, exactly as
   written, as titles the slate suggested, so the slate stays current (no paid Suggest again
   pushed).
4. **API facts:** `TitleIdea.groups`, `skill_level`, `horizon`, `position`, `left_out`;
   `DiscoveryProposalOut.aim_higher`; export format 5 (the proposal is in the export). Client
   regenerated.
5. **Web** (`Directions.tsx`, `vocabulary.ts`): a listed idea's card in its set at its place
   (closed: title and kind of work; open: Make this a target first, then "Found in the UK
   job-title index (ONS). Not compared with your experience yet." and the answers it came
   from; once saved, "Saved as one of your targets" with Remove). The UK-index list beside the
   slate holds only ideas in no set and not left out. The count line names the titles found in
   the index. New story `SlateWithAimHigherIdeas`.
6. **Slice A's three Minors:** the training sentence is said once under Aim higher, for its
   entries' levels (`aimHigherTraining`), never on cards; the placement note shows only when a
   set holds something; "More depth" relaxes the limit to 3 (`DEEPER_FAMILY_LIMIT =
   HORIZON_SIZE`), what a set can show, and its note says 3.
7. **Evaluation:** DSC-22 (Sam, now with "working with people" and "spreadsheets" disliked)
   and DSC-21 (Maya) each give a fixed model output of six ideas. New checks
   `aim_higher_from_ideas`, `titles_first_in_aim_higher`, `set_excludes`; `horizons_by_level`,
   `grounded` and `fewer_has_reason` now cover listed titles. DSC-23 (Sam) and DSC-24 (Maya)
   are live only (`Case.live_only`: run only when named, never offline, not `live`).
8. **Docs** (last commit, after the rebase): ADR 0007 amendment section (after slices E and A),
   ADR 0015 line, register rows DIV1-04, DIV1-11, DIV1-16, TEST1-16, STATE-10, PROF-13,
   MODEL-08; the runbook's Wonder discovery cost.

On the full release (focused integration run): Sam's Aim higher is careers adviser, customer
success manager, training and development officer (no equine dental technician); "Client
executive" (groups 2431 and 3321) stays beside the slate; "Onboarding specialist" is not yet
found. Maya's Aim higher is biomedical scientist (ESCO), genetic counsellor, clinical
scientist; "Children's nurse" (2221 and 5311) stays beside the slate; "STEM outreach officer"
is not yet found.

## Rulings (simplest reading; recorded in ADR 0007's amendment)

- **One rule for every title idea.** The hypotheses and the Aim higher ideas are confirmed and
  placed the same way, so a UK-index hypothesis is now placed in a set too (DSC-20's "Prompt
  engineer" is in Aim higher). Two lists treated differently would be confusing.
- **"A single search's hit" read as "work only searches found".** Tier 1 is any candidate whose
  own matches are all searches; a hit of two searches is not lifted (else the equine dental
  technician, reached by one search plus a too-general one, would rank first). Tier 0 adds the
  person's own titles to ideas and joins.
- **A listed title's weight** is a title idea's (exact match 1, weight 0.9). Its kind of work
  is its first ONS group's minor group.
- **Groups that "disagree"**: different levels, or one level in two sets (the level-4 corner):
  neither set.
- **Keeping the slate current** by counting the discovery's own ideas, rather than a new
  source kind and migration. Typing one of its ideas exactly also keeps it current (recorded
  limit).
- **Maya's case count:** plan v1.6 says "four to six evaluation cases"; with DSC-24 she has six,
  and the browser test is beside them. The test that counted the browser test in the six now
  counts evaluation cases (`tests/eval/test_evaluation.py`, school leaver test). This loosens
  that test by one: flagged below.
- **Output bound 2,000, not 2,500:** at 2,500 a discovery on Wonder ($0.22) would push the live
  evaluation's Wonder explanation case (two runs) past its $0.40 cap. 2,000 still gives six more
  ideas room at the earlier allowance per item.
- **Rebase:** I rebased slice A onto the integration branch early (resolving ADR 0007 and the
  register by keeping both slices), then replayed only my commits with `--onto` once the
  controller integrated slice A. The code under slice A was identical; my branch is a clean
  fast-forward.

## Checks run (all on the final code unless said)

- TDD, RED then GREEN: `test_discovery_contract.py` (ImportError on `MAX_AIM_HIGHER`, then 23
  passed); `test_horizons.py` (ImportError on `place_title`, then 19 passed); `test_slate.py`
  (ImportError on `ListedTitle`, then 25 passed); the slate-current rule (1 failed, then
  passed); web `discoveryWords.test.ts` and `Directions.test.tsx` (6 failed, then 92 passed).
- `make check` after each change and after the rebase: exit 0. Backend 2214 passed, 123
  skipped (pre-existing: bodies kept only on the curating machine); web 513 passed; Biome, tsc,
  client drift clean.
- Focused integration, under the lock, one guarded command each, lock released each time:
  1. `pytest -m integration test_evaluation.py test_discovery.py test_role_space.py
     test_export.py test_slate_explanations.py test_reference_data.py test_interview_turns.py`:
     108 passed, 2 failed (Sam's "Account manager" is ESCO's after plural folding, so the case
     was wrong; the "More depth" test still expected 4).
  2. After fixing both (Sam's disagreeing idea is now "Client executive"; the test expects 3):
     `test_evaluation.py` plus the depth test: 29 passed, "discovery cases: 22, failures by
     type: {}".
  Not re-run after the last two code commits: a mypy-only rewrite of one expression in
  `fewer_has_reason` (same logic) and the rename of a private helper.
- Journey walk (contract item 6), Storybook on 127.0.0.1:6117, telemetry and update check off,
  stopped afterwards; story You / Slate with Aim higher ideas at 1280 and 390: headings Next
  step and Aim higher; one training line under Aim higher, none on cards; each closed card a
  title and one kind-of-work line; the open listed card has one place to act (Make this a
  target, bright teal), then two short sections; the count line one sentence; no em dash in
  any added word. Agent observations, not the human design review.
- `make acceptance`: not run, the controller runs acceptance (Playwright and the Storybook
  build; the web's new card is covered by Vitest only).

## Live calls

None. Cost $0. `discovery-queries-5` is not qualified live: the controller's capped check is
`make live-eval CASES=DSC-23` and `CASES=DSC-24` (test model; about $0.0037 reserved each).

## Not run, and concerns

- **The prompt is unqualified live.** Whether Muse proposes useful Aim higher titles that the
  lists confirm is only shown with fixed outputs. DSC-23 and DSC-24 ask for at least one
  confirmed idea in Aim higher and the rule held.
- **Maya's case cap:** the school-leaver test now counts evaluation cases only (six), where it
  counted the browser test too. This follows the plan's words and the dispatch, but loosens a
  test by one; the controller may prefer DSC-21 to double as her live check instead.
- **"Account manager" is in ESCO** after the product's plural folding ("accounts manager",
  bank account manager, ISCO 3312), so the live model's ideas may land on surprising ESCO
  occupations through hidden or folded labels. That is the existing confirmation rule (R11),
  for the product owner's look.
- **Known limits (recorded):** a listed title has no "Not for me" and is not listed under "Show
  why something wasn't included"; typing one of the slate's own ideas exactly keeps the slate
  current; a listed title's kind of work is its first ONS group's.
- The ADR 0015 decision 5 sentence "reads only the person's confirmed answers about work" is
  widened by the qualifications; the amendment line says so.
- Slice A review's other Minors (4, 6 to 11) are untouched, as the dispatch scoped.
- Walk artefacts landed in the main tree's gitignored `.playwright-mcp/` (the tool's allowed
  root); I moved my three files to my scratchpad. Nothing of mine is left in the main tree but
  this report.

## Paths a reviewer can skip

`apps/web/src/generated/**` (generated client and openapi.json).

## Review

Independent review of 1f03a02..c8d47b0 (worktree `/Users/darianraad/Code/careerwright-wt/6gb`,
head c8d47b0), 2026-11-03. Read the card, the dispatch, the design note, slice A's report and
review, this report, then the 4,856-line package in passes (contract, slate and placing,
evaluation, web, docs), then the worktree code around each named risk below. Read-only checks,
offline, with the backend venv: the prompt's size at every field's true bound, the worst-case
output size, and the pinned ESCO release's labels for "account manager". No suite re-run, no
Docker, no web requests, no live calls.

### Spec Compliance
- ✅ Spec compliant with the card's slice B and dispatch items 1 to 5:
  1. `discovery-queries-5`: up to six `aim_higher` ideas, each quoting 1 to 3 whole answers,
     checked as title ideas are (bounds, the dash check, no inferred characteristic). The
     qualifications reach the model with their status; the prompt says an expected one is never
     achieved, and no code reads a status as met (its only uses are the prompt and the quotable
     name). Qualifications alone never start a discovery. The demo proposer proposes none (test).
     The prompt keeps `DASH_RULE` and has no em or en dash of its own.
  2. One confirmation rule for hypotheses and Aim higher ideas: an ESCO label joins the pool; a
     title the UK index lists exactly becomes a `ListedTitle`, never in the pool, placed by
     `place_title` only when every group agrees on level and set; otherwise not yet found, with
     Research this role. Aim higher's title-first tier is a rule in code with a domain test and
     evaluation checks; Next step is unchanged (no option ranks first there). The slate stays a
     pure function of its inputs.
  3. A placed listed idea becomes a target only by the person's click, through the profile save
     (expected version, idempotency key).
  4. Slice A's Minors 1, 2 and 5 are fixed.
  5. Sam (DSC-22) and Maya (DSC-21) give fixed outputs with real expected sets: exact six-entry
     `title_idea_reasons`, `aim_higher_from_ideas` with count 3, and Sam's `set_excludes`
     (equine). DSC-23 and DSC-24 are live only, outside the default set, never offline (test).
  6. ADR 0007's amendment, ADR 0015's line, the register rows, export format 5, the runbook.
  - The reservation is priced from the registry ($0.0037 test, $0.05325 Spark, $0.196 Wonder);
    three attempts fit the $0.50 default and the session's $1.60 (tests parametrised over every
    run kind); the Wonder explanation case is $0.392, within its $0.40.
- ⚠️ Cannot verify from diff: `make check` and the focused integration runs (the report's
  claims; the last two commits not re-run under integration); whether DSC-21's count 3 would
  fail without the tier rule (needs the full release; likely, by the relevances); `make
  acceptance` (Playwright, the Storybook build with the new story); the 1280 and 390 walk (agent
  observation); the live qualification of `discovery-queries-5` (DSC-23, DSC-24: the
  controller's); the product owner's live look at Maya and Sam (not run, requires human).

### The three rulings
1. **The slate stays current when one of the discovery's own ideas becomes a target:**
   acceptable. Only a change of targets reaches the new rule; every other answer is still
   compared field by field (`backend/src/careerwright/profile/exploration.py:284` and the loop
   after it), so no changed answer can make a stale slate read as current, and the slate itself
   is computed from the pinned answers. What widens: a target equal to any of the model's ideas,
   exactly as written, keeps it current, including ideas never suggested (not yet found, not
   searched) and ones typed rather than clicked. That is the same kind of change as Task W2E's
   "a choice from the slate confirms it", and ADR 0007's known limits record it. See Minor 5.
2. **Maya's cap counted as evaluation cases only:** a fair reading of plan v1.6's words ("four
   to six evaluation cases"), though Task 6e's test and the no-job audit counted the browser test
   among them; the dispatch required her live-only case. The controller's call (Minor 4).
3. **"Account manager" on "bank account manager":** the person sees ESCO's title, never one
   they didn't get. Checked in the pinned release: ESCO v1.2.1 lists "account managers" as an
   alternative label of bank account manager (3312), so the fold lands on ESCO's own label. The
   open card says "What you enjoy: ... Careerwright thought of the title "Account manager" from
   it and matched that title to this occupation in ESCO." (`apps/web/src/lib/vocabulary.ts:1025`),
   one step away. True; whether it is a good Aim higher pick is the product owner's judgement.

### Journey and load (Part 3)
Walked in code (`Directions.tsx`, `vocabulary.ts`) and the Vitest cases:

| Step | Type | Actions | Lines |
|---|---|---|---|
| View row and count line | 0 | 4 or 5 view buttons | 1; adds "and N titles found in the UK job-title index" when any |
| How Careerwright searched (closed) | 0 | 1 disclosure | the placement note only when a set holds something |
| Next step | 0 | 1 toggle per card; the open card's actions unchanged | heading; title and one line per closed card |
| Aim higher | 0 | 1 toggle per card | heading; one training line for the set (was on every card); title and one line per closed card |
| A listed idea, open | 0 | 1: Make this a target (bright) | 2 section titles, the found line, kind of work, 1 to 3 answer lines |
| After choosing | 0 | Remove, then Undo | "Saved as one of your targets" |
| Beside the slate | 0 | none on UK-index titles; Research this role per not-yet-found title (live) | 2 lines and the answers per title |

No new place to type, no competing next action, nothing shown before a choice that must come
first, actions teal, no em dash in any added word, the prompt or this report. Net: fewer lines
than slice A for a full Aim higher set. Two load notes are Minor (11, 12).

### Strengths
- One rule for every title idea (`_title_ideas`) replaces the old hypothesis loop instead of
  adding a second path; the reranker weighs ESCO candidates and listed titles as one `_Option`,
  and the Aim higher tier is one boolean in its gain.
- Unknown stays unknown: a listed title's pay is counted unknown and kept, its AI score unscored
  (kept or left out as the person's filter says), never 0.
- `place_title` is pure and tested on its corners: levels that disagree, one level in two sets,
  no groups.
- The evaluation's level oracle and set reader are independent of the product's tiers and
  table, and every new check's failure path is unit-tested.
- An honest report: the bound trade-off, the cap reading, the folded ESCO title, the limits.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
1. **Output bound against the worst case** (`backend/src/careerwright/profile/discovery.py:61`).
   At every field's bound (17 items, each quoting three 120-character answers) the output is
   about 8,450 bytes, roughly 2,100 tokens at 4 bytes a token, against 2,000; before slice B it
   was about 1,390 against 1,500. The report's "room at the earlier allowance per item" doesn't
   hold (1,500 over 11 items is about 136 an item; six more need about 820, not 500). A cut-off
   response ends the run as a visible failure and real answers are far shorter, so no truth or
   cost issue. Fix: say the bound is for typical answers, or raise it with the Wonder evaluation
   cap; watch output tokens in DSC-23 and DSC-24.
2. **A repeated title is refused, but the prompt doesn't say so** (`discovery.py:280`; the
   instructions at `:326`). "title ideas: each title once" across both lists is a new refusal; a
   model that puts one title in both lists costs a repair request, and a repeat after it fails
   the discovery. Fix: one clause in the prompt, or drop the later copy in code. Watch in the
   live check.
3. **A live command that now fails by design** (`docs/requirements-register.md:372`). TEST1-16
   still gives `make live-eval CASES=INT-16,INT-17,DSC-21`; DSC-21 now carries a fixed output's
   exact `title_idea_reasons` and count 3, which a live model won't reproduce, while its note says
   live is DSC-24. Fix: name DSC-24; consider `select` refusing a case with a fixed output.
4. **Maya's cap** (`backend/tests/eval/test_evaluation.py:98`): loosened by one, openly flagged.
   The controller's call.
5. **The stays-current widening is wider than the dispatch's "an ONS idea placed in a set"**
   (`exploration.py:284`): not-yet-found and not-searched ideas too, typed or clicked; recorded.
   The integration test for it (`backend/tests/integration/test_discovery.py:494-516`) uses the
   fake's only idea, "orbital gardener", which is not yet found, so the listed path is shown only
   by the domain test and Vitest. Fix later: a listed idea in that test.
6. **Provenance:** a listed idea made a target is stored as a "Direct entry" save, so the export
   can't tell the person's click on the discovery's idea from a typed title (Task 6e's
   researched-title precedent). Final review.
7. **Exclusions undercounted under "hide unscored"** (`exploration.py:481`): `kept` is emptied
   before `choose_slate` counts kind-of-work exclusions, so a listed title in an excluded kind of
   work is counted nowhere and "Your exclusions removed N" is one short. Edge.
8. **No test drives `_hard_filters` and `_placed` for listed titles** (the AI filter leaving one
   out as `left_out`, the floor counting one as pay unknown). The code reads right; coverage for
   the final review.
9. **`titles_first_in_aim_higher` passes trivially on DSC-21 and DSC-22** (all three Aim higher
   entries are ideas). The rule's effect is pinned by count 3 and Sam's `set_excludes`; Maya has
   no such pin. Coverage.
10. **Prompt bound at the true field bounds** (`backend/tests/domain/test_discovery_contract.py:418-429`):
    with every text at 120 ASCII characters the prompt is 10,060 bytes against 10,000 (8,596
    against 8,000 before slice B); the test keeps the task lists at about 103 characters.
    Pre-existing pattern; the reservation stays far above real token counts.
11. **The open listed card's words** (`apps/web/src/components/Directions.tsx:658-660`): under
    "What the work is" it says where the title was found and that it isn't compared, not what the
    work is; "ONS" is unexplained; and no line says entry requirements aren't checked, where an
    ESCO card says "Entry requirements aren't researched yet." For the product owner's sheet.
12. **Same kind of title, different affordance:** a UK-index title in a set can be made a
    target, one beside the slate can't (`Directions.tsx:1103-1125`). For the product owner.
13. **Counts of titles worded as occupations:** `few_matched` and `exclusions_removed`
    (`vocabulary.ts:994`, `:1002`) say "occupations" while their counts include listed titles.

### Questions for the product owner's session (suggestion quality)
- Sam's Aim higher: careers adviser, customer success manager (kind of work "Business services
  agents not elsewhere classified"), training and development officer; human resources officer
  (ESCO) is not among them. Sensible?
- An idea that folds onto an ESCO title (Account manager onto bank account manager): keep, or
  ask for exact titles only?
- "Children's nurse" beside the slate, with no way to choose it: acceptable?

### Assessment
**Task quality:** Approved
**Reasoning:** Slice B does what the card asks: the model proposes, code confirms by the existing
rule, places by level and ranks title-found work first in Aim higher, the person chooses, and no
changed answer can make a stale slate read as current. The Minors are fragility to watch in the
controller's live check (the bound, repeated titles), record tidiness and load polish; none
changes a decision, hides a failure or loses input.

## Fix round (implementer, worktree 6gb, branch wt-6gb)

Status: DONE_WITH_CONCERNS. Head 95d3228, a fast-forward of `claude/confident-ramanujan-ux3saw`
(3759c1c). The rebase replayed slice B's five commits with new SHAs (d82c349 is now 708ad66,
64624fb c8fa8ed, b12bec2 35a6f58, e7b332a c09e446, c8d47b0 23b980e); their code is the same.

Commits:
- 783d305 the discovery's output bound holds the largest answer the check accepts and its reasoning
- 495e1e5 the discovery prompt says each title once, as the check refuses a repeat
- 95d3228 ADR 0007's amendment, the runbook and the register rows (MODEL-08, DIV1-16)

### Minor 1: the output bound
- **Measured** in `test_the_output_bound_holds_the_largest_answer_the_check_accepts_and_its_reasoning`
  (`backend/tests/domain/test_discovery_contract.py`): 8 queries, 3 hypotheses and 6 Aim higher
  ideas, each text at its bound (80 characters, the widest channel) and each quoting three
  answers of 120 characters; the test first asserts the check accepts it. It is 8,326 bytes.
- **Tokens:** 3 bytes a token, below what Muse's prompts measured (DSC-01 on Wonder, 31 October:
  557 input tokens for 2,366 bytes of instructions and answers, so 4.2 a token or more): 2,776
  tokens. At the reviewer's 4 a token it would be 2,082.
- **Reasoning shares the bound** (Meta counts it in the output; the ledger's discovery rows show
  output tokens that include it). At minimal effort the ledger's most is 524 in a discovery
  request and 768 in any request, so the test allows 800.
- **Headroom:** a tenth more. 2,776 + 800 = 3,576, plus 357 = 3,933, so the bound is now
  **4,000 tokens** (was 2,000).
- **Reservation, from the registry as before** (the shown estimate uses the same function):
  | Model | Per attempt, before | After | Change |
  |---|---|---|---|
  | Test model | $0.0037 | $0.0049 | +$0.0012 |
  | Spark | $0.05325 | $0.07525 | +$0.022 |
  | Wonder | $0.196 | $0.292 | +$0.096 |
  Three attempts still fit Spark's $0.50 default run limit ($0.226, now the figure the API's
  spend estimate for a discovery states) and the session's $1.60 on Wonder ($0.876).

### Minor 2: repeated titles
- One sentence in the prompt, after the Aim higher paragraph: "Name each title only once, in
  hypotheses or aim_higher." Still `discovery-queries-5`: nothing has run on it (slice B is not
  integrated and no live call used it). The dash line stays. The prompt at every list bound is
  9,135 of its 10,000 bytes, so no words were trimmed.
- Test: `test_the_prompt_says_each_title_once_as_the_check_refuses_a_repeat`, beside the
  existing refusal test.

### Checks
- RED then GREEN: the bound test failed at 2,000 (`assert (3576 + (3576 // 10)) <= 2000`), then
  passed at 4,000; the prompt test failed on the missing sentence, then passed.
- Pinned figures updated to the new arithmetic: `test_an_attempt_reserves_both_requests_at_their_bounds`
  and three tests in `backend/tests/tools/test_live_eval.py`.
- `make check` after each change and after the rebase: exit 0 each time (backend 2216 passed,
  123 skipped, the curating machine's bodies as before; web 513 passed; Biome, tsc, client drift
  clean).
- Focused integration, under the lock, one guarded command, lock released:
  `pytest -m integration test_discovery.py test_slate_explanations.py test_live_eval_ledger.py
  test_evaluation.py`: 60 passed. Run before the rebase; the rebase added only planning files.
- `make acceptance`: not run, the controller runs acceptance.
- Live calls: none. Cost $0. The controller's checks DSC-23 and DSC-24 now reserve $0.0049 each
  on the test model.

### Concerns
- **The Wonder evaluation loses two combinations.** Its per-invocation cap stays $0.40 (I did not
  change a budget cap). A discovery case still runs alone ($0.292), but an interview with a
  discovery ($0.468) and the explanation case ($0.584, also past the scope's $0.50) are now
  refused before any call. The test now says so, and the runbook and `tools/live_eval.py` say so.
  To run either on Wonder, the cap is the controller's call.
- The ratio of 3 bytes a token is an estimate, not a measurement of Muse's output tokenizer;
  DSC-23 and DSC-24 will show real output tokens.
- A model could repeat one quote inside `based_on` (the check folds repeats), or pretty-print
  its JSON; neither is in the measured worst case. The headroom covers ordinary formatting.
- The other Minors (3 to 13) are untouched, as the dispatch scoped.
