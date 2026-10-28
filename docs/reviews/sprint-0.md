# Sprint 0 review: resolve the expensive uncertainties

- Date: 2026-10-28. Branch `l0-local-release`.
- Reviewed revision: `943663c` plus the commit that adds this review, which changes only
  documentation. Sprint 0 commits: `e32fb12`..`2bb36e5` (Task 1: S0.1–S0.4) and
  `e925c57`..`943663c` (Task 2: S0.5, S0.6).
- Reviewer: the Task 2 implementing agent. It is not independent of the work reviewed. A
  separate reviewer is dispatched after this task, and the human gates below remain open.

## Outcome

Sprint 0 delivered its technical decisions and evidence:
- A real Meta call returns a typed result on the pinned model.
- A durable DBOS run survives worker kills without corrupting its accepted result or
  journalling a secret.
- The L0 boundary and the dependency pins are recorded.
- The supplied fixture pack is placed and independently hand-checked.
- The real-source corpus has a manifest with owners.
- Every specification requirement has a planned test and an owner.
- Three signature compositions exist in honest default, unknown-data and failure states.

**No application exists yet.** No journey can be demonstrated from a product UI, and that
is expected at this point in the plan. Human approval of the compositions and the other
human gates are **not run** (ruling R2).

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
| S0.6 requirement-to-test register | Done: 330 IDs covering all 16 M0 requirement IDs, all 14 regression families, the untagged M0 sections and 10 human gates | `docs/requirements-register.md` |

## Checks run on the final candidate

| Command | Result |
|---|---|
| `cd backend && uv sync --locked` | Audited 54 packages; lock current |
| `uv run --locked ruff format --check .` | 29 files already formatted |
| `uv run --locked ruff check .` | All checks passed |
| `uv run --locked mypy` | No issues in 29 source files |
| `uv run --locked pytest` | 63 passed, 12 deselected (integration) |
| `uv run --locked pytest -m integration spikes/durable` (Docker 29.1.2 aarch64, PostgreSQL 16.15) | 12 passed in 31.87 s; no spike container left behind |
| `uv run --locked python -I ../fixtures/m0/validate_fixtures.py` | `"status": "passed"`. The validator also rejected all 9 single-value mutations (hand check §1) |
| `cd docs/design && pnpm install --frozen-lockfile` | lockfile current |
| `pnpm run contrast` | 64 of 64 pairs pass |
| `pnpm run check-data` | 59 fixture assertions pass. Mutations of three values each failed it |
| `pnpm run screenshots` | 18 of 18 captures pass: axe 4.14.0 (WCAG 2.0, 2.1 and 2.2 A/AA), overflow, console, fonts, label collisions |

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
- Conditional readiness stays conditional.
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

**5. Is the interface coherent and polished?** There is no implemented screen to compare
yet. The references were built and iterated against their own renders. The defects found
and fixed are listed in `docs/design/pre-review-sprint-0.md`, labelled as an agent
pre-review. **Design-review scores: not run — requires human (H-02).** The checklist
follows below.

**6. What exact evidence establishes completion?** The commands and results above, on
revision `943663c`. Known gaps:
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

Building the route comparison also exposed a real error in the hand check (incomplete
dominator lists for DIRECTAI G and H). It was corrected in `f5b73d1`.

## Visual findings

From the agent pre-review, not a score:

- Strong: one structural motif across pages, one primary action per view, distinct
  failed, stale, unknown and conditional states, and readable grey layers.
- Weak:
  - The phone's focused chart and map overview are not composed.
  - The bottom sheet has no designed "peek" height.
  - SVG labels at 13 px shrink on narrower desktops.
  - The early sketch's provisional status relies on a dashed edge.
  - No scenario whiskers are demonstrated, because the fixtures carry no scenario data.

## Accepted limitations and open items

| Item | Owner | Disposition |
|---|---|---|
| H-02 design approval of the three compositions | Product owner and design reviewer | Not run — requires human. Checklist below |
| H-07 domain-reviewer sign-off on the fixture hand check and financial worked examples | Domain reviewer | Not run — requires human |
| H-09 confirm or reject the Contributor test model (ADR 0003) | Product owner | Not run — requires human. Fallback documented in ADR 0003 |
| Real-source corpus, 0 of 33 pages | Tasks 8, 10, 12 | Planned (`corpus/manifest.json`) |
| Task 1 carry-forward list (roles, typed DB-down failure, M4, M7, bounded stop, Contributor refusal) | Task 3 | `.superpowers/sdd/l0-sprint-tasks/carry-forward-task-3.md` and register DUR-02, DUR-08, ARC1-08, MODEL-02 |
| amd64 images (manifests only) | Task 16 | Fresh-install qualification |
| Re-estimate after Sprint 0 (plan "Delivery envelope") | Product owner or controller | Not done by the agent |
| Phone focused views, tablet layout, keyboard flows, Safari | Tasks 4, 8, 14 and humans (H-04) | Planned |

## Human design-review checklist (H-02, not run)

Use `docs/design/compositions/index.html` and `docs/design/screenshots/`. Record a 1–5
score per category with concrete defects (plan section 5). The full checklist, with the
questions to answer, is in `docs/design/pre-review-sprint-0.md`.

| Category | Score (1–5) | Defects |
|---|---|---|
| Hierarchy | | |
| Typography | | |
| Spacing | | |
| Visual identity | | |
| Chart legibility | | |
| Uncertainty communication | | |
| Responsive composition | | |
| Interaction continuity | | |

Approval: not given. Approver and date: blank until a human reviews.
