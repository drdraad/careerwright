# Real-source extraction corpus

`manifest.json` is the checked-in manifest for the real pages that qualify extraction,
grounding and outcome mapping (spec section 20, "M0 source corpus and acceptance"; plan
section 9). It extends the pack's `fixtures/m0/source_corpus_manifest.json` (hash recorded
in `derived_from`) with one slot per required page, intended case types, owners and open
items.

**Status: not collected (0 of 20 job postings, 0 of 10 course pages, 0 of 3 funding
pages).** Synthetic personas and generated HTML do not count toward it.

## What lives where (ruling R3; the session 1 rights policy)

| Item | Location |
|---|---|
| URL, retrieval time, HTTP status, SHA-256 of the retained body, rights status, template family, split, labels, minimal span excerpts, missingness | `manifest.json` (git) |
| Full page bodies, where the page's class permits keeping them privately | `var/evidence/corpus/<slot id>/` (gitignored; path proposed, Task 3 confirms it) |
| Full text in git | Only for the two OGL classes below, only if the option pack needs it, with the OGL attribution |
| Pages that may not be retained | Hash, URL, date and the minimal excerpts needed to locate each labelled span; record the re-verification limitation |

## Rights policy (H-06, set by the product owner at session 1, 2026-10-28)

The product owner's own answers are in `docs/reviews/session-1.md` (Part A). These
conditions hold for every class: public pages only, nothing behind a login, robots.txt and
the site's terms respected, and no third party's personal details kept (recruiter names,
phone numbers). For each page, the agent records the class and the terms it relied on.

"Keep privately" means the full page body in the gitignored `var/evidence/` folder on this
machine, for local testing only. "Commit excerpts" means git holds only the URL, date, hash
and the short quoted spans that prove each extracted value.

| Class (`manifest.json` id) | Pages | Permitted |
|---|---|---|
| `govuk` (line 1) | GOV.UK pages (Open Government Licence v3.0) | Keep privately; commit excerpts; commit the full text if the option pack needs it, with the OGL attribution |
| `public-sector` (line 2) | National Careers Service, Skills England, ONS, Find an Apprenticeship pages (public sector, OGL where they say so) | As `govuk`. The full text needs the OGL attribution, so it is committed only for a page that says it is under the OGL |
| `course-provider` (line 3) | College, university and training-provider course pages | Keep privately; commit excerpts only, never the full text |
| `professional-body` (line 4) | Professional bodies and regulators (for example HCPC, NMC) | As `course-provider` |
| `employer-posting` (line 5) | Employer job postings on their own careers site or applicant-tracking page | Keep privately; commit excerpts only |
| `job-board` (line 6) | Job-board and aggregator pages (for example Indeed, Reed, Totaljobs) | Reference only: hash and excerpts, never the body, unless the site's terms clearly allow more. If it is not clear what they allow, the page stays reference only |
| `other` (line 7) | Anything else, or a page not clearly within one class above | Stays `pending human rights review` for the product owner, page by page (checklist below) |

## Filling a slot

1. Check robots.txt and the site terms, and record `robots_and_terms_checked_at`. Never
   fetch past a sign-in, paywall or access control. Policy-denied fetches become
   `attempt_cases`, not page slots.
2. Fetch with the acquisition pipeline once it exists (Task 7). Record `retrieved_at`,
   `http_status`, `content_type` and `sha256` of the exact bytes kept.
3. Set `rights_status` from the rights policy above. Name the page's class and the terms
   relied on, quoted and dated: `<class id>: <terms, quoted and dated>`, for example
   `govuk: "<the licence statement as the page words it>" (<where on the page>, read
   <date>)`. Keep only what that class permits. A page outside the classes, or not clearly
   within one, stays `pending human rights review`.
4. Assign `template_family` and `split` before any tuning uses the page.
5. Label fields: value, unit or currency, the span (offsets or a stable selector plus a
   minimal excerpt), expected unknowns and expected failure states. `label_review` stays
   `not run - requires human domain reviewer` until a person reviews it.
6. Update `collected_samples` and the slot's `status`.

A page that later disappears keeps its slot. Record the failed recheck, or replace the page
and give the documented reason (plan section 9).

## Open items

Every unresolved access or reviewer need is in `open_items`, each with an owner and a
disposition. The human-only items (OI-07 rights review of pages outside the policy's
classes, OI-08 label review) are **not run - requires human** (ruling R2). No agent
records them as passed.

## Human rights-review checklist (OI-07)

For each retained page outside the rights policy's classes, or not clearly within one:

- [ ] The page was publicly reachable without signing in, and the fetch respected
      robots.txt.
- [ ] The site's terms or licence statement were read and dated. The quoted basis supports
      retaining the body locally for private evaluation, or only minimal excerpts.
- [ ] Nothing personal about a third party is retained beyond what the posting publishes.
- [ ] Attribution required by the licence is recorded.
- [ ] The decision is written into `rights_status`, with the reviewer's name and date in
      the commit message.
