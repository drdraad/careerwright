# The school-leaver pack session: the AI check that counts as the product owner's review

The product owner's ruling, verbatim (1 November 2026): "AI check counts as my review". The
controller offered: an AI checks all rows against the official pages; it counts as their
review; rows the AI can't confirm go back to them. So: you check every row of
`docs/reviews/school-leaver-pack-questions.md` against its page, and write the session record.

## Inputs
- `/home/user/careerwright/planning/env-cloud.md`.
- The questions: `/home/user/careerwright/docs/reviews/school-leaver-pack-questions.md`.
- Pack 0.3.0 (unpublished) and its labels: `backend/src/careerwright/catalogue/packs/england_option_pack/`
  (the 0.3.0 file) and `backend/tools/school_leaver_labels.json`.
- The kept page bodies: `/home/user/careerwright/var/evidence/corpus/<slot>/` (GOV.UK).
  UCAS (C12) has no kept body: its located excerpts and contexts are in
  `planning/task-7f-fetch-output-c12.json` and `task-7f-fetch-output-c12-date.json`.
- How session 2's record looked: `docs/reviews/session-2-answers.md`.

## For each row
Answer **yes** only if the page's own words, read in context (not just the excerpt), state
exactly what the row says, in the same unit, period, condition and date range. Answer **no**
with the page's words if the page says something different. Answer **can't confirm** with
the reason if the page doesn't settle it (missing, ambiguous, out of the excerpt's reach, or
a judgement only a person can make, such as a rights class or a "most undergraduate courses"
reading). Never yes on a guess. The UCAS deadline row: say exactly what the page shows
around "13 Jan" and the 2027-entry heading; yes only if the page itself pairs the date with
the nursing degree's deadline.

## Write
`/home/user/careerwright/docs/reviews/school-leaver-pack-session.md`, in plain words:
- the ruling verbatim, its date, and that the reviewer is "an AI check, counted as the
  product owner's review by their ruling";
- one line per row: number, answer, and for no / can't confirm the page's words or the
  reason;
- a short list of the can't-confirm and no rows, for the product owner, plain words, money in
  pounds.
Commit only that file, with an explicit pathspec, in the main tree (nothing else is running
there except possibly the controller's acceptance run: don't touch code). Commit message ends
with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Rules
Read-only apart from that file. No web requests, no live calls, no subagents, never start
Docker, never read `.env` or print an environment value, never push. Reply with the counts
(yes / no / can't confirm) and the no and can't-confirm rows in one line each.
