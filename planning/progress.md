# Careerwright L0: the live ledger (from 2026-11-01)

The full ledger to 1 November 2026 is `planning/archive/progress-to-2026-11-01.md` ("A" below,
with its line number). Commit ranges, rulings and history are there. Keep this file under 150
lines: one row per task, what runs now, open questions, open rulings and the final-review
list. Append new events at the end, one line each ("Ruling: what — why — cost if wrong").

## Tasks
| Task | Status | Commits (last range) |
|---|---|---|
| 1, 2 | complete | 324b2ab..2bb36e5; 2bb36e5..ff449da |
| 3, 4 | complete | ff449da..eb70b6a; eb70b6a..885596b |
| 5, 6 | complete | 10afdbf..8a817f6; 8a817f6..b543fd3 |
| 6b, 6c | complete | f360a86..6acaa71; e5365e1..8276485 |
| 7 (7A, 7B) | complete | 8276485..df44221; df44221..84dc858 |
| 7d | complete | c75b877..5b33f6b |
| 7b | complete | 417396a..4516de8 |
| 9 | complete | 09e820b..f6e9bfb |
| 11 | complete | 3d4e37a..594843c |
| 7c | complete | fa40db5..8e3d2ee (pack and capability reference 0.2.0) |
| W1 | complete | da25020..fa40db5 |
| W2 (W2A, W2B, W2C part 1) | complete | c1bc2f3..c84729e; c84729e..166e4ef; 166e4ef..f179d0f |
| W2E | complete; Sprint W closed | 8410eff..60c8516 |
| A1 (the audit) | complete | fde8e7d; 63b46ce..0931cbb |
| 13a | complete, integrated | ab22f45..8ff5100 (integrated 98fd0a9) |
| 12a | complete, integrated | 16ca9b0..86d7ead |
| 3b | complete, integrated | 4c9b72d..c2af6b1 (integrated fa7322c) |
| 13b | complete, integrated | ecbd662..99a8992 (integrated 29072d1) |
| 6d (A, B, C) | complete | 1577db2..59095b8; dff9c2e..51ca593; 51ca593..ecf7cec |
| Plan v1.6 (school leavers) | complete, integrated | 656dd64 (A 1011) |
| 12c (with the Advanced Learner Loan) | complete, integrated | b47cac2..b0f7715 (integrated 7c81100; follow-up eead7b9) |
| 6f (with Childline) | complete | 7b3a41e..3d136e3; Childline 8f6a669, 7a17a65 |
| 6e (with unread pages) | complete | 7ebb214..3d86198; follow-up 081f514 |
| Linux stack | complete | 578b0fe..d7c5ac7 (Minors M1, M4, M5 fixed in the acceptance fix) |
| Fetch proxy | complete, integrated | a05855f..ee263a3 (integrated 39e2176) |
| Acceptance fix | complete | fd4f939, 61597ee |
| 10A (Skills backend) | complete, integrated | dbc1bd1..d011472, b24668e, 81010d3; draft-checklist readiness 93c1e0e..51c03eb |
| e2e fix | complete | 53ca60d, c2f1cc9 |
| 7f (school-leaver pack) | first half complete (integrated 5420d35); second half running | 276c79d..bb438fc; session record 5ff2a18, answers 292e9e8 |
| School-leaver pack session | held: an AI check counted as the product owner's review (their ruling); the six rows sent back answered | `docs/reviews/school-leaver-pack-session.md` |
| Lean clean-up (documents) | running | f4b129a.. |
| 10B (Skills screens) | waits for session W2 (backend half done as 10A) | — |
| 12b, 14, 15 | wait (order: `planning/controller-state.md`) | — |
| 7e, 8, M, 16, 17 | wait (order: `planning/controller-state.md`) | — |
| Session W2 | not yet held (package: Task 6e) | — |
| End-to-end session | after Task 15 | — |

## Running now
- Acceptance run 10 (the controller, on 51c03eb and after).
- The lean clean-up (documents only, main tree).
- Task 7f's second half (worktree wt-7f from 292e9e8, `planning/task-7f-second-half-dispatch.md`):
  publishes pack 0.3.0 from the session record.
- Next: session W2.

## Open questions for the product owner
- None left on the school-leaver pack: the six rows sent back (Q75, Q95, Q104, Q110, Q115 and
  UCAS's words) were answered on 1 November 2026; Q101 stays unknown
  (`docs/reviews/school-leaver-pack-session.md`).
- Session W2's sheet: the lines starting "Session W2" in A (906, 958, 965, 1060), the
  Childline link question (A 1110), research beside the role in You (6e M5, A 1082), and
  `planning/carry-forward-task-W2D.md`.
- Skills: match entry facts by whole words? (Task 10A review M2,
  `planning/task-10A-review.md`).
- The first real-data live run on Muse Wonder needs your own key pasted into the app.
- Role research: the two-host "found" case is covered offline only; live scope is used up
  (A 1159).

## Open rulings and owed checks
- In force from 1 November 2026 (the product owner's yes): one paper file per piece (the
  review and the fix round go into the implementer's report); the infrastructure is frozen
  for L0 (no new services, workflows or run kinds; new pure computation runs in-process).
  The controller records them in the sprint tasks file (A 1165).
- The R11 carve-out from Task A1's re-review N2 waits for a docs touch (A 802).
- Owed, to confirm at the next acceptance run: 6d slice C's review captures (A 1028); Sam's
  title against ESCO and the UK index now the datasets are here (A 1081).

## Final-review list
Every line in A starting "Parked", "minor (deferred)" or "Carried to", and every review Minor
sent to the final review. Items carried to a task that is now complete are kept so the final
review can confirm they landed.
- Task 1 Minors M4, M7, DB-down escape, shutdown hang → Task 3 (A 42, 47).
- Task 2 Minors: phone "More" sheet, route-B Gantt label, Send in failure state → Tasks 4/14 (A 58).
- Task 3 Minors: live-smoke Ctrl-C rows, leak-scan masking, reconciler, SEC-07 (A 84).
- Task 4 Minors: `next` exception, role=alert double-read, lastSeen map → Task 6 (A 107).
- Task 5 Minors: stall flush, double JSON parse, r0009 upgrade test, $0.10 limit (A 130).
- Task 6 Minors: N-M1, N-M2, unscreened sends, REC1-09, A-M4 relevance floor (H-12) (A 190).
- Task 6b Minors: replace() bool, I3 serialisation, whole-word allowance (A 227).
- Session 1 transcription Minors: "by construction" count; `_to_end_it` scope (A 248, 256).
- Task 6c Minors: 360 px phone peek, lowerFirst acronyms, 200 % zoom → Task 14 (A 268).
- Task 7A: B-M12 split evidence/acquisition.py; DBOS attempt count after a crash (A 300, 378, 408).
- Task 7B: B-M4, B-M5, 1-A N2, 1-B Minor 2, m1, m2 (A 439, 453, 457).
- Task 7d M3: worker-side first-lock guard (A 470, 479).
- Task 7b M3, M9, N6; N5 and J01's header → Task 8 (A 498, 508).
- Task 9 M4, M7, N8, R3-1 (also Task 10's words) (A 523, 540).
- Task 11 M2, M12 and the report's items (A 564).
- Task W1 Minors → W2 (calm-mode click, label layout, phone width) (A 601).
- Task 7c M6, M7 (A 631).
- W2A: D-M5, A-M3, strip words → W2C (A 653); re-review 2 M1–M5 → W2C/W2D (A 667).
- W2B M6 → W2D, M7 → W2C, M8 chosen-occupation normalisations (A 681), with concept_key "&"
  and accents (A 724).
- W2C part 1 reviews: D-M3 leaf green and A-M6 tablet strip → session W2 (A 736); D-M7
  → W2C part 2 (A 737); D-M5 "Review the latest version, then save again." (A 775).
- Task 13a Minors M1–M6 (A 798); C07, C09, M4 → Task 12a (A 799).
- Task A1 apply review Minors (`planning/archive/task-A1-apply-review.md`; A 781, 802).
- Task W2E Minors: D-M1, design M2–M9, A-M2–A-M5, phone keyboard, ConnectionOut fields
  (A 825, 841, 842, 845).
- Task 12a Minors (`planning/archive/task-12a-review.md`, list; A 837, 857).
- Task 6d slice A Minors (A 875, 935, 938); → slice B (A 874, 905).
- Task 3b M4 settle-before-exit; ledger traceback when the stack is down (A 889, 920); → 6e (A 922).
- Task 13b Minors (A 948); R-M3, R-M5, R-M7 and typed limit fields → Task 14 (A 927, 947).
- Task 6d slice B Minors, app Minor 1 (A 972, 983); → Task M (A 985).
- Task 6d slice C: other Minors (`planning/archive/task-6dC-review-app.md`,
  `-design.md`; A 1017); chime → Task M, world.js pair → Task 8 (A 1030).
- Task 12c Minors 2, 3, ADR 0013 ruling 2 wording; Minor 4 → Task 12b (A 1038, 1046).
- Task 6f Minors M2, M4–M7 (A 1054, 1059).
- Task 6e Minors M4, M5, M10, M11; pack-title mismatch (A 1082).
- Fetch proxy Minors M1–M5 (`planning/archive/task-fetch-proxy-review.md`; A 1116).
- Linux stack Minors M2, M3 (`planning/archive/task-linux-stack-review.md`; A 1117).
- Task 7f: other Minors (`planning/task-7f-review.md`; A 1132); six claims whose deciding
  words sit beyond 200 characters (A 1136).
- Task 10A Minors M1, M3–M6 (`planning/task-10A-review.md`; A 1144).

## Events (from 2026-11-01, newest last)
PO answers (2026-11-01, verbatim): "yes, fix 1-3, 4. no not fair, 5 yes, 6 yes" — recorded in docs/reviews/school-leaver-pack-session.md (292e9e8). The school-leaver pack session is held (AI check counted as the PO's review by their ruling; six rows decided by the PO). Task 7f second half: dispatched (opus), worktree wt-7f reset to 292e9e8, task-7f-second-half-dispatch.md.
