# Real-source extraction corpus

`manifest.json` is the checked-in manifest for the real pages that qualify extraction,
grounding and outcome mapping (spec section 20, "M0 source corpus and acceptance"; plan
section 9). It extends the pack's `fixtures/m0/source_corpus_manifest.json` (hash recorded
in `derived_from`) with one slot per required page, intended case types, owners and open
items.

**Status: collected (20 of 20 job postings, 10 of 10 course pages, 3 of 3 funding pages;
Task 7b, 2026-10-29); label review applied, 55 of 121 records reviewed (session 2,
2026-10-29 to 2026-10-30; Task 7c).**

- **Labels:** the labels live in the England option pack 0.2.0, the version session 2
  reviewed (`backend/src/careerwright/catalogue/packs/england_option_pack/`, ADR 0011). Each slot's
  `labels.claims` names its claims there. Version 0.1.0, every record proposed, is kept
  unchanged beside it.
- **Label review (H-07, session 2):** applied. The product owner answered Q1-Q15. An AI
  checked Q16-Q344, T1-T36 and R1-R58, and the product owner ruled on 2026-10-30 that those answers
  count as their review (`docs/reviews/session-2-answers.md`). Task 7c applied the record
  with `tools.session_2_pack`: 55 of 121 records are reviewed and 66 stay proposed; none
  was left out. Each slot's `label_review` says how many of its records were accepted, and
  each record in the pack carries its decision.
- **Rights review** of the one page pending (C08) is **not run - requires human**. Session 2
  took no rights decision.
- **The question package** is generated from the pinned 0.1.0 by `tools.option_pack_files`
  (from `backend/`), never edited by hand.
- **Split:** 20 pages are in the development split, 13 in holdout. The early accuracy read
  of the development pages is `docs/evidence/option-pack-accuracy-read.md`.
- **Excluded:** synthetic personas and generated HTML do not count toward the corpus.
- **Attempt cases** (Task 7A, 2026-10-29): X01, a GOV.UK address that returns 404, and X02,
  a LinkedIn posting the source manifest refuses without a request.

| Owner (consumes the reviewed version) | Slots | Collected | Sources |
|---|---|---|---|
| Task 8 (Sprint 3) | J01–J20 | 20 | 9 Reed and 8 NHS Jobs pages (job boards, reference only); 3 Adzuna adverts from one API response |
| Task 10 (Sprint 4) | C01–C10 | 10 | 6 course-provider or public-sector pages kept privately; 3 Reed pages (reference only); 1 university page pending rights review (C08) |
| Task 12 (Sprint 5) | F01–F03 | 3 | 2 GOV.UK pages; 1 Department for Education page (Skills for Careers) |

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
2. Fetch with the acquisition pipeline (Task 7A): from `backend/`, `uv run --locked python
   -m tools.corpus --slot <slot> --url <url>` (add `--rights-class <class> --terms "<terms,
   quoted and dated>"` to record your classification, dated with the run's date; it replaces
   the class the pipeline derived in either direction before anything is kept, but never
   keeps more of a listed host's page than the source manifest permits). A page's own
   structured data never decides its class: an unlisted employer careers or ATS page is
   `other` until you classify it. It applies the URL and
   address checks, the source permission manifest
   (`backend/src/careerwright/evidence/sources.json`, OI-11), robots.txt and the fetch bounds, keeps
   the body under `var/evidence/corpus/<slot>/` only where the class permits, and prints the
   record: `retrieved_at`, `http_status`, `content_type`, `sha256` of the exact bytes and each
   claim's offsets and excerpt. It never edits this manifest.
   - Add `--locate "<excerpt>"`, once per labelled excerpt, to get each excerpt's offsets in
     the hashed text and its real count (`count`; the first 5 spans are listed). A run of
     spaces matches any whitespace, and the tool prints the exact text found. This is the
     only way to place an excerpt on a page whose body is not kept.
   - For an Adzuna slot, run `--adzuna "<what>" "<where>"` in place of `--url`. That is one
     request through `make live-adzuna`'s own capped, ledgered, leak-scanned path.
   - Each run is one process with its own pacer. Leave at least the host's rate limit
     (`sources.json`, 5 seconds by default) between runs against the same host: a shell
     loop of runs does not pace them.
3. Set `rights_status` from the rights policy above. Name the page's class and the terms
   relied on, quoted and dated: `<class id>: <terms, quoted and dated>` for any class but
   `other`, for example
   `govuk: "<the licence statement as the page words it>" (<where on the page>, read
   <date>)`. Keep only what that class permits. A page outside the classes, or not clearly
   within one, stays `pending human rights review`.
4. Assign `template_family` and `split` before any tuning uses the page.
5. Label fields: value, unit or currency, the span (offsets or a stable selector plus a
   minimal excerpt), expected unknowns and expected failure states. A new slot's
   `label_review` stays `not run - requires human domain reviewer` until a person reviews
   it, and its labels go into a new option pack version.
6. Update `collected_samples` and the slot's `status`.

A page that later disappears keeps its slot. Record the failed recheck, or replace the page
and give the documented reason (plan section 9).

## Open items

Every unresolved access or reviewer need is in `open_items`, each with an owner and a
disposition. The human-only item OI-07 (rights review of pages outside the policy's
classes) is **not run - requires human** (ruling R2). No agent records it as passed. OI-08,
the label review, was held at session 2 and applied by Task 7c.

After Task 7c, the items still open:

- **Human gate:** OI-07 (C08's rights).
- **Corpus gaps and later captures:**
  - OI-05: no real prompt-injection page was found, so a labelled synthetic page covers
    the case.
  - OI-06: J10's second capture is Task 8's.
  - OI-12: employer careers and applicant-tracking pages the pipeline cannot read.
  - The case `deferred_grant` was not observed on F03.
- **Before any push:** OI-13 lists the committed excerpts that hold a person's name.
- **Unchanged:** OI-10 (the evidence directory's backup).

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

Two questions for this review, both to be answered before any push:

- [ ] **May C08's committed excerpts stay?** Its 18 excerpts in the option pack (1,322
      characters, the most of any page) rest on ruling R3's default for a pending page,
      yet the page is pending because its notice says its material "may not be reproduced
      without permission".
- [ ] **Should C01 and C08 be treated alike?** C01's "©Copyright 2026 all rights reserved"
      was read as within A3, and its body is kept privately. C08's notice was read as not
      clearly within A3.
