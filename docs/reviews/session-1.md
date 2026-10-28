# Session 1 record: the rights policy (H-06) and the Sprint 2 checklist (H-12)

- Date: 2026-10-28. Held by the product owner.
- The package was prepared by an agent (ruling R2). The answers are the product owner's
  own, copied below as given, without rephrasing (rulings R2, R10). The agent that
  transcribed them supplied none.
- Plan: section "Human review sessions"; ruling R10; ADR 0008 decision 3.

## The package and the product owner's answers

About 2 hours. Two parts. Answer each line yes / no (+ a note if no).
Holding it before Task 7b lets 7b classify the option pack's pages itself; otherwise every
page stays "pending human rights review". It must happen before Task 8.

### Part A — H-06: which page classes may agents keep? (rights policy)

Always true, whatever you answer: public pages only, nothing behind a login, robots.txt and
site terms respected, a third party's personal details (recruiter names, phone numbers) never
kept, and the agent records for each page the class and the terms it relied on. A page that
fits no class you permit, or not clearly one, stays with you.

"Keep privately" = full page body in the gitignored `var/evidence/` folder on this machine,
for local testing only. "Commit excerpts" = git holds only the URL, date, hash and the short
quoted spans that prove each extracted value.

1. GOV.UK pages (Open Government Licence v3.0): keep privately, commit excerpts, and commit
   the full text if the option pack needs it (with the OGL attribution)? yes
2. National Careers Service, Skills England, ONS, Find an Apprenticeship pages (public sector,
   OGL where they say so): same as line 1? yes
3. College, university and training-provider course pages: keep privately and commit
   excerpts only (never the full text)? yes
4. Professional bodies and regulators (for example HCPC, NMC): same as line 3? yes
5. Employer job postings on their own careers site or applicant-tracking page: keep privately
   and commit excerpts only? yes
6. Job-board and aggregator pages (for example Indeed, Reed, Totaljobs): reference only —
   hash and excerpts, never the body — unless their terms clearly allow more? yes
7. Anything else: stays "pending human rights review" for you, page by page? yes

### Part B — H-12: the Sprint 2 checklist (ADR 0007, "Human review checklist")

Answer "yes = accept for L0 as built" or "no = change it (say what)".

1. Support screen: one word-list screen, no attempt to judge intent; a calm panel with four
   UK resources beside the conversation; every message still sent; nothing about the panel
   stored. Known limits: English only, a finite word list, some career phrases show the panel
   unnecessarily, messages never sent are never screened. Accept? yes
   (Optional: add the phrases "end it", "carry on", "not exist"? yes)
2. Inference guard: the model may not name a health condition, personality type or protected
   characteristic you never used yourself. Accept the current word lists? yes
3. Slate policy: the weights, quotas, family limit and relevance floor as built. 164 ESCO
   title pairs in the same group are treated as one role (example: physiotherapist and
   occupational therapist). Are those the same role for a slate? yes
4. Interview repair rate: track how often the one-question rule needs a paid repair, at
   release. Accept tracking only (no target yet)? yes
5. The 43 evaluation cases and their expectations as written (20 test fixed code; the model
   rests on single live samples so far). Accept for L0? yes
6. Counterfactual check (does an irrelevant detail change the advice?): run the powered
   comparison at release, estimated at most $0.07 on the test model. Approve? yes

## Transcription notes (agent, not part of the record)

- H-06: the policy part is done. The seven classes and what each permits are in
  `corpus/README.md` and `corpus/manifest.json` (`policy.rights_policy`). A page outside the
  classes, or not clearly within one, stays "pending human rights review": not run —
  requires human.
- Part A line 2: "full text only for a page that says it is under the OGL" (in
  `corpus/README.md` and the manifest's `public-sector` class) is the transcriber's reading
  of "OGL where they say so", not the product owner's words. The product owner may widen it.
- H-12: the six lines of Part B are ticked in ADR 0007's "Human review checklist", each as
  the line above puts it. The package was drafted before Task 6b added two things to that
  checklist: the written "Why this could suit you" (ADR 0007 decision 12) and evaluation
  case EXP-01, which made 44 cases. Neither was put to the product owner, so both are still
  not run — requires human.
- Part B line 1, the optional addition: the three phrases were added to the support screen
  after the session. Their form, as constructions in the screen's proximity design rather
  than bare words, is a controller ruling. The product owner has not seen them as built.
- Part B line 6: the comparison is approved for the release task (Task 16). Its sample
  and request counts come from the Task 6 report, and the pass rule across several samples
  per arm is still open: it must be decided before Task 16 runs the comparison. No live
  call was made for it.
