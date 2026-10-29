# Intermediate code review (2026-10-29)

- The product owner supplied this review in the chat on 2026-10-29, at commit 12190cf (after
  Task 7 slice 7A, with slice 7B in progress). It is copied below as given. The author is
  not stated.
- The product owner asked for the development plan to be modified where the controller
  concurs. The controller concurred with all four points, so plan v1.2 applies them:
  `docs/plan/development-plan.md`, `docs/plan/l0-sprint-tasks.md` (Task 7d, R11, R12) and
  ADR 0008's amendment.

---

Nessa is broadly on track. The foundations are strong; the main risk is spending too long
refining them before proving the core planning experience with real evidence. I would keep
the architecture and the revised delivery order.

What this repo does: Nessa connects career discovery, evidence, training options and
financial constraints into explainable routes. I assessed it against the planned local,
single-user deployment, including its concurrent API and background workers.

The implementation supports several important quality claims: clear domain boundaries, a
shared execution path for model calls, validated profile changes, generated API types, and
explicit distinctions between unknown, failed and unavailable results. The tests exercise
meaningful failure cases. I found no reason for a broad refactor or additional
infrastructure.

Four things deserve attention:

1. Fix the known cancellation deadlock. Cancelling work and publishing worker progress can
   acquire database locks in opposite orders. PostgreSQL can abort one transaction,
   leaving the user to repeat cancellation. This affects normal local use and is already
   acknowledged in ADR 0009 (docs/adr/0009-evidence-acquisition.md:540); code inspection
   confirms the conflicting paths. Give it a focused lock-order correction and a concurrent
   regression test before extending background execution further.
2. Make real evidence the next proof of progress. The required corpus remains 0 of 33 pages
   (corpus/README.md:9). Acquisition has substantial implementation and testing, but
   extraction accuracy on that corpus remains unproven. This is consistent with the
   current task sequence, rather than a missed milestone—but it should now dominate
   priorities. Finish the current catalogue work, then follow the existing chain: option
   pack → capability/outcome model → monthly financial checker → human review. Further
   infrastructure polish should not displace that work.
3. Put a firm boundary around language-rule refinement. The review history shows repeated
   repairs to support screening, explanation validation and redaction. Many fixes were
   necessary, but this is the clearest rabbit-hole risk. The support classifier eventually
   needed simplification after repeated unsuccessful corrections
   (docs/reviews/sprint-2.md:270). Preserve required safeguards, retain the explicitly
   accepted limitations, and require a reproduced defect or evaluation failure before
   expanding linguistic rules. More exceptions do not establish general understanding.
4. Get human feedback before adding more interface detail. The saved screenshots show
   coherent typography, spacing and visual identity. They also show substantial reading
   burden: one mobile suggestion card
   (docs/reviews/sprint-2/screenshots/you--slate--390x844.png) extends beyond a screen
   before its decision controls appear. Sprint 2's human design review is still
   outstanding. Use that review to test scanning, understanding and choosing; shorten the
   initial presentation where needed while keeping evidence accessible. Automated
   accessibility checks cannot answer whether the experience feels straightforward.

I would treat "40% complete" as an effort estimate, not a measure of product readiness. The
financial checker, optimiser and usable end-to-end planning journey still carry substantial
uncertainty. The plan's decision to prove small, independently checked optimisation cases
before building full-scale search machinery is sound.

Fresh checks on committed revision 12190cf passed: 1,132 backend tests, 211 web tests,
lint/format checks, Python and TypeScript checks, generated-client consistency, and fixture
validation. I used an isolated copy and left the ongoing catalogue changes untouched.

Not checked: full Docker/browser acceptance, fresh provider calls, or human usability; the
deadlock was inspected, not reproduced. The principal remaining risk is whether real
evidence supports useful, trustworthy routes.
