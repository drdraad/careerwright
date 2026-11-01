# Session 1 transcription — fix round 1 (FIX_BASE eb53837)

Review 1: Approved (record byte-faithful, H-12 six-of-seven split honest, constructions sound,
one shared predicate). These Minors need decisions; the controller's rulings are below.
Fix all of them. Name covering tests, command and output in your fix report.

1. `safety.py:136, 234` — the "going" false positive. Ruling: narrow `_not_exist` to want and
   wish forms only (`_WANT` plus wish/wishes/wished/wishing), not the whole `_INTENTS` set.
   "isn't/aren't/not going to exist" is everyday wording in a product about AI exposure, and a
   flagged turn drops the next question. Keep all five `session1` must-flow rows passing; pin
   "That job is not going to exist in ten years." and "Those roles aren't going to exist." as
   must-not-flow rows; update ADR 0007 decision 7's description and known limits (the recall
   given up for other intent words in this one construction).
2. Stale "provisional" wording. Ruling:
   - `Conversation.tsx:133-134`: remove "This note is provisional until it is reviewed." The
     panel's wording and resources were accepted at session 1; review status is not for a
     person who may be in distress. Update its test and recapture the support-panel states at
     the three viewports.
   - `safety.py:43` `REVIEW_STATUS`: say the policy was accepted for L0 at session 1 (H-12) and
     the three phrasings added on 2026-10-28 are not yet reviewed as built. Never claim more.
     Make the docstring at `safety.py:29`, the H-12 and PROF-09 rows and
     `test_interview_choices.py:138` agree with it.
3. `vocabulary.ts:547`: replace "Your answers are too short to quote" with a neutral title that
   holds for both causes (for example "Your answers can't be quoted on their own"); keep the
   recovery. Web test; recapture that state only if its pixels change.
4. `corpus/README.md:35`, `manifest.json:34`: add one line to session-1.md's transcription notes
   (the agent section, not the record) naming "full text only for a page that says it is under
   the OGL" as the transcriber's reading of Part A line 2, which the product owner may widen.
5. `requirements-register.md:117` (REC1-09) and ADR 0007:539-545: phrase REC1-09 as decision 9
   does. The product owner approved "run the powered comparison at release, at most $0.07, test
   model". Label the sample count, request count, scope above the 9-request cap and fields as
   derived from the Task 6 report, and state that the pass rule across several samples per arm
   is still open and must be decided before Task 16 runs it.
6. `manifest.json:17-26, 39, 14`: exclude class `other` from the generic
   `<rights_policy class id>: …` value (it stays `pending human rights review`); make
   `git_holds` mention OGL full text committed for the pack.

Also: `make check`; `make acceptance` once at the end (UI change). No live calls. Edit/Write
tools only for file changes. Append the fix report to session-1-transcription-report.md and
reply with the short contract.
