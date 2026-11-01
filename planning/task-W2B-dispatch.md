# Task W2, slice W2B dispatch: the deterministic sources

Where this fits: Careerwright L0 is mid-build (branch `l0-local-release`). Task W2 builds the
product owner's chosen "living world" into the app in four slices. W2A (the world layer and
its design references) is done and reviewed. You own W2B: the backend sources the first
moments and the two revelations stand on. W2C then builds the You chapter and the first
moments in the interface on top of your API; W2D closes acceptance and the register.

## Read first, in this order
1. Your brief (requirements, Global Constraints, standing rulings; exact values verbatim):
   `.superpowers/sdd/l0-sprint-tasks/task-W2-brief.md`
2. The slice plan, its W2B paragraph and the rulings binding every slice:
   `.superpowers/sdd/l0-sprint-tasks/task-W2-slices.md`
3. Your contract: `.superpowers/sdd/l0-sprint-tasks/implementer-contract.md`
4. `docs/plan/development-plan.md` section 4 in full (especially "The first ten seconds",
   "Usual is not confirmed", "Revelations are earned") and the Sprint W card (SW.5);
   `docs/adr/0014-the-living-world.md` decision 3; `docs/adr/0007*` (discovery and the slate,
   decision 12 on span-verified quotations); `docs/adr/0006*` (one run task per kind);
   `docs/adr/0012*` (capability: self-reported vs evidenced, unresolved).
5. Session 2's record of the slate (`docs/reviews/session-2-answers.md`: search it for "data
   analyst" and "arbitrary matching on keywords") and the five personas in `fixtures/`.
6. The code: `careerwright/profile/` (`slate.py`, `slate_explanation*.py`, `discovery*.py`,
   `commands.py`, `interview*.py`, `fixture_*.py`, `safety.py`), `careerwright/catalogue/` (the
   ESCO taxonomy), `careerwright/identity/activity.py` and `workflow.py` (the pinned durable
   activity pattern), `careerwright/worker.py`, `careerwright/api/`.

## What W2B delivers (backend, API and the regenerated client only)
1. **The first question's type-ahead:** "What do you do now, or what did you do last?" matched
   against occupation titles (preferred and alternative labels) from the pinned ESCO release.
   Deterministic, no model call, works before a key is connected and in the demo. No match is
   an honest empty answer the UI can turn into a sharper question; never an invented match.
2. **The first answer, recorded:** the chosen occupation saved through the profile's existing
   expected-version command path (`run_idempotent`, an `Idempotency-Key`). Use an existing
   field if one fits; if a new field is needed, it is a contract change: migrate, test and
   regenerate the client, and say so in the report.
3. **"Usual in your role, not confirmed yet":** the essential skills of the chosen occupation
   (ESCO), served as their own display-only state. Wherever anything is computed (readiness,
   gaps, ranks), such a skill stays unresolved (ADR 0012). The person picking one ("I've used
   this") is their own claim: self-reported, never evidenced. Record it through the existing
   capability or profile structures; no parallel store.
4. **The slate joined by shared essential skills, never by shared words in a title.** Check the
   "data analyst" case and the five personas before and after, fix where it matches on words,
   and amend ADR 0007. The first scatter of destinations follows from the first answer.
5. **The unexpected connection:** a deterministic rule over the slate that singles out one
   destination as a revelation, worded as a fact about the two roles ("Data analysts and
   statisticians share 7 essential skills"), never about the person, with its shared skills
   one step away. You choose the rule; record it in ADR 0007's amendment with why.
6. **The overlooked strength:** a new bounded run kind (ADR 0006: one `RunTask`, composed in
   `worker.py`, never a second call path), per the brief and ADR 0014 decision 3.
7. The first answer's response (type-ahead, usual skills and the first slate) within one second
   on the pinned release: show it with a test or a measured check, and say where it was run.

## Decisions the brief cannot know (the controller's)
- **Scope:** no interface work (W2C builds it on your API); no register family (W2D). Tag your
  tests with existing register IDs where they fit, and list the new requirement candidates in
  your report for W2D.
- **"One of their destinations"** for the overlooked strength means a destination in the
  person's world now: a target they chose, or a slate suggestion on their horizon. The
  proposal names which, and the confirm step shows it. Its skill must be essential to that
  destination in ESCO; its quotation must verify as a span of the person's pinned answers
  (reuse the slate explanation's verifier; only the quoted words are checked).
- **When it runs:** at most one proposal per conversation turn that added answers. Never on a
  turn where the support policy found a risk word (`safety.py`): that turn only acknowledges
  and offers a smaller step. Live only with the person's key and within their spend limit
  (the activity re-checks access, model, key and budget). Demo workspaces show one scripted,
  labelled example from the offline fixture path; never a provider call.
- **Confirming:** the strength shows only after the person confirms it, through a command
  (expected version, `Idempotency-Key`). Confirmed, it is self-reported ("you said so"), with
  the verified quotation as its source. Declining stores nothing about the skill.
- **DBOS `application_version`:** give the overlooked strength its own workflow, started
  beside the interview turn, not a new step inside an existing workflow, so the version stays
  `careerwright-l0-1`. If that is impossible, stop and report NEEDS_CONTEXT: CLAUDE.md names
  the version and changes to CLAUDE.md need the product owner's approval.
- **Tests** use fixtures or the test model's offline doubles only. No live call of any kind:
  not `make live-smoke`, `live-eval` or any other live command (R5).
- Architecture: new vendor or SQL imports only in the adapters listed in
  `backend/tests/architecture/test_boundaries.py`; identity never imports profile or catalogue.

## Hard rules
- Change source files with Edit and Write only: never `sed`, `awk`, heredocs, or scripts that
  rewrite files, not even for string replacements (generated outputs from the project's own
  tools are fine, such as `pnpm run generate`).
- Stage explicit paths only; never `git add -A` or `git add .`. Never stage or commit
  `answers-2.md`. Never push.
- Never read `.env` or anything under `~/.nessa` or `~/.careerwright`. No web requests.
- No headed browser, no `open`, nothing that puts a window on the product owner's screen.
- Leave `spikes/world` unchanged. Do not dispatch subagents.
- `make check` and `make acceptance` pass before your final commit.

## Report
Write your full report to
`.superpowers/sdd/l0-sprint-tasks/task-W2B-report.md`: what each of the seven deliverables is
(endpoint, command, run kind), the "data analyst" and persona slates before and after, the
unexpected-connection rule, the one-second evidence, every ruling you made, the requirement
candidates for W2D, and the paths a reviewer can skip. Then reply with only the short contract.
