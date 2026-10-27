# Real-source extraction corpus

`manifest.json` is the checked-in manifest for the real pages that qualify extraction,
grounding and outcome mapping (spec section 20, "M0 source corpus and acceptance"; plan
section 9). It extends the pack's `fixtures/m0/source_corpus_manifest.json` (hash recorded
in `derived_from`) with one slot per required page, intended case types, owners and open
items.

**Status: not collected (0 of 20 job postings, 0 of 10 course pages, 0 of 3 funding
pages).** Synthetic personas and generated HTML do not count toward it.

## What lives where (ruling R3)

| Item | Location |
|---|---|
| URL, retrieval time, HTTP status, SHA-256 of the retained body, rights status, template family, split, labels, minimal span excerpts, missingness | `manifest.json` (git) |
| Full page bodies, where retention is permitted | `var/evidence/corpus/<slot id>/` (gitignored; path proposed, Task 3 confirms it) |
| Pages that may not be retained | Hash, URL, date and the minimal excerpts needed to locate each labelled span; record the re-verification limitation |

## Filling a slot

1. Check robots.txt and the site terms, and record `robots_and_terms_checked_at`. Never
   fetch past a sign-in, paywall or access control. Policy-denied fetches become
   `attempt_cases`, not page slots.
2. Fetch with the acquisition pipeline once it exists (Task 7). Record `retrieved_at`,
   `http_status`, `content_type` and `sha256` of the exact bytes kept.
3. Set `rights_status`. It stays `pending human rights review` unless the terms clearly
   permit retention (for example, a GOV.UK page under the Open Government Licence v3.0,
   quoted with its date). Then it may be `permitted: <licence, date>`.
4. Assign `template_family` and `split` before any tuning uses the page.
5. Label fields: value, unit or currency, the span (offsets or a stable selector plus a
   minimal excerpt), expected unknowns and expected failure states. `label_review` stays
   `not run - requires human domain reviewer` until a person reviews it.
6. Update `collected_samples` and the slot's `status`.

A page that later disappears keeps its slot. Record the failed recheck, or replace the page
and give the documented reason (plan section 9).

## Open items

Every unresolved access or reviewer need is in `open_items`, each with an owner and a
disposition. The human-only items (OI-07 rights, OI-08 label review) are **not run -
requires human** (ruling R2). No agent records them as passed.

## Human rights-review checklist (OI-07)

For each retained page:

- [ ] The page was publicly reachable without signing in, and the fetch respected
      robots.txt.
- [ ] The site's terms or licence statement were read and dated. The quoted basis supports
      retaining the body locally for private evaluation, or only minimal excerpts.
- [ ] Nothing personal about a third party is retained beyond what the posting publishes.
- [ ] Attribution required by the licence is recorded.
- [ ] The decision is written into `rights_status`, with the reviewer's name and date in
      the commit message.
