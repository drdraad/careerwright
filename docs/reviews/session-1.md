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

## Addendum (2026-10-28): H-12 item 7, "Written explanation" (ADR 0007 decision 12)

Asked by the controller in the chat on 2026-10-28, after the session 1 package, because
Task 6b added this checklist item after the package was drafted. The questions as asked, and
the product owner's answer as given ("yes yes yes yes yes"):

1. The note is requested automatically when suggestions first appear, with no click. That's one
   paid call per set of suggestions: the cheap test model for synthetic data, the production
   model otherwise. — yes
2. Each sentence in the note must quote both you and the job's official record. A one-word
   answer like "art" can't be quoted on its own. — yes
3. Claims about readiness, pay or hiring are blocked ("qualified", "well-paid", "in demand",
   "employers need"). Such a word is allowed only if the job's own record uses it. Known false
   alarm: "employers need" is blocked even in careers-adviser notes. — yes
4. After a failure, "Try again" appears only if no paid call was made. Otherwise "Suggest
   again" appears, which makes a new set of suggestions. — yes
5. The note sits above "How Nessa found it" and says only the quoted words were checked. The new
   test case for it (EXP-01) is accepted as written. — yes

Not asked, so not covered by these answers: the claim and quotation bounds (counts and
lengths), the full function-word list, the "first view" definition of a slate, and the session
1 transcription's later changes to the support screen (the three phrasings as built).

Transcription note (agent, not part of the record): this addendum supersedes the note above
that the written explanation and EXP-01 were not put to the product owner. ADR 0007's
checklist ticks item 7 for what the five answers cover; what they do not cover stays an
unticked open item.

## Addendum (2026-10-29): names in running text (Part A's "always true" clause)

Asked by the controller in the chat on 2026-10-29, after Task 7A found that a personal name
in running text (for example "ask for Jane in HR") cannot be detected deterministically
(ADR 0009 decision 4, known limits). The question as asked, and the product owner's answer as
given ("yes"):

1. May a person's name that appears in a page's running text stay in the copy kept privately
   on your machine? — yes

Not asked, so not covered by this answer: names in excerpts, claim values or anything
committed to git; names in structured contact fields (still removed); email addresses and
phone numbers (still never kept).

### Delegated decision (2026-10-29): names in excerpts and claims

The controller then asked: "May a name in running text also stay in those short evidence
quotes, including the ones committed to git?" The product owner answered, as given: "Do as
you think best for these questions." This is therefore the controller's decision under that
delegation, not the product owner's own answer, and the product owner may reverse it:

- Excerpts and claim values kept on this machine (the database): a name in running text may
  stay, as in kept bodies. Names cannot be detected deterministically (ADR 0009 decision 4).
- Excerpts committed to git: they may be committed on this machine. Before any push or
  publication of the repository, the committed excerpts are reviewed for names in running
  text. That review is a human gate on the push, carried in the release report.
- Unchanged: structured contact names, email addresses and phone numbers are removed
  everywhere.
