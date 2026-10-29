# Nessa local development plan

## From product specification to a beautiful and verifiable local app

29 October 2026 • Plan version 1.3 (1.2 and 1.1: 29 and 28 October 2026; 1.0: 27 October 2026) • Based on product specification 1.3

Build a complete career-planning experience that runs on a developer’s computer, works without credentials in a labelled synthetic demo, and uses one user-supplied Meta API key for live conversation and research. The endpoint is a tested local release candidate with inspectable evidence, reproducible route comparisons and a printable plan. Public hosting is outside this plan.

The delivery strategy is to prove the risky integration and mathematical boundaries early, establish the visual language before building the feature set, then deliver complete user journeys in small increments. Every sprint ends with a working demonstration, relevant tests and a short review of the whole system.

## Three commitments

Product integrity is structural. The language model proposes facts and interpretations; validated application commands commit them. Deterministic Python computes readiness, affordability and route rankings.

Visual quality is a delivery requirement. The conversation, opportunity map and route comparison receive explicit design reviews, responsive states and usability tests throughout development.

Local completion is measurable. A fresh checkout can start the app, exercise all five personas, use a real key, survive a worker restart and reproduce the selected plan across screen, print, JSON and ICS.

## Delivery envelope

Eleven outcome-based sprints, numbered 0–10, with Sprint 6 delivered as 6a and 6b, and an initial estimate of 39–54 engineering days (Sprint 10, added in v1.3, is 2–3 of them). For one experienced full-stack engineer using an LLM coding assistant, plan roughly 8–11 working weeks, with regular product and design input. This is a planning range, not a validated productivity forecast. Re-estimate after the technical spike and first real-source extraction work; external access and evidence review can add elapsed time.

With agent implementers, engineering days are a sizing unit, not a duration: Sprints 0–2, sized at 9–12 engineering days, took 16 hours of wall-clock time. Elapsed time is set by human review hours: the three scheduled review sessions (section 10) and the human checks of Sprints 8–9.

The earlier ten-day private-beta target is not adopted. The current instruction changes the endpoint to local operation and places a higher bar on UX. A compelling early demonstration should emerge in Sprint 1; a demonstration is not the completed product.

## How to use this plan

Scope and architecture come first, followed by the design contract, sprint roadmap, detailed sprint cards, test strategy and release checklist. Each sprint card identifies deliverables, acceptance evidence and its coherence review. Keep the source specification alongside this plan for complete domain definitions.

**Version 1.1 (28 October 2026)** applies the L0 assessment handover written after Sprints 0–2 (`docs/plan/l0-assessment-handover.md`), with its decisions D1–D3 confirmed by the product owner and recorded in ADR 0008. Human review becomes a scheduled resource with three sessions (sections 6 and 10). The required corpus becomes a reviewed England option pack (section 9). The remaining work follows the critical chain, and Sprint 6 is split into 6a and 6b (section 6). One formative comprehension session follows Sprint 5 (section 5). Adzuna stays optional (Sprint 3) and two risks are added (section 12). Sprint 2 gains the span-cited explanation the specification now permits (S2.7). Scope is otherwise unchanged: the dendrite, the three Pareto layers and the sliders all stay; only their order changes.

**Version 1.2 (29 October 2026)** applies an intermediate code review held after the Sprint 3 acquisition core (`docs/reviews/intermediate-code-review-2026-10-29.md`; ADR 0008, amendment). Scope and architecture are unchanged. Four changes:

1. A focused cancellation lock-order correction, with a concurrent regression test, runs right after the Sprint 3 backend and before the option pack (section 6).
2. Real evidence is the next proof of progress. From the option pack to review session 2, the chain (option pack → Sprint 4 backend → Sprint 5 backend → session 2) takes priority. Infrastructure polish that no failing check or reproduced defect requires is listed for the final review instead. The option pack also reports an early, unreviewed accuracy read on its development split.
3. Language rules (the support screen, explanation validation, redaction, and the pay, date and work-mode readers) grow only for a reproduced defect or an evaluation failure. A fail-safe outcome (unknown, unclear, not kept) is preferred to a new pattern. Safeguards and accepted limitations stay as recorded (section 12).
4. Review session 2 also holds Sprint 2's design review, which tests scanning, understanding and choosing. Its findings are applied before more interface detail is added (sections 6 and 10).

**Version 1.3 (29 October 2026)** adds Sprint 10 at the product owner's request: an operator's manual, written by doing every task it describes in the built product. Friction points found along the way are logged. Those a small change can smooth are fixed in the sprint. A larger refactor for user experience is put to the product owner only when there is high conviction that its benefit outweighs its cost. Nothing else changes.

# 1 The local delivery boundary

Call this milestone L0 to distinguish it from the specification’s hosted private beta, M0. Preserve M0’s business semantics and bounded model. The differences below are deliberate local adaptations, not claims that all M0 or M1 gates have been completed.

| Area | L0 decision |
|---|---|
| Geography | England, en-GB and GBP; up to three cities and three active targets. Keep country-neutral identifiers and explicit unsupported-region states. |
| Product journey | All six chapters: You, Roles, Skills, Options, Routes, Plan. Include sure and unsure entry, apply-now, conditional and unavailable outcomes. |
| Planning model | At most 24 action concepts, two reviewed starts per concept, six selected actions, 24 months and one conditional bridge-role transition. |
| Hosted infrastructure | Replace Cloud Run, GCE, Cloud SQL and Cloud Storage with local processes, PostgreSQL and private local storage. No deployment, domain, public URL or Terraform work. |
| Authentication | Firebase Authentication emulator with a demo project and seeded identities. Preserve invitation and ownership checks; real Google OAuth qualification is deferred. |
| Secrets | Local runtime master key outside the repository and database; authenticated encryption for saved user keys. No GCP Secret Manager or KMS dependency. |
| Transport | Loopback-only HTTP is an explicit development exception to hosted TLS. Reject non-local host/origin access. No LAN binding or tunnel in the delivered configuration. |
| Data credentials | A Meta key suffices for the live-assisted journey. Adzuna app ID/key enables a separately qualified live vacancy integration; it is not silently assumed to be part of the Meta key. |
| Export | Browser print CSS, JSON and ICS from one plan snapshot. No server PDF service, calendar connection or automatic external action. |
| Visual scope | Full M0 surfaces plus a narrow promotion of purposeful panel and graph-reveal transitions. Semantic zoom, mini-map, pulsing halos, generated illustrations and multiple animated journey overlays remain deferred. |

The selected stack stays React/Next.js, SVG/D3, FastAPI/Pydantic AI, DBOS and PostgreSQL. Do not introduce another solver, workflow engine, renderer, scraper vendor, vector database or general agent platform.

Local does not remove provenance, money, isolation, secret, cancellation or deletion requirements. Use synthetic personas for development and live-provider qualification. Processing real people’s information requires the specification’s applicable privacy assessment and disclosures; no claim of legal compliance follows from passing engineering tests.

# 2 Runtime modes and local startup

Record the data mode on every workspace and run. Fixtures must never fill missing live fields or appear as real evidence.

| Mode | Credentials and network | What it proves |
|---|---|---|
| Demo | No key; no outbound requests after installation and data seeding. Deterministic model and source fixtures. | Complete interaction, business rules, numerical traces, recovery and export paths. Persistent synthetic-data label. |
| Live assisted | One user Meta key; qualified Meta model/search plus permitted selected-page retrieval. Pinned public imports and user-pasted source text. | Genuine interview, grounding, extraction and planning using reviewed inputs. Vacancy coverage may be partial. |
| Live vacancy extension | Live-assisted mode plus separate Adzuna credentials and permitted account access. | Real bounded Adzuna requests, prediction flags, pagination, deduplication and freshness. Report separately if unverified. |

Provider outages preserve work and show unavailable status. Switching to a demo creates a separate workspace. Manual text import retains its own provenance.

## Local process layout

Docker Compose runs PostgreSQL 16, Firebase Auth emulator, FastAPI, DBOS, a restricted acquisition worker and Next.js. The optimiser is a cancellable child process without network access. Acquisition receives no model/master key or private profile store. Separate DBOS and application schemas/databases with scoped roles.

Bind published ports to 127.0.0.1. Route API/events through the web origin. Use named database volumes and a private evidence directory. Verify ARM64/x86 images; local startup requires no cloud account.

## Command contract to implement

| Command | Required behaviour |
|---|---|
| make setup | Check prerequisites, build locked dependencies and create local configuration/key safely. |
| make dev | Start healthy services, migrate, seed identities and report the local URL. |
| make demo | Open the fixture workspace; block outbound demo traffic. |
| make check | Formatting, lint, type checks and fast deterministic tests. |
| make acceptance | Run the full offline suite against PostgreSQL and DBOS. |
| make live-smoke | Run a budget-capped real Meta smoke; no key in command arguments. |
| make stop | Stop processes without deleting persisted work. |
| make reset-demo | Reset the named fixture workspace only. |

These commands are implementation deliverables. Installation can require network access; the seeded demo runs offline.

# 3 Architecture and clean code contract

Use a modular monolith, explicit use cases and separate workers at trust/execution boundaries. Keep core rules as small typed functions and immutable values.

## Module ownership

| Boundary | Owns | Key rule |
|---|---|---|
| Profile and exploration | Profiles, interviews, slates and targets | Model patches cannot change secrets or commitments; hard constraints need confirmation. |
| Evidence and acquisition | Source policy, claims, mappings and freshness | Failure is not an empty success. |
| Capability and catalogue | Skills, gates, offerings, funding and outcomes | Planned learning is not demonstrated skill. |
| Planning and optimisation | Schedules, ledgers, archive and layers | No network, LLM or ORM access in candidate evaluation. |
| Plan and progress | Snapshots, commitments, progress and exports | Preserve evidence and commitments when replanning. |
| Identity and execution | Consent, keys, ownership, runs and spend | Check ownership/revocation before every call. |

## Repository shape

Use apps/web and backend/src/nessa. Organise Python by domain module with clear services/adapters, without empty layer scaffolding. Separate domain, integration, acceptance, security and evaluation tests. Keep manifests, fixtures, tokens, ADRs and the runbook easy to locate.

Generate the TypeScript client from FastAPI’s OpenAPI contract; do not duplicate money/state/error enums. Pydantic validates external structure; domain functions validate meaning and cross-record rules.

## Practical SOLID rules

Give each use case one clear purpose and transaction boundary. Use descriptive functions such as confirm_profile_patch, compile_catalogue and select_plan rather than a generic manager or agent controller.

Introduce narrow ports at real I/O boundaries: model proposals, source fetching, repositories, clock and event publication. Use dependency injection at the composition root; avoid interfaces around every pure function.

Prefer composition to inheritance. A fixture adapter must satisfy the same failure and provenance contract as a live adapter, with its synthetic origin retained.

Pass explicit context instead of ambient mutable state. Include workspace ID, actor, expected version and idempotency key on consequential commands.

Keep comments for why a rule exists, particularly conservative timing, negative economic cost and rank semantics. Explain normal control flow through names and small functions.

Use uv and pnpm lockfiles, Ruff, one Python type checker, TypeScript strict mode and one established JavaScript lint/format toolchain. Pin compatible versions after the spike. Reject circular module imports and raw vendor/SQL access from domain code through automated architecture checks.

# 4 Design the experience before expanding it

The visual concept is the specification’s calm observatory: an ink-blue space for exploration, fine luminous branches, generous typography and warm light cards for reading and decisions. The spectacular moments should reveal real relationships. Small datasets, uncertainty and errors must look as considered as the ideal view.

## Signature compositions

| Surface | Intended experience | Required implementation detail |
|---|---|---|
| You | A spacious conversation beside an editable account of what is known. One useful question at a time. | Proposed changes appear in a review tray with accept, edit and undo. Show an early labelled route sketch after minimum inputs. |
| Roles | A stable map of cities, companies and opportunities, linked to a precise list and pay lens. | SVG hierarchy, curved branches, stable IDs, restrained industry colours, readable selected card and explicit coverage counts. |
| Skills | A clear picture of demonstrated, self-reported, planned and unresolved requirements. | Behavioural anchors, inspectable evidence, shared questions across targets and visibly protected gates. |
| Options | A curated comparison by gap, with enough detail to judge cost, time and evidence. | Pin/exclude controls, provider provenance, conditional funding and an explicit review checkpoint. |
| Routes | A striking but exact time–cost composition that becomes a tangible journey on selection. | Discrete schedule points, readable F1–F3, equivalent-point groups, a selected Gantt and synchronised route cards. |
| Plan | A calm, complete document with one next action and a dependable financial story. | Version and condition labels, evidence links, revision comparison, clean print hierarchy and portable downloads. |

## Design deliverables

Before feature expansion, produce three complete high-fidelity compositions: conversation with evidence drawer, opportunity map with selected role, and route comparison with selected journey. Use actual fixture numbers and realistic long labels. Include mobile variants, unknown data and one failure state for each. Preserve the designs in a versioned local design reference and implement their components in Storybook.

Use the specification’s ink #09121F, raised ink #142338, light canvas #F5F7FA and sea-glass action accent #5DE0C1 as starting tokens. Validate contrast rather than assuming these combinations pass. Choose one licensed self-hosted humanist body face and one restrained display face; record licence and files before adoption. Use tabular numerals and consistent currency/date formatting.

Define semantic tokens for surfaces, text, focus, selection, industry and status. Industry colour must never also mean success or error. Use fixed licensed icons, meaningful labels and clear hierarchy. No decorative photographic assets are necessary for L0.

On desktop, use a slim chapter rail, central work area and evidence drawer. On mobile, lead with cards and lists, with focused graph views and a bottom evidence sheet. Do not shrink the desktop graph to phone size and call it responsive.

# 5 Visual and usability acceptance

“Breathtaking” needs a review process, not a test assertion. Treat visual composition, factual clarity and interaction quality as separate gates. Passing automated checks does not establish that the experience is beautiful or understandable.

## Design review rubric

At Sprints 1, 3, 7 and 9, the product owner and a design reviewer assess hierarchy, typography, spacing, visual identity, chart legibility, uncertainty communication, responsive composition and interaction continuity. Record a 1–5 score with concrete defects; require every category to reach at least 4 before the final local release. This is a proposed internal review convention, not a validated UX measurement.

A screenshot approval covers all six chapters at 1440 × 900 and 390 × 844, plus a tablet check at 768 × 1024. Review default, selected, empty, partial, stale, unavailable and failed states for the components that support them. Test long role/provider names, three targets, negative economic cost, zero results and the 100-visible-job limit. Never approve only the attractive fixture.

## Interaction rules

Maintain one shared selection and filter contract across list, map, pay lens, scatter and Gantt. Preserve selection and scroll position when safe; explain stale or out-of-range selections.

Show progress with actual stages and counts. Do not invent percentage completion for an unbounded provider call. Keep earlier results readable during refresh, with their version and freshness visible.

Use short transitions only to explain selection, expansion or change. Proposed timings: 120–180 ms for controls, 220–320 ms for panels and up to 450 ms for a staged graph reveal. Do not run continuous force motion.

Calm mode and prefers-reduced-motion remove spatial animation without removing information. Every essential interaction must work with motion off and through a DOM list.

A conditional route, stale claim and failed request must look distinct. Grey Pareto layers remain legible; disabled low-contrast text is not an acceptable way to explain a dominated route.

## Accessibility and local performance

Target WCAG 2.2 AA. Check keyboard-only completion, visible focus, proper headings, accessible names, focus return from drawers, 200% zoom, narrow-screen reflow, contrast and error announcements. Use axe plus manual VoiceOver testing on the actual target Mac; Playwright WebKit does not replace testing Safari and assistive technology.

Set measured local budgets: immediate input feedback within 100 ms; p95 linked filtering/selection within 150 ms at 100 visible jobs and a bounded 1,000-mark route projection; no horizontal page overflow at 390 px. Report device, browser, dataset and measured percentiles. These are proposed lab budgets, not field Web Vitals or a guarantee on every laptop. The complete archive stays accessible through paginated groups; projection counts disclose hidden marks and never change ranks.

Run five short synthetic-data task sessions near Sprint 9, covering sure/unsure entry, evidence inspection, route choice and print. Aim for four of five participants to finish the core task without assistance and correctly explain cost, conditional readiness and uncertainty. Any dangerous misunderstanding is a blocker regardless of the aggregate result; this small study is formative, not statistical validation.

Hold one earlier formative comprehension session after Sprint 5, so that user contact precedes the two most expensive UI sprints. One person spends 30 minutes with synthetic data on the fixture route comparison and the TRACE-01 ledger; screenshots or Storybook are acceptable surfaces. Ask them to explain the cost shown, what “conditional readiness” means and what is uncertain. Record any dangerous misunderstanding as a Sprint 7 scope input. The product owner runs it at review session 2 (section 10). It is formative, not statistical, and leaves the five Sprint 9 sessions unchanged.

# 6 Sprint roadmap

Sprints are short, outcome-based increments rather than arbitrary two-week containers. Each starts from a usable main branch and ends with a demonstration and written evidence. Effort estimates include implementation, focused tests and the sprint review, but depend on access to the specified providers and datasets.

| Sprint | Outcome | Engineering days | Human review hours | Main dependency |
|---|---|---|---|---|
| 0 | Verify provider, durability and local constraints; freeze contracts | 2–3 | Done: approvals given 2026-10-28, not timed | Supplied specification and access checks |
| 1 | Beautiful local shell and persisted fixture journey | 3–4 | Done: approval given 2026-10-28, not timed | Sprint 0 decisions |
| 2 | Live interview and grounded career discovery | 4–5 | H-11 done 2026-10-28, not timed; H-12 in session 1 | Identity, versions, Meta contract, ESCO import |
| 3 | Reliable evidence acquisition and living opportunity map | 4–5 | About 2 (session 1, before the Roles chapter); the design review is not estimated | Source policy, taxonomy, run lifecycle |
| 4 | Skills, protected gates and evidence-based outcomes | 4–5 | H-07 in session 2 | Profile, targets and source claims |
| 5 | Reviewed options and correct monthly finances | 4–6 | About 2 (session 2, after the Sprint 5 backend) | Capability model and offerings |
| 6a | Verified enumeration and three Pareto layers on instances that complete | 5–7 for 6a and 6b together | None | Frozen planning input, financial checker and reviewed option pack |
| 6b | Durable, bounded search at full scale | (within 6a's range) | None | Sprint 6a |
| 7 | Exceptional coordinated route comparison | 4–6 | About 1 (session 3, before Sprint 7 closes) | Real solver output, design system and session 2's findings |
| 8 | Chosen plan, progress, revision and exports | 3–4 | Not estimated: Safari print (H-04) | Stable comparison and immutable snapshots |
| 9 | Local release qualification and handover | 4–6 | Not estimated: design review, VoiceOver, Safari, five task sessions (H-01, H-03–H-05) | Complete product journey |
| 10 | Operator's manual, with the friction it finds smoothed | 2–3 | Not estimated: a person follows the manual (H-14); decisions on any larger proposal | The qualified release candidate |
| Total | Local release candidate | 37–51 | About 5 scheduled, plus Sprints 8–9 | Re-estimate after Sprints 0 and 3 |

## Responsibility and sequencing

An engineering owner is accountable for each sprint, including agent-written code. The product owner decides consequential scope and acceptance questions. A design reviewer owns visual critique; a domain reviewer checks consequential requirement/outcome mappings and the financial worked examples. These roles can overlap, but the author’s confidence is not independent evidence.

Begin source curation in Sprint 0 and complete the required corpus across Sprints 3–5. In v1.1 the corpus is curated once, right after the Sprint 3 acquisition backend, as the England option pack (section 9). Begin visual design in Sprint 0 and implement the shell in Sprint 1. Do not postpone either until integration week. If the same engineer owns everything, include this work in the estimate rather than treating it as free parallel capacity.

The critical chain is validated inputs → evidence and outcomes → monthly feasibility → solver/archive → coordinated comparison → immutable exports. Visual exploration and data labelling can proceed alongside that chain with explicit contracts. An unresolved blocker affects dependent work, while independent design, fixtures and pure-domain tasks can continue.

**Order of the remaining work (v1.1).** The backend slices of Sprints 4 and 5 run before the Roles chapter UI, because in L0 the dendrite has no live vacancy data and every role is unscored: the Roles chapter is requested and stays in scope, but it does not feed the chain. After Sprint 2, work proceeds in this order:

1. Sprint 2 addition S2.7, then the Sprint 0–1 visual corrections.
2. Sprint 3 acquisition backend (S3.1–S3.4 and the reduced S3.6), then the cancellation lock-order correction (v1.2).
3. The England option pack (section 9).
4. Sprint 4 backend, then Sprint 5 backend.
5. Review session 2, then the reviewed option pack published from its record.
6. Session 2's Sprint 2 design findings applied, then Sprint 4 Skills chapter and review, then Sprint 5 Options chapter and review.
7. Sprint 3 Roles chapter (S3.5), job scoring and review, after review session 1.
8. Sprints 6a, 6b, 7 (closing after review session 3), 8, 9 and 10.

Review session 1 can be held at any point before the Roles chapter; held before the option pack is curated, it lets the pack's pages be classified against its rights policy rather than left pending human review. Each sprint's review is written when its last slice finishes, so the Sprint 3 review follows those of Sprints 4 and 5. With one implementer at a time, slices without a dependency on each other run one after the other, in either order.

**Human review sessions.** Human review is a scheduled resource, not an event between sprints. Three fixed sessions, named in section 10 with the gates each closes, are dispatch preconditions for the work after them: no dependent slice starts until its session has happened. They total about five and a half hours. The other human checks (the Sprint 3 and Sprint 9 design reviews, VoiceOver, Safari, the five Sprint 9 task sessions and the privacy decision) keep their positions in the sprint cards; none of them is a dispatch precondition.

# Sprint 0 Resolve the expensive uncertainties

2–3 engineering days • Entry: product specification 1.2 and starter kit • Requirements: BND-1, ARC-1, TEST-1, sections 16–19

## Demonstrable outcome

A minimal local technical spike proves the selected model and durable execution path. The team has a fixed L0 boundary, three signature screen compositions, an evidence backlog and a small set of architectural decisions that an LLM coder can implement without choosing a different product.

## Build and decisions

S0.1 Record the scope overrides in section 1 and a dependency matrix with exact runtime/package versions to pin. Check Docker architecture support, Python 3.12, PostgreSQL 16, the Firebase emulator and compatible Node/pnpm versions.

S0.2 With an authorised test key and cost cap, prove Standard-mode muse-spark-1.3 access, schema output, search, streaming and usage reporting through Pydantic AI’s native Meta provider. Record capabilities, model ID and observed restrictions; do not silently choose another model.

S0.3 Prove a DBOS workflow against local PostgreSQL. Kill and restart a worker, exercise an outbox replay and inspect the persisted arguments/results. Resolve how private payloads and keys are excluded from workflow journals before feature work depends on the integration.

S0.4 Confirm the durable boundary: workflows carry IDs; an authorised bounded activity resolves encrypted payloads and the credential just in time, persists validated outputs and returns references. Pin the supported Pydantic AI/DBOS composition in an ADR. Do not assume attaching a durability capability automatically satisfies privacy or recovery.

S0.5 Reconstruct P01–P05, TRACE-01 and the A–I direct-spend fixture from section 20 and section 12. The referenced Nessa_M0_Fixtures.zip was not attached. Mark these as newly reconstructed fixtures, not the original pack, and independently check their expected values.

S0.6 Create the source-corpus manifest and design references. Establish a canonical requirement-to-test register. Keep unresolved source access or reviewer needs visible.

## Exit evidence

A real call succeeds with a typed response; an invalid key fails visibly; worker recovery does not corrupt the accepted result; persisted state contains no credential. Manually checked TRACE-01 arithmetic and the five persona expectations are committed. Every unknown dependency has a named owner and disposition. If live access is blocked, the spike is explicitly blocked rather than passed.

## Coherence review

Can one confirmed profile change flow through a typed command, a durable run and a versioned result without the LLM owning a transaction? Check that the local scope still delivers the complete product journey and that the visual compositions use honest data states.

# Sprint 1 Build a polished local walking skeleton

3–4 engineering days • Entry: Sprint 0 boundary and technical decisions • Requirements: ARC-1, sections 3, 14, 16–19

## Demonstrable outcome

From a fresh checkout, start Nessa, sign in as a seeded local identity, edit a profile, inspect a fixture route and reopen the same work after restarting services. The six-chapter shell already looks like the intended product.

## Deliverables

S1.1 Implement the command contract, Compose configuration, health checks, migrations and deterministic seeding. Configure a demo Firebase project, two invited test identities and one uninvited identity. Keep emulator use explicitly local and fail closed on unsafe environment/host configuration.

S1.2 Create profile/workspace versions, expected-version writes, source references, typed error envelopes, run IDs and an outbox. Add database ownership controls using non-owner application roles, including worker access; do not rely solely on a user ID from the browser.

S1.3 Implement encrypted key storage and revoke/rotate commands. Keep the runtime master key outside git, database backups and acquisition containers, with restrictive file permissions. Add server-side budget reservation and redacted logging before live product calls expand.

S1.4 Build the chapter rail, workspace strip, evidence drawer, cards, buttons, form controls, status vocabulary and mobile layouts. Define tokens and Storybook stories for loading, empty, unknown, conditional, stale, error and disabled states.

S1.5 Connect the UI to the real local API/database. A fixture adapter supplies labelled content for the initial end-to-end shell; no component contains bespoke hard-coded financial examples. Add resumable status events and a reconnect path.

## Acceptance and tests

A fresh database migrates successfully; a populated fixture database upgrades without losing the selected snapshot. Profile updates survive reload and restart. A stale version is rejected. API, stream, cache and worker requests for another workspace fail, as do uninvited requests. Test key redaction across errors, database history and exports. Verify an unauthorised local origin cannot trigger authenticated changes.

The shell passes the first visual review on desktop and mobile. Keyboard navigation reaches every chapter and evidence drawer, with correct focus return. The fixture mode makes no external request after setup. Its route preview is clearly fixture-driven; it does not claim that the production solver has been implemented.

## Coherence review

Trace one workspace through browser, API, database, outbox and worker. Confirm every record has an owner and version; all six chapters share the same state vocabulary; and empty states explain what the user can do next. Eliminate duplicate state stores and placeholder abstractions before building features on them.

# Sprint 2 Deliver conversation and career discovery

4–5 engineering days • Entry: persisted shell, key and execution boundaries • Requirements: REC-1, DIV-1, TAX-1, sections 3–5 and 16

## Demonstrable outcome

A sure user confirms a target quickly. An unsure user describes their circumstances, reviews proposed profile changes and receives a grounded, varied slate of career hypotheses. Both can see a labelled early sketch without completing a long form.

## Deliverables

S2.1 Import the full pinned English ESCO catalogue, aliases and skill relationships with hashes, versions and attribution. Add PostgreSQL full-text retrieval and a reviewed finite English-city list. Preserve provisional internal concepts for corroborated titles outside ESCO.

S2.2 Implement the structured InterviewTurn contract, bounded validation repair, proposed patches, source message references and explicit confirmation of hard constraints. Direct editing and chat use the same application commands. Never commit partial streamed JSON.

S2.3 Support sure/unsure entry, practical/gentle/challenge preferences, pause/resume, skip/unknown and editable “What we know”. Ask one useful question at a time and reuse information already supplied.

S2.4 Retrieve a bounded multi-query pool, deduplicate concepts and greedily construct a qualified diverse slate. Keep the six-suggestion and 60–120-candidate targets soft when evidence is insufficient. Explain fit, mismatch and a small experiment; do not fabricate a match percentage.

S2.5 Show a route or requirement sketch within the proposed five-minute usability target after the minimum inputs. Generic steps remain explicitly unresolved; a sketch is never labelled feasible or Pareto-optimal.

S2.6 Add the minimal reviewed response policy for explicit acute distress and inappropriate diagnostic inference. Keep it separate from career suitability, with maintained resource references where needed.

S2.7 (added in v1.1, after the Sprint 2 review; D3) Add the model-written “Why this could suit you” that specification section 4 now permits: at most one bounded call per slate, quoting only the person's confirmed answers and the grounded occupation record, each quotation verified server-side, with one repair and then an observable invalid-output failure. The deterministic provenance stays underneath, is shown in every case and is what exports cite. Live checks use the test model on synthetic data within an explicit cap.

## Acceptance and tests

P02 completes exploration without an invented income baseline or forced personality test. Sure users bypass optional exploration. Test invalid schemas, refusals, truncation, unavailable models, budget exhaustion and stale concurrent profile writes. The old profile survives every failed proposal.

Evaluate grounded occupation IDs, citations, family/task diversity, duplicate aliases, unsupported-title rejection and irrelevant demographic counterfactuals. Use semantic expectations rather than exact prose. Test at least 30 reviewed synthetic interview/discovery cases and record failures by type. Run a budget-capped live version of representative cases; deterministic fixtures do not certify the model’s behaviour.

## Coherence review

Check the chain from user statement to proposed fact, confirmed profile, retrieval query and career suggestion. Confirm that personality preferences inform hypotheses without becoming exclusions, and that no exploratory filter has silently become a planning constraint.

# Sprint 3 Make the evidence and opportunity map real

4–5 engineering days • Entry: source policy, occupation identity and durable runs • Requirements: TAX-1, AIR-1, VIS-1, sections 5–7 and 11

## Demonstrable outcome

Research produces inspectable records and useful partial results. Jobs can be explored through a beautiful stable city/company dendrite, an accessible list and a linked pay lens, with the same selection and filters everywhere.

## Deliverables

S3.1 Implement SourceAttempt and SourceClaim records, permitted retention, field spans, hashes and distinct publication/retrieval/effective dates. Add pinned ASHE imports and reviewed UK-SOC mappings; leave unresolved crosswalks explicit.

S3.2 Implement bounded Meta search discovery and keyless Scrapling HTTP fetch/parse. Check scheme, resolved IP, redirects, content type, size and time. Parse stable structured fields first and use model extraction only where needed. Manual pasted text is a separately recorded input route.

S3.3 Implement the Adzuna adapter and fixture contract. Qualify actual requests if credentials are available; otherwise record the live integration as unverified. Preserve predicted/advertised/unknown pay and snippets versus full descriptions. Adzuna stays optional: if developer credentials are registered and stored under `NESSA_HOME` before the acquisition backend starts, S3.3 qualifies the live integration; otherwise this deliverable is unchanged. It is external data, still a local run.

S3.4 Deduplicate syndicated jobs, retain source copies, distinguish agencies from employers and count multi-city views once. Implement closure/freshness checks, favourites, cancellation and resumable incremental results.

S3.5 Build the SVG dendrite with stable anchors, company expansion, up to 100 visible job nodes and explicit aggregation counts. Add numeric salary and AI-range filters, pay lanes and a mobile-first list. Graph distance never implies commute feasibility. In v1.1, S3.5 runs after the Sprint 5 backend and after review session 1 (section 6, "Order of the remaining work"); its deliverable is unchanged.

S3.6 Import the versioned AI evidence/mapping packs and publication-state machinery. Publish only reviewed range records; otherwise show unscored. Implement lower-bound filtering and keep unscored roles visible by default in exploration. In v1.1 S3.6 delivers the assessment record model, its publication-state checks, the lower-bound filter and the unscored state, qualified with one conspicuously labelled fixture record. The pinned evidence and mapping imports stay, so exposure-only evidence can be shown with resilience unscored. The review pipeline is data entry through the record model: a record publishes only when an accountable reviewer's recorded decision passes the publication checks, and no model output can publish one. L0 publishes no reviewed real record unless an accountable reviewer exists, which specification section 5 allows (“the beta can expose unscored roles and the functioning range filter”).

## Acceptance and tests

Complete the 20-job portion of the real-source corpus, including closed jobs, missing/predicted pay, snippets, duplicate adverts, drift and hostile page instructions. In v1.1 these are the option pack's 20 job postings (section 9), run through the pipeline. Score the live path, pointed at the same provider pages, field by field against the reviewed values: correct, incorrect, missing and unsupported, with denominators. Prove that a failed fetch cannot become “no vacancies”; one ASHE snapshot cannot become a trend; and an ambiguous mapping cannot become precise city pay.

Test time-based freshness: jobs 24 hours, considered fees/intakes seven days, active funding availability 48 hours; failed refresh never extends validity. Test SSRF/redirects with a controlled server, including IPv6 and encoded addresses. Verify the fetcher has neither user secrets nor private profile access. Confirm map/list counts, deduplication, focus retention and keyboard actions agree. Run the second design review with sparse and dense data.

## Coherence review

Select a job and trace every important number to its retained evidence and date. Compare list, map, pay lens and filters. Confirm source failures reduce stated coverage, not the user’s apparent potential, and research remains private to its workspace.

# Sprint 4 Build trustworthy skills and outcome assessment

4–5 engineering days • Entry: versioned profile, targets and evidence • Requirements: MAP-1, OUT-1, RDY-1, sections 8–10

## Demonstrable outcome

The user can inspect a provisional skills matrix, answer high-value evidence questions and understand which gaps require learning, demonstration, credentials or verification. The product recognises an apply-now case and protects regulated gates.

## Deliverables

S4.1 Create versioned matrices from ESCO and up to three permitted full-text exemplars per target. Label them provisional and expose actual snippet/full-text coverage. Keep essential, preferred, disputed and unknown requirements distinct.

S4.2 Implement behaviourally anchored levels, unknown versus level 0, separate self-report/demonstration, evidence recency and confirmation. Share evidence across targets without assuming the same skill label has the same rubric or required level.

S4.3 Implement the combined question graph, gate-first ordering and decision-impact heuristic. Start with 8–12 high-value prompts, permit pause/stop and report unresolved coverage without an employability percentage.

S4.4 Implement typed, immutable protected gates for legal practice, recognition, admission and eligibility. A user may challenge evidence or change the target definition; a preference toggle cannot remove a statutory gate.

S4.5 Build OUT-1 row mappings from syllabus and assessment spans to observable tasks. Distinguish topic mentions, practice and assessed demonstration. User acceptance of a provisional mapping creates an assumption, not expert validation.

S4.6 Classify gaps and produce the abstract action graph. Implement the P05 apply-now path ahead of course recommendations. Preserve the target/matrix version on all derived results.

## Acceptance and tests

P04 cannot become ready by demoting registration; an unresolved gate and an out-of-model pathway remain distinct from ineligibility. P05 leads with meeting modelled requirements and posting checks, with no forced training.

Test that two introductory courses cannot add ordinal levels into competence, course enrolment/completion cannot overwrite current evidence, and an unsupported outcome level remains null. Evidence changes recompute only affected gaps. Changing an essential non-protected row creates a new target definition and invalidates earlier ranks.

Label the outcome fields for at least ten real course pages in the source corpus, including misleading titles and teaching without assessment. In v1.1 these are the option pack's ten course pages, labelled with the pack and reviewed at review session 2 (H-07). Review false-positive readiness mappings individually; any unsupported consequential outcome blocks publication of the affected route. Score the live path, pointed at the same course pages, field by field against the reviewed values: correct, incorrect, missing and unsupported, with denominators. Exercise direct edits and chat proposals through the same contract.

## Coherence review

Trace one missing skill from source requirement through evidence, gap, proposed course outcome and future assessment gate. Check that the current profile, planned state and UI labels never collapse into one “skill score”. Confirm shared answers reduce effort without losing context.

# Sprint 5 Compile real options into an honest monthly model

4–6 engineering days • Entry: typed gaps, protected gates, outcome records and the England option pack • Requirements: OUT-1, TIME-1, FIN-1, sections 10–12

## Demonstrable outcome

The user reviews genuine or explicitly synthetic options, pins/excludes them and sees why a route may fail workload, payment or cash constraints. A pure Python checker reproduces the worked financial trace before the optimiser is added.

## Deliverables

S5.1 Separate stable action concepts from dated offerings and intakes. Capture actual dates, timetable, fees, liabilities, prerequisites, source spans, outcomes and review status. Model apprenticeship time, wages and training once through a composite action.

S5.2 Finish the three-funding-page corpus (in v1.1, the option pack's three funding pages). Represent confirmed, potentially eligible, ineligible and insufficient-information statuses separately from actual award approval. Only confirmed support enters unconditional figures. New loans remain information; existing debt is a fixed commitment.

S5.3 Build the option-review checkpoint. Show missing critical fields, scope bounds and removed-candidate counts. Ask the user to retain variants when limits are exceeded; never truncate to the first 24 options or two intakes silently.

S5.4 Compile the immutable monthly input: touched-month activity masks, next-boundary prerequisite availability, application deadlines, maximum weekly workload envelopes, fixed-session clashes and user-confirmed net-income assumptions. Reserve commitments consistently without subtracting them twice.

S5.5 Implement separate direct-spend, income-difference and liquidity ledgers in integer GBP minor units. Distinguish direct budget, payment cap, deficit cap and reserve. Include contractual liabilities beyond the comparison horizon and a common post-readiness income scenario.

S5.6 Implement fixed base, delay, no-award and no-offer scenario evaluation. An accepted offer gate controls both experience and wages. Do not optimise adaptive policies or invent hiring probabilities.

## Acceptance and tests

Reproduce TRACE-01 exactly, including route B’s £600 direct/economic cost, £150 peak payment and £4,850 minimum prefunded lower cash bound. Confirm that the £100 opening balance, £200 day-one fee and £300 late-month pay example fails prefunding despite a positive closing balance.

Test the £1,800 initial payment against a £250 monthly cap; overlapping concentrated workload; same-month application restrictions; signed negative economic costs; grants paid directly to a provider; and remaining liabilities beyond the horizon. P03 cannot spend an unapproved grant or unaccepted offer. Missing baseline requires a question or explicit direct-spending mode, not an automatic switch.

Run the TRACE-01 checker on at least one real option set for P01's target from the option pack, with every consequential field span-cited and human-reviewed at review session 2 (H-07). Score the live path, pointed at the pack's funding and course pages, field by field against the reviewed values: correct, incorrect, missing and unsupported, with denominators. A `proposed` record stays out of any unqualified “affordable and feasible” result.

After the Sprint 5 backend, the product owner runs the formative comprehension session (section 5) at review session 2: one person, 30 minutes, synthetic data, on the fixture route comparison and the TRACE-01 ledger, asked to explain the cost shown, what “conditional readiness” means and what is uncertain. Any dangerous misunderstanding is recorded as a Sprint 7 scope input.

## Coherence review

Read one route as both a user story and a ledger. Every payment, receipt, time commitment and outcome must have one source and one place in the model. Confirm that conservative model rejection is not described as real-world impossibility.

# Sprint 6a Prove the optimiser and layers on instances that complete

5–7 engineering days for 6a and 6b together • Entry: frozen input compiler, tested feasibility rules and the option pack reviewed at review session 2 • Requirements: OPT-1, ROU-1, FIN-1, RDY-1, TEST-1

Sprint 6 is split in v1.1. At two starts per concept, the selection bound alone permits 10,161,633 combinations before feasibility pruning, so at full scale the 1,000,000-state cap cannot exhaust the space unless sound pruning removes most of it: `budget_truncated` is the expected coverage for large catalogues (specification section 12). Sprint 6a proves the core on instances that complete; Sprint 6b then builds the apparatus for those that do not.

## Demonstrable outcome

A deterministic Python search returns independently checked routes and correctly computed F1–F3, with truthful coverage, on TRACE-01, the A–I fixture and instances built from the option pack. The same tiny instance can be verified by an intentionally simpler implementation. The sprint reports the measured instance sizes at which complete coverage is reached.

## Deliverables

S6.1 Implement canonical DFS over skip or one reviewed offering per concept, with at most six selected actions. Preserve action DAGs and dates without enumerating equivalent permutations. Check all mandatory gates, timetable, cash and workload rules.

S6.2 Start with only plainly sound pruning. Document each pruning proof and its assumptions. Do not prune on first-front dominance, current readiness or accumulated economic cost where future income/funding can change the result.

S6.5 Keep every distinct feasible schedule encountered, including dominated schedules, and compute layers over that full encountered archive by simple iterative nondominated peeling, then group families for presentation. Equal coordinates do not dominate one another; preserve distinct alternatives behind grouped points.

S6.6 Build an independent Cartesian-product oracle for tiny instances and an independently expressed route checker. They must not reuse the candidate feasibility or Pareto implementation they are checking.

S6.7 Record search coverage: `complete` only after exhausting the declared finite tree with sound pruning, otherwise `budget_truncated`, never infeasible. For growing pack-scale instances (concepts, starts per concept, months), measure the expanded states and time that complete coverage needs with the implemented pruning, and report the largest sizes that complete within the M0 limits.

## Acceptance and tests

Compare feasible schedule sets, objectives and layers against the oracle across hand-worked and generated instances. Test the three-dominator counterexample, exact ties, multiple intakes, parallel prerequisites, zero-action readiness and economic-cost supersets.

Reach complete coverage on TRACE-01, the A–I fixture and the pack-scale instances. The sprint report states the measured instance sizes at which complete coverage is reached with the implemented sound pruning, with their expanded-state counts and times; a measurement run stopped before completion is reported as not complete at that size, never as infeasible. Explain observed bottlenecks and user-selectable relaxations; claim a minimal conflict only when proved. A complete empty archive means no route within this bounded model. A complete run on the same immutable input reproduces the same result. Profile/input changes cannot alter the snapshot being solved.

## Coherence review

Compare the input assumptions, candidate checker, archived route, rank and displayed explanation for the same schedule. Check that the measured coverage sizes and the narrowings they suggest are stated where Sprint 7 can show them.

# Sprint 6b Make the search durable and bounded at full scale

Within Sprint 6a's 5–7 engineering days • Entry: Sprint 6a's checked enumerator, oracle and layers • Requirements: OPT-1, ROU-1, TEST-1

## Demonstrable outcome

A full-scale search runs durably in a cancellable child process, stops at its limits with exact reasons, keeps every encountered feasible schedule on disk and ranks a 50,000-point archive within its own observable stage. A truncated result presents itself as the normal case.

## Deliverables

S6.3 Persist every distinct feasible schedule encountered, including dominated schedules, to a versioned disk-backed archive. Use atomic archive checkpoints and an idempotent solve identity. A recovered attempt either resumes a proven checkpoint or restarts under a new attempt ID; never merges inconsistent prefixes into a completeness claim.

S6.4 Enforce 30 seconds, 1,000,000 expanded states and 50,000 feasible schedules per target. Include archive persistence in the search budget and preserve every acknowledged feasible record. A cap stops with a reason; a crash is failed. A truncated result leads with “Best trade-offs found”, states the instance size and names the narrowing (fewer concepts, one start, a shorter horizon) that would let the search complete.

S6.8 Add an efficient two-objective rank algorithm, qualified against Sprint 6a's iterative peeling on the same archives. Rank calculation has its own observable stage and must finish before results claim ranked completion.

## Acceptance and tests

Test archive truncation, each cap's exact stop reason and the retention of every acknowledged feasible record, and resumption or restart after an injected crash. Inject cancellation and child-process failure. A truncated empty archive means none found before the limit. State-limited replay is deterministic; wall-time-limited prefixes need not match. Profile/input changes cannot alter an in-flight snapshot. Benchmark 50,000-point ranking separately; avoid an unqualified quadratic implementation at this limit. On every instance that completes, the disk-backed archive and the efficient ranks equal Sprint 6a's encountered archive and peeled layers.

## Coherence review

At two starts per concept, the selection bound alone permits 10,161,633 combinations before feasibility pruning; the resource budget cannot be treated as a completeness guarantee. Check that a full-scale truncated run reports itself as the expected case, with its instance size and the narrowing to try, and never as infeasible. The Sprint 6 review record covers 6a and 6b.

# Sprint 7 Make route comparison the signature experience

4–6 engineering days • Entry: real solver output, approved design compositions and the findings of review session 2; closes only after review session 3 • Requirements: VIS-2, ROU-1, AIR-1, sections 13–14

## Demonstrable outcome

The user understands the actual trade-off, selects a route and sees a coherent journey with costs, work, study and gates. The experience feels exceptionally polished with motion on or off, without suggesting fictional options or certainty.

## Deliverables

S7.1 Build the per-target time–cost scatter using discrete schedules. Show the chosen cost definition, baseline, horizon, currency, catalogue bounds and coverage near the chart. Treat truncated coverage as the normal state: lead with “Best trade-offs found”, state the instance size and name the narrowing that would let the search complete. Group equivalent objective points without losing alternatives.

S7.2 Keep F1–F3 visible with readable styling, family grouping and named dominance explanations. Choose comparators through one documented deterministic rule and allow inspection of others. Display failed or unknown stress scenarios separately; do not give them invented finite time/cost points.

S7.3 Implement exact numeric inputs and keyboard sliders for time/cost. View filtering preserves ranks. Explicit reranking uses the eligible retained archive; changing planning constraints creates a new solve version. A hidden dominator does not make a route globally optimal.

S7.4 Connect selection to a static Gantt, step cards, monthly financial table and evidence drawer. Use overlapping bands for parallel work/study, clear waits and conditional gates, and actual dates alongside model months.

S7.5 Add the agreed purposeful transitions, reduced-motion/calm mode, persistent target-specific controls and pinned out-of-range states. Preserve the inspected route while recalculating.

S7.6 Use paginated archive queries and a bounded projection for large results. Disclose shown/total counts, preserve extremes and selected points, and provide access to every retained schedule. Do not relabel a sampled plot as the full frontier.

## Acceptance and tests

TRACE-01 shows A/B/C in F1, D in F2 and E in F3. The separate A–I fixture uses direct-spending labels. Equal-point alternatives, negative cost, one route, apply-now, no routes and truncated search all render correctly.

Property and browser tests prove selection/filter consistency across charts, cards, list and Gantt. Test keyboard control, focus after filtering, target switching and stale results. Verify no smooth interpolated curve implies attainable intermediate plans. Unknown scenario evidence cannot become zero-width uncertainty.

Run the third visual review and measure the local interaction budgets. Its human part is review session 3, held against what review session 2 showed; Sprint 7 closes only after it. Capture desktop/mobile screenshots with realistic names and actual solver records. A visual regression change requires inspection and an explanation; blanket baseline updates are not acceptance.

## Coherence review

Ask a reviewer to explain why two routes differ, which cost is being plotted, what is conditional and whether the search was complete. Any mismatch between that explanation and the stored model is a product defect, even if every chart renders correctly.

# Sprint 8 Turn a selected route into a durable plan

3–4 engineering days • Entry: complete comparison and plan snapshot contract • Requirements: sections 11 and 15, FIN-1, AIR-1

## Demonstrable outcome

A user confirms consequential assumptions, saves a plan, records progress and exports the exact same version. A changed price or intake produces an inspectable revision instead of rewriting history.

## Deliverables

S8.1 Create immutable PlanVersion records containing target/matrix, selected route, profile, evidence, scenario, model, assessment and source versions. Store confirmations and commitments explicitly. Choosing a plan does not enrol, apply or resign.

S8.2 Build the overview, one-next-action card, progress bands and rest/reschedule controls. Separate planning progress, evidence gained and real-world activity. Marking a task complete cannot automatically award a skill or credential.

S8.3 Add dependency invalidation and proposed plan updates for changed fees, intakes, requirements and resilience assessments. Show old/new differences and preserve the old selected plan until the user accepts a revision.

S8.4 Replan the remaining horizon using completed evidence, paid/sunk costs and remaining contractual commitments. Keep original and revised accounting bases explicit; do not compare their economic totals as if they shared one baseline/window.

S8.5 Generate browser print, JSON and ICS from a shared serialisable snapshot. Include direct/economic costs, baseline/horizon, monthly payments, cash reserve, conditional gates, actual dates, model bounds, search coverage stated as in S7.1, source register with the option pack's date and review states, and assessment dates. Let users omit sensitive notes and financial detail.

S8.6 Define ICS date/time semantics, stable UID and revision sequence. Conditional events are labelled proposed; downloads never create external calendar entries. Use safe encoding for content and links.

## Acceptance and tests

Choose TRACE-01 route B and assert that screen, print and JSON agree on the exact numeric fields and snapshot ID. Parse ICS with an independent library to verify dates, timezones, inclusive/exclusive end-date semantics and identity. Check a UK daylight-saving boundary and all-day dates.

Inspect printed output in Chromium and Safari with long step descriptions, monochrome output and page breaks. No clipped tables, split essential conditions or secret material. Verify that reloading a saved plan works with the provider unavailable, a revoked key or no network after setup.

Simulate a closed intake, changed fee and newly demonstrated skill. The old version remains readable, the affected future actions are identified, and replanning neither repeats completed learning nor erases obligations. Test workspace deletion across plan snapshots, exports, cache and workflow references.

## Coherence review

Open the chosen version in all four representations and compare its facts. Confirm that progress, finance and replanning agree about what has already happened, what is still conditional and what money is irrecoverably committed.

# Sprint 9 Qualify and hand over the local release

4–6 engineering days • Entry: complete six-chapter application • Requirements: TEST-1, all L0 requirements and critical invariants

## Demonstrable outcome

A clean machine or equivalent clean user environment can run and test Nessa using the documented commands. Both the offline demo and a budget-capped live Meta journey pass, and the release report states exactly what was verified.

## Deliverables

S9.1 Run P01–P05 end to end through the actual browser, API, PostgreSQL, DBOS and solver. Confirm all negative and conditional paths as well as the selected-route print flow.

S9.2 Run a real Meta journey with a synthetic persona and reviewed permitted evidence: interview, grounded discovery, extraction, checkpoint, solve, selection and export. Disconnect/reconnect the browser and restart the worker during the run. An unavailable integration is blocked, not passed by substituting a fixture.

S9.3 Exercise invalid/rotated/revoked keys, concurrent spend reservations, provider timeout/rate limit/refusal, cancellation, source drift, stale writes and injected process crashes. Inspect logs and durable storage for leaks. Record ambiguous external-call charges honestly.

S9.4 Test a fresh install and a migration from the last release candidate. Perform a PostgreSQL and permitted-blob backup/restore, with key material handled separately. Demonstrate full workspace deletion and explain that backup copies follow the documented local retention/reset procedure.

S9.5 Finish the visual and accessibility review, real Safari/Chrome checks, VoiceOver walkthrough and five formative task sessions. Fix consequential comprehension, keyboard, contrast, responsive and print defects before sign-off.

S9.6 Package the repository, lockfiles, source/fixture manifests, licence notices, architecture decisions, test commands, troubleshooting runbook and release evidence. Document optional Adzuna qualification separately. Tag the tested local release; do not publish a service.

## Release blockers

Any false affordability/readiness claim, cross-workspace exposure, secret leak, silently changed objective, wrong layer, unsupported evidence assertion, masked failure, corrupt restart, broken essential keyboard flow or clipped essential print content blocks release. A core workflow requiring undocumented manual database edits also blocks release.

The final command report must distinguish passed, failed, blocked and not run. The local release is not fully accepted if the real-provider smoke is blocked; the fixture build can still be delivered with that explicit limitation. No production security, multi-country, employment-outcome or public-hosting claim is made.

## Coherence review

A fresh reviewer completes the golden journey from a blank workspace and then deliberately changes an assumption. Check the entire system’s explanation, state transitions and exports against the canonical contracts. Close the sprint only after the findings are resolved or accurately recorded as non-blocking limitations.

# Sprint 10 Write the operator's manual and smooth the friction it finds

2–3 engineering days • Entry: the qualified local release candidate (Sprint 9) • Requirements: BND-1 (local operation), section 5 (usability acceptance), ARC-1 (keys, spend, recovery and deletion as the operator meets them)

The operator is the person who runs Nessa on their own computer. They install it, enter their own key, use it, and keep it working. They need not be a developer. The developer runbook (`docs/runbook.md`) stays as it is; the manual is the operator's version.

## Demonstrable outcome

A person who did not build Nessa can install, start, use, maintain and recover it with the manual alone. Every friction point the manual's writing found is fixed, proposed or recorded, with its reason.

## Deliverables

S10.1 Write the manual (`docs/manual/`) in plain English, with numbered steps and synthetic-data screenshots at desktop and 390 px. It covers:
- getting started: prerequisites, setup, the first run, and demo versus live mode;
- keys and spending: entering, rotating and revoking a key, spend limits, what costs money, and the estimates shown before work starts;
- each chapter (You, Roles, Skills, Options, Routes, Plan): what it shows, and what its states and labels mean (unknown, proposed, unscored, truncated, couldn't read versus none found);
- evidence and sources: what is fetched, what is kept and why, and Adzuna;
- exports and printing;
- maintenance: stop, reset, backup and restore, deletion, and updating to a new version;
- troubleshooting: every error message's words, what it means and what to do;
- privacy and known limits, in plain words.

Every command and on-screen word in the manual is the build's own.

S10.2 Write the manual by doing. Follow every procedure from a fresh checkout and a blank workspace, in a real browser, in demo mode and in a capped live mode (test model, synthetic persona; R5). Log each friction point in `docs/reviews/sprint-10-friction-log.md`. A friction point is any place where an operator would hesitate, misread, repeat a step, need a step the product does not tell them, or meet a message that does not say what to do. Record its steps, its evidence (a screenshot or command output), its severity (blocks, slows or annoys) and its disposition.

S10.3 Fix in the sprint any friction point that a small change smooths: wording, labels, an error message's words, a default, an order, focus, a missing link, or a command's output. A small change alters no API contract, schema, migration, workflow step sequence, deterministic computation or verified requirement's behaviour. Each fix has a test or an updated capture, and the manual describes the fixed behaviour.

S10.4 Put a larger refactor for user experience to the product owner only with high conviction that its benefit outweighs its cost. The proposal states:
- whom it affects and how often;
- the steps, errors or confusion it removes;
- the change, with its risk and effort;
- what the manual says until it is done.

Nothing larger is built in this sprint without the product owner's decision; an approved proposal becomes its own task. A point without that conviction stays in the friction log as known friction, with the manual's workaround.

S10.5 Re-qualify the changed candidate. Re-run the fast and full acceptance checks and Sprint 9's automatable checks on the final commit, and add a manual-and-friction addendum to the release report. Tag a new candidate only with the product owner's approval.

## Acceptance and tests

A docs check in the fast checks fails when:
- a command the manual names is not in the command contract;
- an error code in the UI vocabulary is missing from the troubleshooting chapter;
- a screenshot the manual uses is missing.

Every friction point has a disposition: fixed, proposed or known. Every fix has its test. The fast and full checks pass on the final commit. A person following the manual from a fresh checkout to a printed plan (H-14) is prepared as a checklist and recorded "not run — requires human" until a person records it.

## Coherence review

A fresh reviewer follows only the manual, from a fresh checkout to a printed plan. Where they had to guess, the manual or the product is wrong. Close the sprint when every guess is fixed in one or the other, or is recorded as known friction.

# 7 Testing that can expose real mistakes

Test contracts and invariants, not coverage percentages or implementation-shaped assertions. Prefer independent oracles, hand-worked ledgers and focused regression examples.

| Layer | Scope and tools | Completion evidence |
|---|---|---|
| Domain | pytest; Hypothesis for money, dates, gates, identity, state transitions and ordering properties | Hand-worked cases plus generated boundary cases. Critical rules each have explicit test IDs. |
| Algorithm | Independent Cartesian oracle, independent route checker and simple front peeling | Exact feasible-set and rank agreement on small complete cases, including meaningful known-bad variants. |
| Persistence | Real PostgreSQL, SQLAlchemy/Alembic, DBOS and outbox | Transaction rollback, concurrent writes, restart, migrations, isolation and archive integrity. SQLite is not a substitute. |
| Adapter | Recorded permitted inputs plus deterministic failure servers | Source parsing, schema validation, retries, redaction, usage and error classification. |
| API | FastAPI contract tests and generated-client compile checks | Ownership, validation, optimistic concurrency, pagination and stable error envelopes. |
| UI | Vitest and Testing Library for stateful components; Playwright for journeys | Selection/filter consistency, asynchronous states, navigation, keyboard and export behaviour. |
| Accessibility | axe, manual keyboard, contrast and VoiceOver | No unresolved critical failures; manual task completion and focus behaviour recorded. |
| Visual | Storybook states and Playwright screenshots on a pinned environment | Human-approved baselines, no unexplained diffs, responsive and print inspection. |
| Model quality | Versioned prompts, reviewed cases and explicit live eval command | Schema, grounding, constraint preservation, outcome precision and useful suggestions; no exact-prose assertions. |
| Security and recovery | Hostile fixtures, controlled HTTP server, process kills and two workspaces | SSRF, injection, revocation, spend, duplicate delivery, deletion and restoration evidence. |

## Feedback cadence

Fast checks should target a two-minute local budget on the recorded development machine; use measurements to tune the split. The full offline acceptance command runs the actual stack and must remain deterministic with fixed fixtures, clocks and seeds. Real-provider evaluations are explicit, budget-capped and outside the default offline command. Do not run a full browser suite after every edit.

Format before verification. CI, if a remote repository is used, executes the same acceptance command against the submitted revision. A test that could not start, collected no required cases, or passed before the last relevant edit is not evidence for completion. Never soften assertions simply to get a green result.

Use stateful tests for confirmation, runs and plan revision. Inject failures around outbox dispatch, remote acknowledgement, archive persistence and cancelled publication. Domain records must not duplicate; remote billing can remain ambiguous.

# 8 Numerical and state regression register

Map these minimum cases to requirement IDs and independent expected values. Namespace the two route fixtures separately.

| Test family | Required assertions |
|---|---|
| TRACE01 | A/B/C are F1; D is F2; E is F3 in economic mode. B: 4 months, £600 direct/economic, £150 peak payment, £4,850 prefunded lower bound. Six-month horizon. |
| DIRECTAI | A/B/C, D/E/F, G/H/I form F1, F2, F3 respectively in direct-spending mode. Do not reuse TRACE01 IDs or objective labels. |
| PREFUND | £100 opening, £200 immediate fee, £300 late pay fails. A positive month-end balance does not rescue it. |
| PAYCAP | £2,400 total with £1,800 immediately fails a £250 payment ceiling even with a £3,000 direct budget. |
| TIME | Touched months reserved; prerequisite usable only after its completion boundary; same-month application restricted; original dates preserved. |
| WORKLOAD | Summed maximum weekly loads compared with minimum available hours; explicit session clash rejected; unknown timetable requires review. |
| ECON | One common horizon/baseline; net income counted once; negative economic cost supported; post-horizon liabilities retained; no invented target wage. |
| FUNDING | Potential eligibility is not an award; uncertain grants/wages cannot fund earlier payments; provider-paid grant not counted twice; new debt not optimised. |
| READINESS | All essential evidence and protected gates required; planned outcomes conditional; unknown distinct from level 0; apply-now permits zero selected training. |
| PARETO | (1,3), (2,2), (3,1) all dominate (4,4), which is F2. Equal objective pairs do not dominate one another. No cross-target dominance. |
| FAMILY | Different schedules can have different ranks within one family. Grouping, pagination and display filters cannot change the archive or proof scope. |
| LIMITS | State/time/archive caps retain encountered records and exact stop reason. Failed/cancelled/invalid runs do not become successful empty or complete runs. |
| VERSIONS | Confirmed edits create new input versions. Old plans immutable. Stale workers cannot overwrite newer profile/catalogue versions. |
| AI_RANGE | [5,8] fails minimum 6 under lower-bound filtering. Unknown included in exploration by default; strict planning threshold needs explicit scope. |

## Properties worth generating

For complete searches, input permutation preserves feasible sets/ranks. Duplicate source copies preserve canonical job counts. Relaxing a resource bound preserves feasibility in the mathematical model.

Truncated searches can discover different prefixes. Adding options can change ranks. Do not encode false monotonicity claims.

# 9 Evidence and model qualification

Correct algorithms cannot rescue unsupported course outcomes. Assign owners, reviewed labels and release evidence to source curation and model evaluation.

## Required corpus

Curate 20 real full job postings, 10 course pages and three funding pages. Record permitted retention/references, URLs, rights, dates, hashes, labelled spans and missingness. A manifest, synthetic personas or generated HTML does not satisfy this corpus.

Split cases by source/template family so near-duplicate pages do not leak into both tuning and holdout evaluation. Because 33 pages is small, report raw counts and per-field failures rather than claiming representative production accuracy. Include schema drift, closed vacancies, predicted salaries, snippets, disputed mappings, missing fees, teaching without assessment and conditional grants. Refresh or replace inaccessible cases with a documented reason.

## The England option pack (v1.1, D1)

Choose the 20 job postings, 10 course pages and three funding pages for the five personas' targets (P01–P05), still covering the case types above, and deliver the labelled result as a **reviewed, versioned, dated England option pack**. Its records take the specification section 18 shapes: LearningOption and Offering, FundingInstrument, SkillRequirement rows and `PlanAction.outcomes` (OUT-1), each with its SourceClaims, rights status, `review_state` and dates. Every record starts `proposed`. After the human review at review session 2 (H-07), a new dated pack version is published from the reviewer's record: accepted records carry `review_state: reviewed`, rejected ones are left out, every corrected value is span-cited, and undecided records stay `proposed`. The later sprints score and solve against that reviewed version.

The pack is an immutable public evidence pack (specification section 11): fetched and hash-checked like ESCO (ruling R7), or committed if it is small and its rights permit under the session 1 policy. Its labelling rules:

- Every surface that uses it shows its date and each record's review state.
- A pack record never fills a live field and is never shown as current.
- Synthetic data stays labelled synthetic and never enters the pack.

Live research (Meta search, Scrapling, Adzuna) writes to the same catalogue contract, inside its own workspace and never into the pack, with `review_state: proposed`. Proposed records are explorable but excluded from an unqualified “affordable and feasible” recommendation until reviewed, which is the option review checkpoint rule (specification section 10). The pack gives the numerical core real, reviewed options to run on before Sprint 9, and gives the live path reviewed values to be scored against.

## Evaluation outputs

| Task | Measure | Blocking examples |
|---|---|---|
| Extraction | Correct, incorrect, missing and unsupported critical fields by source class; precision and recall with denominators | Wrong fee, deadline, award status or salary basis accepted as verified. |
| Live versus reviewed | The live path, pointed at the option pack's provider pages, scored field by field against the reviewed values: correct, incorrect, missing and unsupported, with denominators, by source class (Sprints 3–5) | A live value that disagrees with the reviewed one accepted as verified, or a missing field counted as correct. |
| Grounding | Claim-to-span validity and exact supporting context | Citation points to an unrelated statement, fabricated provider or invented source. |
| Interview | Valid patch rate, constraint preservation and unsupported inference count | Quietly changes a budget, invents baseline income or infers a diagnosis. |
| Outcomes | Task/assessment alignment and conditional-versus-evidenced state | Topic mention published as demonstrated competence or statutory credential. |
| Discovery | Grounded relevance, family/task coverage, alias duplication and useful novelty | Implausible filler to meet a diversity quota or unsupported demographic exclusion. |
| Safety and integrity | Resistance to hostile page instructions; correct error/status output | Page text gains tool authority, requests secrets or changes a plan. |

Compare discovery with a relevance-only slate and a common-careers baseline on the same eligible pool. Review sensitive counterfactual cases while preserving legitimate work-rights and accommodation inputs. Use people to judge plausibility and usefulness; deterministic checks should own IDs, sources and constraints. A second LLM rating is not independent truth.

## Acceptance policy

Fix or quarantine consequential false positives before route use. Report recall, coverage and task completion alongside precision. Evaluate the release holdout without rewriting failed expectations.

Record model/prompt/schema/data/parser versions, retries, costs and outcomes. Repeat critical live cases within the spend cap to expose instability. Qualification covers only the tested version and scope.

# 10 The sprint completion and coherence procedure

Reserve 20–30 minutes after each sprint for a whole-system review. This is a lightweight integration checkpoint, not a second implementation project. Keep the same six questions and add the sprint-specific question from its card.

1. Does the user journey still make sense from entry to the latest working outcome? Demonstrate it from the UI, including a relevant missing-data or failure path.

2. Do shared concepts mean the same thing everywhere? Check unknown, conditional, stale, complete, ready, direct cost, economic cost and search coverage.

3. Can a consequential displayed claim be traced to its source, version, user confirmation and calculation? Verify one example end to end.

4. Are the module and process boundaries intact? Look for new vendor logic in the domain, duplicate calculations, hidden fallbacks and unnecessary abstraction.

5. Does the interface remain coherent and polished? Compare the implemented screen with the design reference, inspect responsive behaviour and test keyboard focus.

6. What exact evidence establishes completion? Identify commands actually run on the final candidate, results, known gaps and the next dependent milestone.

Store a short record in docs/reviews/sprint-N.md: demonstrated journey, current revision, checks/results, visual findings, cross-module issues and accepted limitations. Fix critical incoherence before dependent work continues. Aesthetic details can be scheduled only if they do not compound into a different interaction model.

## Human review sessions (v1.1)

Human review is scheduled as three fixed sessions, about five and a half hours in all. Each is a dispatch precondition for the work after it: an agent prepares the session's package (checklists, captures, the records to review), a person holds the session, and dependent work starts only after it has happened. If it has not, the work is recorded as “blocked: awaiting session N”, never started or self-certified. The product owner confirmed D1–D3 on 28 October 2026, so no session needs time for them.

| Session | When | Gates it closes | Precondition for |
|---|---|---|---|
| 1, about 2 hours | Before the Sprint 3 Roles chapter (S3.5) and before any page body is retained beyond the source classes it permits | H-06 as a rights policy for the permitted source classes of the corpus and the option pack, so agents can then classify pages themselves (a page outside those classes stays with a person); the H-12 checklist in ADR 0007 | The Roles chapter and job corpus; retaining or committing page bodies beyond ruling R3 |
| 2, about 2½ hours | After the Sprint 5 backend | H-07 for Sprints 4 and 5, on the option pack and the TRACE-01 checker run on P01's real option set; the formative comprehension session (section 5, H-13); H-01 for Sprint 2, the design review of the You chapter and the slate at desktop and 390 px, testing scanning, understanding and choosing (v1.2) | Publishing the reviewed option pack, and through it Sprint 6a and the Skills, Options and Roles chapters' scoring against reviewed values; more interface detail in those chapters, which first applies the Sprint 2 design findings; the start of Sprint 7 |
| 3, about 1 hour | Before Sprint 7 closes | H-01 for Sprint 7, the design review, against what session 2 showed | Closing Sprint 7, and so Sprint 8 |

## Use the supplied Claude Code starter kit

Adopt the concise CLAUDE.md contract and replace every placeholder with the actual setup, fast-check and full-acceptance commands. Add only repository facts that change implementation decisions: typed proposal boundaries, money/time invariants, search coverage, module dependencies and the location of representative code. Do not paste the full specification into startup instructions.

The archive contains hook designs, not an installed quality.py dispatcher. Start with explicit verification commands. Implement a formatter hook only if formatting has no other reliable owner. Add a bounded completion hook only after its behaviour is tested; preserve passed, failed, blocked and stale outcomes. Do not add a digest/receipt cache until measured repeated checking justifies it.

Use selective independent review for money, authorisation, data contracts, concurrency, migrations and solver changes. Give the reviewer the contract, patch, surrounding interfaces and executed checks, without a persuasive implementation narrative. Request reproducible defects and missing behaviour, not a target number of findings. A human or separate review session can provide this role; no always-on multi-agent orchestration is needed.

## Reusable implementation instruction

Implement the named sprint’s current slice against its requirement IDs and acceptance tests. Inspect the existing system first. Resolve ordinary implementation choices simply; ask when ambiguity changes behaviour, scope or acceptance. Keep the change coherent, verify the final candidate and report implemented behaviour, checks actually run and remaining gaps. Do not suppress failures, replace agreed providers or broaden scope to make a result look complete.

# 11 Traceability and final release evidence

Link this living checklist to code, tests, demonstrations or scope exclusions. Plan headings are not implementation evidence.

| Specification area | Primary sprints | Required evidence |
|---|---|---|
| BND-1 and local overrides | 0, 1, 9 | L0 scope ADR, startup/run modes, no public deployment dependency |
| REC-1 and DIV-1 | 2 | Sure/unsure flows, grounded slates, diversity/counterfactual eval, span-cited explanations with verified quotations (S2.7) |
| TAX-1 and AIR-1 | 2, 3, 7 | Pinned imports/mappings, reviewed/null range records, filter semantics |
| Acquisition and source rights | 0, 3–5 | Source manifest, real corpus, hostile-input and access-policy tests |
| England option pack (D1) | 3–5, 6a | Pack manifest with dates, review states and rights; the session 1 rights policy and the session 2 review (H-06, H-07); live-versus-reviewed field scores; the TRACE-01 checker on P01's real option set; complete coverage on pack-scale instances |
| MAP-1, OUT-1 and RDY-1 | 4, 5 | Provisional matrix, inspectable spans, protected gates and apply-now |
| TIME-1 and FIN-1 | 5, 6a, 8 | Independent ledger checks, conservative timing, export agreement |
| OPT-1 and ROU-1 | 6a, 6b, 7 | Oracle agreement, full encountered archive, exact/truncated labels, measured complete-coverage sizes, truncation shown as the expected case |
| VIS-1 and VIS-2 | 1, 3, 7, 9 | Approved compositions, coordinated state, keyboard and performance |
| Evidence lifecycle and chosen plan | 3, 8, 9 | Invalidation, immutable snapshots, replan and offline export |
| ARC-1 and secret/privacy controls | 0, 1, 9 | Ownership, journals, spend, revocation, recovery, deletion and restore |
| TEST-1 | All, final gate 9 | Five browser personas, two numeric fixtures and real Meta smoke |
| Operator's manual (v1.3) | 10 | The manual, the friction log with every disposition, a test per small fix, proposals with their decisions, and the H-14 record |

## Final reviewer demonstration

From clean setup, demonstrate P01’s ledger, P02’s unknown baseline, P03’s payment/funding problem, P04’s protected gate and P05’s apply-now result. Inspect desktop/mobile surfaces and verify print/JSON/ICS.

Use a real Meta key and capped budget with synthetic personal inputs and permitted evidence. Reconnect/restart mid-flow; revoke the key and verify future calls stop. Editing/saved plans remain usable. Show stale-source, truncated-search and complete-empty outcomes separately.

## Release record

Record revision, dependency/model versions, device/browser, data hashes, commands/results, screenshots, numerical checks, live usage and gaps. State Adzuna qualification separately. Include quickstart, troubleshooting and reset/backup/restore instructions.

Defer hosted Google sign-in, cloud infrastructure/TLS/secrets and deployed smoke tests. M1 retains global qualification, larger studies, advanced visuals, images, borrowing optimisation, shared research and tagged PDFs. None is claimed by L0.

# 12 Implementation references and risk register

The product specification 1.3 is the domain authority, with the local overrides in this plan. The supplied Claude Code starter kit contributes the concise repository contract, observable failure rules and selective-review workflow. No application code or live-key test has been executed as part of preparing this development plan.

## Official documentation checked for this plan

1. Meta model catalogue: https://dev.meta.ai/docs/models . The catalogue lists muse-spark-1.3 and its capabilities. Sprint 0 must still prove access with the actual account/key and pin the tested release. Do not assume entitlement from a public listing.

2. Pydantic AI Meta integration: https://pydantic.dev/docs/ai/models/meta/ . The current documentation describes the native Meta provider, search and tool-choice restrictions. Verify schema mode and streaming on the chosen package/model combination.

3. Pydantic AI DBOS integration: https://pydantic.dev/docs/ai/capabilities/durable_execution/dbos/ . The current capability-based integration requires an explicit workflow wrapper; the older DBOSAgent wrapper is deprecated. Test the chosen composition’s journalling and recovery rather than copying an outdated constructor.

4. Firebase Auth emulator: https://firebase.google.com/docs/emulator-suite/connect_auth . It supports local auth testing and issues unsigned emulator tokens. Emulator acceptance must remain confined to the explicit local configuration; it is not proof of production identity security.

References checked on 27 October 2026. These narrow checks support the integration plan; they are not a full audit of every source claim or package in the product specification. Recheck mutable APIs during Sprint 0. Keep imported data releases, rights and extraction evidence in the repository manifest rather than copying unverified current-year assertions into code.

## Risks and responses

| Risk | Early evidence and response |
|---|---|
| Provider access or schema mismatch | Sprint 0 real call. If blocked, preserve the fixture track and report live completion blocked; no unapproved provider/model substitution. |
| Durable history leaks private payloads | Sprint 0 inspect persisted records and crash recovery. Qualify ID-based activity boundaries before expanding live research. |
| Data curation takes longer than coding | Start manifest in Sprint 0; finish labels in Sprints 3–5. Track owner and source permissions. Extend estimates rather than manufacture evidence. |
| Monthly bounds reject viable real routes | Preserve exact dates and explain coarse-model limitations. Offer explicit reviewed changes within scope, not an infeasibility claim about life. |
| Search does not finish within limits | Keep every encountered route and disclose truncation. Use tiny complete cases for proof; qualify the full-size workload empirically. |
| Attractive UI hides uncertainty | Make conditional/unknown states part of initial compositions and formative comprehension tests. Block misleading presentation. |
| Design quality arrives too late | Approve signature compositions in Sprint 0, shell in 1, map in 3 and route view in 7. Fix interaction debt before final integration. |
| Scope expands into public launch | Maintain the explicit L0 checklist. Schedule hosted/private-beta and M1 work as later milestones with their own acceptance evidence. |
| Human review becomes the bottleneck | Sprints 0–2 took 16 hours of wall-clock time, so review points that assumed weeks between them now set elapsed time. Hold three fixed review sessions as dispatch preconditions (section 10) and size the remaining work in human review hours (section 6). |
| Language-rule refinement becomes open-ended (support screen, explanation validation, redaction, value readers) | Grow a rule only for a reproduced defect or an evaluation failure. Prefer a fail-safe outcome (unknown, unclear, not kept) to a new pattern. Record a hypothetical form as a known limit. Keep the safeguards and accepted limitations as recorded (v1.2; ruling R11 in the task file). |
| Infrastructure polish displaces evidence | From the option pack to review session 2, polish that no failing check or reproduced defect requires goes to the final review list (v1.2; ruling R12 in the task file). |
| The numerical core is unexercised on real, reviewed options before Sprint 9 | Build the England option pack from the required corpus (section 9), run the TRACE-01 checker on P01's real option set and review it at session 2, and hold one formative comprehension session after Sprint 5 (section 5). |
