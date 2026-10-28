# Sprint 0 review: resolve the expensive uncertainties

- Date: 2026-10-28. Branch `l0-local-release`.
- Historical reviewed revision: `25bdb1b`, the last Task 2 commit that changes code or data
  (after fix round 1). The original candidate checks below ran on it.
  Sprint 0 commits: `e32fb12`..`2bb36e5` (Task 1: S0.1–S0.4) and
  `e925c57`..`25bdb1b` (Task 2: S0.5, S0.6 and fix round 1).
- Implementation reviewer: the Task 2 implementing agent, not independent of the work.
  Composition reviewer: Codex, inspecting all 18 images and the reference sources, with
  fresh design checks recorded under Visual findings. This is an **agent pre-review —
  not the required human review** (R2), and does not qualify the current application.

## Outcome

Sprint 0 delivered its technical decisions and evidence:
- A real Meta call returns a typed result on the pinned model.
- A durable DBOS run survives worker kills without corrupting its accepted result or
  journalling a secret.
- The L0 boundary and the dependency pins are recorded.
- The supplied fixture pack is placed and independently hand-checked.
- The real-source corpus has a manifest with owners.
- Every M0 requirement ID, every plan section 8 regression family and the untagged M0
  sections have register rows with planned test IDs and owners. The rows paraphrase the
  specification. Ten families were compared line by line against the specification text;
  the rest have had a structural check only.
- Three signature compositions exist in honest default, unknown-data and failure states.

**At Sprint 0, no application existed yet.** The product journey was therefore not
demonstrable from a UI. The composition review finds a coherent visual direction, but two
phone conversation blockers (S0-V01/S0-V02) need correction before that layout is reused.
Human approval of the compositions and the other human gates remain **not run — requires
human** (ruling R2).

## Exit evidence (Sprint 0 card)

| Card exit evidence | Result | Evidence |
|---|---|---|
| A real call succeeds with a typed response | **Passed** (Task 1) | `docs/evidence/sprint-0-spike.md` S0.2; ledger calls 3–7, 8 and 10 |
| An invalid key fails visibly | **Passed** (Task 1) | ledger calls 1, 9 and 11 |
| Worker recovery does not corrupt the accepted result | **Passed** (Task 1); suite re-run on this revision: 12 passed | ADR 0002; command below |
| Persisted state contains no credential | **Passed** (Task 1, live key scan). Limit: the live scan did not test windows of the private text; the fake-model suite does | ADR 0002 "Evidence" |
| Manually checked TRACE-01 arithmetic and five persona expectations committed | **Passed** (Task 2), with 9 findings for implementers. Domain-reviewer sign-off: **not run — requires human** (H-07) | `docs/evidence/fixture-hand-check.md` |
| Every unknown dependency has a named owner and disposition | **Passed** | `docs/dependencies.md` (packages and runtimes), `corpus/manifest.json` `open_items` (sources and reviewers), `docs/requirements-register.md` (owners per test) |
| If live access is blocked, the spike is blocked | Not blocked: key, Standard entitlement and test model all work | ADR 0003 |

| Deliverable | Result | Evidence |
|---|---|---|
| S0.1 scope and dependency matrix | Done (Task 1). Design tooling added to the matrix in Task 2 | ADR 0001, `docs/dependencies.md` |
| S0.2 Meta qualification | Done; ADR 0003 is **provisional** (H-09) | ADR 0003 |
| S0.3, S0.4 durability and the journal boundary | Done (spike code; product versions are Task 3) | ADR 0002 |
| S0.5 fixtures | Done. The plan said to reconstruct P01–P05 and TRACE-01, but ruling R1 used the supplied original pack instead (byte-identical, hashes recorded). The A–I fixture is absent from the pack, so it was reconstructed and labelled | `fixtures/` |
| S0.6 corpus manifest | Done as a scaffold: 33 page slots and 2 failure cases with owners. **0 of 33 pages collected**, as planned (Sprints 3–5) | `corpus/` |
| S0.6 design references | Done; 18 of 18 automated captures pass. Human approval **not run** (H-02) | `docs/design/` |
| S0.6 requirement-to-test register | Done: 355 IDs covering all 16 M0 requirement IDs, all 14 regression families, the untagged M0 sections (including a `PLN` anchor for spec §12) and 10 human gates. Ten families were fidelity-checked against the spec text in fix round 1; the rest have a structural check only | `docs/requirements-register.md` |

## Checks run on the final candidate (`25bdb1b`)

| Command | Result |
|---|---|
| `cd backend && uv sync --locked` | Audited 54 packages; lock current |
| `uv run --locked ruff format --check .` | 29 files already formatted |
| `uv run --locked ruff check .` | All checks passed |
| `uv run --locked mypy` | No issues in 29 source files |
| `uv run --locked pytest` | 63 passed, 12 deselected (integration) |
| `uv run --locked pytest -m integration spikes/durable` (Docker 29.1.2 aarch64, PostgreSQL 16.15) | 12 passed in 31.61 s; no spike container left behind |
| `uv run --locked python -I ../fixtures/m0/validate_fixtures.py` | `"status": "passed"`. The validator also rejected all 9 single-value mutations (hand check §1) |
| `cd docs/design && pnpm install --frozen-lockfile` | lockfile current |
| `pnpm run contrast` | 65 of 65 pairs pass |
| `pnpm run check-data` | 64 fixture assertions pass. Mutations of three values each failed it (first round) |
| `pnpm run screenshots` | 18 of 18 captures pass: axe 4.14.0 (WCAG 2.0, 2.1 and 2.2 A/AA), overflow, console, fonts, label collisions. The re-shot PNGs were byte-identical to the committed ones |

Not run in Task 2: live Meta calls (none were needed, and none were made); amd64 images;
WebKit or Safari; a 768×1024 tablet layout.

## The six questions

**1. Does the journey make sense from entry to the latest outcome?** Not demonstrable from
a UI: none exists until Task 4. The nearest evidence:
- The compositions show the intended You, Roles and Routes chapters, each with a
  missing-data path and a failure path.
- The spike CLI shows a failure surfacing visibly (an invalid key ends
  `failed/provider_authentication`).
- ADR 0001 and the register keep all six chapters in scope. Each chapter's requirements
  have an owning task (T3–T16), and none is dropped.

Result: **not run (no UI yet)**.

**2. Do shared concepts mean the same thing everywhere?** Checked across the
specification, the register, the hand check, the compositions and the ADRs:
- Unknown is never zero.
- Conditional readiness is stated in the group/journey notices; individual route cards
  need to retain it when separated from those notices (S0-V03).
- Stale and failed stay distinct.
- Economic and direct cost are never mixed: TRACE-01 versus DIRECTAI, with labels checked
  in the compositions.
- Search coverage is "complete" or "budget truncated".

Hazards found and recorded for implementers:
- P02 carries `current_net_income_minor: 0` beside an unconfirmed baseline (H2).
- P03's option fails two hard constraints but names one reason (H1).
- TRACE-01 route IDs are bare letters (H8).

**3. Can one consequential claim be traced to source, version, confirmation and
calculation?** Traced: route B's "lowest balance £4,850" in the route composition.
- The page value is bound to `data.js`. `check-fixture-data.mjs` asserts it equals
  `worked_trace.json` `print_snapshot.minimum_prefunded_cash_minor` (file SHA-256 in
  `fixtures/README.md`).
- The page also recomputes the six-month ledger from the fixture's payments, living costs
  and income, and logs an error on any mismatch.
- The hand check derives the same figure by hand (§4), from spec §20's stated inputs.
- The "confirmation" is the fixture's own synthetic confirmation
  (`work_pattern_approval: confirmed_in_synthetic_fixture`). No product command exists yet
  to record a real one (Task 3/5).

Result: **passed at the reference level**. A product-level trace is Sprint 5 and later.

**4. Are module and process boundaries intact?**
- `backend/src/nessa` is still empty, and all Sprint 0 code is under `backend/spikes/`,
  so no domain module exists to contaminate.
- The design tooling is isolated under `docs/design` with its own pnpm lockfile, and it is
  dev-only: Playwright and axe-core, as the plan's candidates.
- Open items carried to Task 3:
  - The non-owner database roles (the spike connects as owner).
  - Typed failure when the app database is down during an activity.
  - The accepted-output check before re-calling the model (M4).
  - Moving the model factory and budget policy out of the spike CLI (M7).
  - A bounded `make stop` (an unexplained worker shutdown hang, 1 in 19 runs).
  - Refusing the Contributor test model for non-synthetic workspaces.

None blocks Task 2's deliverables.

**5. Is the interface coherent and polished?** The reference surfaces, typography and
selection language are coherent; phone task completion is not established. The review of
all 18 captures, reference sources and targeted Chromium layouts reproduced a hidden
profile-review entry point and a covered composer/retry action. Conditional readiness,
stale selection, unsupported preference-fit copy and unknown-state hierarchy also need
correction. The detailed agent critique and earlier fixes are in
[`pre-review-sprint-0.md`](../design/pre-review-sprint-0.md).
**Design-review scores: not run — requires human (H-02).** The checklist follows below.

**6. What exact evidence establishes completion?** The commands and results above, on
revision `25bdb1b`. Known gaps:
- Corpus: 0 of 33 pages.
- Human gates: H-02, H-07, H-09, and later H-06 and H-08.
- Design references cover no tablet layout, no phone focused-chart or map-overview layout
  and no keyboard flows.
- amd64 is not executed.

Next dependent milestone: Task 3 (Sprint 1 platform), built on ADR 0002 and the register.

## Coherence question (Sprint 0 card)

**Can one confirmed profile change flow through a typed command, a durable run and a
versioned result without the LLM owning a transaction?** Partly established:

- The durable run and its typed result are shown (ADR 0002):
  - The workflow carries only a run ID.
  - One bounded activity opens the sealed input and key just in time.
  - The model returns a schema-validated proposal (`NativeOutput`).
  - The activity stores it once as the run's accepted output, idempotently, and returns
    a reference.
- The model writes nothing else. Its output is stored only as the run's artefact and
  changes no profile or plan record.
- Not yet shown: a confirmed profile change entering as a typed, versioned command
  (expected version, idempotency key) and producing a new profile version. There is no
  profile store or command layer until Task 3 (S1.2) and Task 5 (InterviewTurn patches).
  Register rows PROF-03/04/05, VERSIONS-01 and DUR-01 own it.

**Does the local scope still deliver the complete product journey?** Yes, on paper:
- ADR 0001 keeps all six chapters, the sure/unsure entry, the apply-now, conditional and
  unavailable outcomes, and the three exports.
- The register gives every chapter's requirements an owning task.
- What L0 drops is hosting only: Cloud services, TLS, real Google sign-in and the
  deployed smoke test. It is listed in register section 7.

**Do the visual compositions use honest data states?** Yes, by construction and by check:
- Every fixture number is asserted against the fixture files.
- Invented map listings are labelled synthetic on every page.
- Unknown values are drawn as unknown ("Not confirmed, not £0", "Pay not stated", "none
  found in the 4 sources checked", "Schedule not available").
- Scenario ranges are stated as not evaluated rather than drawn at zero width.
- A failed search keeps the previous comparison as stale, never as "no routes".

The composition critique identifies presentation limits despite those data checks:
individual cards lose their readiness condition (S0-V03), and the fixed selected journey
does not carry its own stale version (S0-V04). Honest data needs those qualifications to
remain visible with the selected item.

Building the route comparison also exposed a real error in the hand check (incomplete
dominator lists for DIRECTAI G and H). It was corrected in `f5b73d1`.

The independent review of Task 2 (fix round 1) found that the route reference itself
undercut this answer:
- The key said every route in the shaded area is bettered by a route on the line, yet D
  sits on the line and is bettered by B.
- Layers 2 and 3 looked the same.
- AI Resilience lacked its Experimental marker.

All three are fixed in `25bdb1b`. Dominated points are lifted off the line by a halo, a
note names the equal-time tie, layers are a disc and a ring with labels, and every AI
display carries the badge.

## Visual findings

**Agent pre-review — not the required human review.** The full
[evidence, screenshot matrix and eight findings](../design/pre-review-sprint-0.md#open-findings)
are recorded in the existing composition critique.

- **Strengths:** consistent ink/light surfaces, typography and selection; labelled
  synthetic data; explicit unknown pay and reduced coverage; distinct route-layer shapes.
  The inspected desktop Gantt and ledger explain the assessment gate, payments and
  pre-pay low balance. The early sketch has a provisional title and research disclaimer,
  as well as its dashed edge.
- **Phone blockers (S0-V01/S0-V02):** both the profile panel and its mobile summary are
  hidden. The reply field at y=775–819 is covered by the sheet beginning at y=632, and
  scrolling cannot expose it; the work area has no scroll range. The failure retry
  button is also covered. Correct these before reusing the conversation layout.
- **State clarity (S0-V03–S0-V06):** route cards need their own condition, the selected
  stale journey needs its old version/freshness, the unknown Roles card must not claim a
  preference match, and unknown Routes should retain B's known 9 months/£2,400 and More
  affordance.
- **Hierarchy (S0-V07/S0-V08):** phone failure/unknown stacks put the first listing or
  route behind the sheet. Default desktop You and failed Roles have competing filled
  actions, contrary to the stated primary-action convention.

Fresh design checks: **64 fixture assertions, 68 contrast pairs and 18 Chromium captures
pass**. The screenshot checker and contrast checker wrote only to a temporary folder;
all 18 PNGs and both generated reports match the committed files byte for byte. Separate
layout probes reproduced the phone blockers and absent unknown-route expansion control.
Passing the baseline checks does not establish task usability.

Coverage: all nine composition/state pairs at desktop and phone sizes, plus five default
desktop section captures. No tablet, phone expanded sheet, focused chart/map view, 200 %
zoom, keyboard journey, VoiceOver or Safari check was run. Dense data, negative economic
cost and scenario ranges remain uncomposed. No application code was changed or backend
suite rerun for this design review.

## Accepted limitations and open items

| Item | Owner | Disposition |
|---|---|---|
| H-02 design approval of the three compositions | Product owner and design reviewer | Approved by the product owner on 2026-10-28, with S0-V01–S0-V08 open; no category scores recorded. Checklist below |
| S0-V01–S0-V08 composition findings | Web/design owner | Open. Task 6 avoids the phone conversation blockers (S0-V01/S0-V02) and S0-V05, S0-V07 (Roles), S0-V08 in the app; the visual-corrections batch after Task 6 fixes the rest and corrects the compositions |
| H-07 domain-reviewer sign-off on the fixture hand check and financial worked examples | Domain reviewer | Sprint 0 part confirmed by the product owner on 2026-10-28 (`docs/evidence/fixture-hand-check.md`) |
| H-09 confirm or reject the Contributor test model (ADR 0003) | Product owner | Confirmed by the product owner on 2026-10-28; ADR 0003 accepted |
| Real-source corpus, 0 of 33 pages | Tasks 8, 10, 12 | Planned (`corpus/manifest.json`) |
| Task 1 carry-forward list (roles, typed DB-down failure, M4, M7, bounded stop, Contributor refusal) | Task 3 | ADR 0002 (decisions 2 and 7, "Consequences and follow-ups"), `docs/evidence/sprint-0-spike.md` ("Blocked, not run, or limited") and register DUR-02, DUR-08, ARC1-08, MODEL-02, BND1-14 |
| amd64 images (manifests only) | Task 16 | Fresh-install qualification |
| Re-estimate after Sprint 0 (plan "Delivery envelope") | Product owner or controller | Not done by the agent |
| Phone focused views, tablet layout, keyboard flows, Safari | Tasks 4, 8, 14 and humans (H-04) | Planned |

## Human design-review checklist (H-02, approved 2026-10-28 without scores)

Use `docs/design/compositions/index.html` and `docs/design/screenshots/`. Record a 1–5
score per category with concrete defects (plan section 5). The
[full checklist and agent evidence](../design/pre-review-sprint-0.md#human-review-checklist-not-run--requires-human)
are ready for the human review required by R2. Pending scores are not passes.

| Category | Score (1–5) | Defects |
|---|---|---|
| Hierarchy | Not run — requires human | Buried phone lists and competing filled actions (S0-V07/S0-V08) |
| Typography | Not run — requires human | Readable desktop text/table; small SVG labels, dense tray and zoom require review |
| Spacing | Not run — requires human | Phone input/recovery covered by the sheet (S0-V02) |
| Visual identity | Not run — requires human | Consistent surfaces, branches and selection; colour-vision/display checks remain |
| Chart legibility | Not run — requires human | Desktop chart/Gantt/ledger inspected; phone focus, tablet and dense/scenario cases absent |
| Uncertainty communication | Not run — requires human | Conditions, stale selection, unsupported match and omitted known figures (S0-V03–S0-V06) |
| Responsive composition | Not run — requires human | Hidden review entry, covered controls, unknown sheet and buried lists (S0-V01/S0-V02/S0-V06/S0-V07) |
| Interaction continuity | Not run — requires human | Phone review/input and stale context need correction; keyboard/expansion/focus checks remain |

Approval: **given by the product owner on 2026-10-28 (H-02)**. No category scores were
recorded. S0-V01–S0-V08 stay open and are assigned (see the table above).
