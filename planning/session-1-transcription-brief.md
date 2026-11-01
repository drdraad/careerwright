# Session 1 transcription (controller brief; dispatched after Task 6b, before Task 6c)

Ruling R10: the first task dispatched after a review session transcribes its outcome. The
product owner held session 1 on 2026-10-28; their own answers are in
`.superpowers/sdd/l0-sprint-tasks/session-1-package.md` (every line answered "yes"). You
transcribe that record; you never supply or reinterpret it (R2).

Read first: `CLAUDE.md`, `docs/plan/l0-sprint-tasks.md` (Global Constraints, standing
rulings R2, R3, R9, R10), ADR 0007 (decision 7 and "Human review checklist"), ADR 0008
decision 3, `corpus/README.md`, `corpus/manifest.json` (`policy`), the H-06 and H-12 rows
of `docs/requirements-register.md`, `backend/src/nessa/profile/safety.py` and
`backend/tests/domain/test_safety.py`.

## Deliver

1. `docs/reviews/session-1.md`: the session record. Date 2026-10-28, held by the product
   owner, the package's questions and the answers exactly as given (copy them; do not
   rephrase an answer), and a line saying the package was agent-prepared and the answers
   are the product owner's own (R2, R10).
2. H-06 rights policy:
   - `corpus/README.md`: replace the "stays pending unless the terms clearly permit"
     instruction with the policy's classes (Part A lines 1–7) and what each permits (keep
     privately; commit excerpts; commit full text for the OGL classes with attribution;
     reference only for job boards and aggregators unless their terms clearly allow more;
     anything else pending human rights review). The standing conditions stay (public only,
     no login, robots.txt and terms, no third-party personal details). For each page an
     agent records the class and the terms it relied on. Keep the OI-07 checklist for pages
     outside the classes.
   - `corpus/manifest.json` `policy`: add the classes and their permitted retention so a
     page's `rights_status` can name its class; keep existing values valid.
   - Register H-06: the policy part done 2026-10-28 (session 1); pages outside the classes
     stay "not run — requires human".
3. H-12: tick ADR 0007's checklist items as accepted by the product owner on 2026-10-28
   (session 1), citing `docs/reviews/session-1.md`; register H-12 done, same citation.
   Part B line 3: the 164 within-group alias pairs keep folding (confirmed). Line 6: the
   powered REC1-09 counterfactual comparison (at most $0.07, test model) is approved to run
   in Task 16; record that on REC1-09 and in ADR 0007 decision 9. Make no live call.
4. The three phrases (Part B line 1, optional addition: "yes"). Controller ruling: add them
   as constructions in the screen's existing proximity design, not as bare tokens, because
   bare "carry on" and "end it" are ordinary career wording:
   - "carry on" joins "go on" wherever "go on" is a construction (cannot go on, no reason to
     go on), in every inflection of carry.
   - "end it": an intent or wish word within the screen's usual window before an end word
     followed by "it" (beside the existing "end it all").
   - "not exist": a wish or intent with a negation and "exist" within the window ("want to
     not exist", "wish I didn't exist", "don't want to exist").
   Use TDD. Add these rows to `CORPUS` in `test_safety.py` verbatim (source tag
   `session1`); do not compose any other distress wording:
   - must flow: "I can't carry on." / "There's no reason to carry on." / "I want to end
     it." / "Sometimes I want to not exist." / "I wish I didn't exist."
   - must not flow: "I'd like to carry on working in healthcare." / "Jobs like that don't
     exist here." / "The course ended and I want to start a new one."
   Record any new false positives you find (for example "I can't carry on working nights")
   in ADR 0007 decision 7's known limits and keep them as pinned rows. Update the ADR's
   description of the constructions and the matching register row.
5. Task 6b carry-over (two Minors from its last re-review; controller ruling to fix here):
   - `backend/src/nessa/profile/exploration.py:635`: the no-quotable-answer pre-check uses
     `quotable(raw text)`, but the real rule reads quotations through `quoted_span` and the
     fixture predicate (`fixture_explainer.py:75`, `_accepted`). An answer set made only of
     single-quoted phrases ending in "s" (for example 'odd jobs', straight or curly) passes
     the pre-check, then no quotation of it verifies: the demo note fails, and a live run
     would spend a paid repair before `invalid_model_output`. Make the pre-check use the
     same predicate the fixture uses (one function, not a copy). Test with 'odd jobs'
     (both quote styles) as the only answer: refused before any run, typed
     `INSUFFICIENT_EVIDENCE` / `no_quotable_answer`. Correct ADR 0007 decision 12 where it
     says the fixture's note "always passes the check" if any case remains.
   - `docs/reviews/sprint-2.md:434-436` (Task 6b addendum, round 3 recheck): the caveat
     names only quotations; reading the full ESCO records also widens the record-only
     allowance for readiness, pay and hiring words and covers every essential skill, not
     the prompt's first N. Say so, and add the same caveat to the round-1 recheck sentence.
6. Run `make check`; run the safety and slate-explanation tests and paste their output in
   the report. Run `make acceptance` once at the end if any API or UI file changes. No
   live calls.

## Rules
- Edit/Write tools only for every file change (no sed, awk, perl, heredocs or redirection).
- Do not edit `CLAUDE.md`; propose wording in the report if it needs a change.
- Commit with messages ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  Never push. Do not dispatch subagents.
