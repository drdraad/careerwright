# ADR 0001: L0 local delivery boundary

- Status: Accepted (records the local development plan v1.0, section 1)
- Date: 2026-10-27
- Requirements: BND-1 (spec section 1), ARC-1 (spec section 17)

## Context

The product specification (v1.2) defines M0 as a hosted, invitation-only private beta: Cloud
Run, a GCE worker, Cloud SQL, Cloud Storage, GCP Secret Manager, real Google sign-in, TLS and
one deployed end-to-end smoke test. The local development plan (v1.0) changes the endpoint to
a release candidate that runs on a developer's computer and raises the UX bar. It calls this
milestone **L0** so that nobody reads it as M0 delivered.

Authority order: specification, then the plan's local overrides, then the sprint task
breakdown. This ADR records the overrides and does not relax anything else.

## Decision

L0 keeps M0's business semantics and bounded model. It makes these deliberate local
adaptations and no others:

| Area | M0 (specification) | L0 decision |
|---|---|---|
| Geography | England, en-GB, GBP; up to three cities and three active targets | Unchanged. Country-neutral identifiers and explicit unsupported-region states remain. |
| Product journey | Sure/unsure entry through a printable plan | All six chapters (You, Roles, Skills, Options, Routes, Plan), including apply-now, conditional and unavailable outcomes. |
| Planning model | 24 action concepts, two starts each, six selected actions, 24 months, one conditional bridge role | Unchanged. |
| Hosted infrastructure | Cloud Run, GCE worker, Cloud SQL, Cloud Storage | Local processes under Docker Compose, PostgreSQL 16 and private local storage. No deployment, domain, public URL or Terraform work. |
| Authentication | Firebase Authentication with Google sign-in and a verified invitation allowlist | Firebase Auth **emulator** with a `demo-` project and seeded identities. Invitation and ownership checks stay. Real Google OAuth qualification is deferred. |
| Secrets | Versioned runtime key in GCP Secret Manager; AES-GCM credential records | Local runtime master key outside the repository and database; authenticated encryption for saved user keys. No Secret Manager or KMS. |
| Transport | TLS | Loopback-only HTTP as an explicit development exception. Published ports bind 127.0.0.1; non-local Host/Origin is rejected; no LAN binding or tunnel. |
| Data credentials | Meta key; live bounded Adzuna search | A Meta key suffices for the live-assisted journey. Adzuna needs separate credentials and is qualified separately; it is never assumed to come with the Meta key. |
| Export | Browser print CSS, JSON and ICS | Unchanged: print CSS, JSON and ICS from one plan snapshot. No server PDF, calendar connection or automatic external action. |
| Visual scope | M0 surfaces; motion and halos are M1 | M0 surfaces plus purposeful panel and graph-reveal transitions. Semantic zoom, mini-map, pulsing halos, generated illustrations and animated journey overlays stay deferred. |
| Acceptance | Includes one deployed end-to-end smoke test | Replaced by a local end-to-end run with a real, budget-capped Meta smoke. No deployed smoke test is claimed. |

The stack does not change: React/Next.js, SVG/D3, FastAPI/Pydantic AI, DBOS and PostgreSQL.
No other solver, workflow engine, renderer, scraper vendor, vector database or general agent
platform is introduced.

The three runtime modes are recorded on every workspace and run: **demo** (no key, no
outbound traffic after installation and seeding, persistently labelled synthetic data),
**live-assisted** (one user Meta key) and **live-vacancy extension** (adds Adzuna
credentials). Fixtures never fill missing live fields or appear as real evidence.

## What L0 does not change

Being local does not remove provenance, integer-money, isolation, secret, cancellation or
deletion requirements. The M0 non-deferrable invariants (spec section 1) apply unchanged:
unknown is not zero or ineligible, failure is not an empty success, a truncated search is not
infeasibility, nothing is invented, and LLM proposals never directly commit facts or plans.

## Consequences

- L0 claims no M0 hosting, TLS, Secret Manager, real Google sign-in or deployed-smoke gate.
  Those remain open for a later hosted milestone with its own acceptance evidence.
- Emulator tokens are unsigned (verified in Sprint 0: `alg: none`). Accepting them must be
  confined to explicit local configuration. Emulator acceptance is not evidence of production
  identity security.
- Development and live-provider qualification use synthetic personas. Processing real
  people's information still needs the specification's privacy assessment and disclosures.
  Passing engineering tests is not legal compliance.
- Every later ADR and sprint review checks scope against this table. Hosted, private-beta
  and M1 work is scheduled as separate milestones and is not claimed by L0.
