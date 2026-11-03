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
