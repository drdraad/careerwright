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
| 7f (school-leaver pack) | complete, integrated (pack 0.4.0) | 276c79d..bb438fc; session record 5ff2a18, answers 292e9e8; second half e7b0916, ac16d6e (932cfc1) |
| School-leaver pack session | held: an AI check counted as the product owner's review (their ruling); the six rows sent back answered | `docs/reviews/school-leaver-pack-session.md` |
| Lean clean-up (documents) | complete | f4b129a..103463a |
| 12bA (Options backend) | complete, integrated | d9dbf8e..79bce14, fix 5dd0534 |
| 14A (Routes backend) | complete, integrated | 85ce831..bd4aaf2, fix aa807b9 |
| 10B, 12bB, 14B (screens halves) | wait for session W2 | — |
| 15 | waits (order: `planning/controller-state.md`) | — |
| 7e, 8, M, 16, 17 | wait (order: `planning/controller-state.md`) | — |
| Session W2 | not yet held (package: Task 6e) | — |
| End-to-end session | after Task 15 | — |

## Running now
- Back on the Mac (2026-11-02). Next: session W2 with the product owner, then 10B, 12bB and
  14B in parallel.

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
Task lean-cleanup: implementer DONE_WITH_CONCERNS — f4b129a..103463a (documents only): brief preamble 42,140 -> 26,077 bytes (a Task 10 brief 46,576 -> 30,512); ledger 334,017 -> 8,498 bytes (archived to planning/archive/progress-to-2026-11-01.md); planning/ 352 -> 46 entries (302 archived; 8 gitignored diffs deleted); the plan's 'How to use' 8,519 -> 508 bytes, section 6 15,852 -> 9,190; R12-R17 merged into one current ruling; contracts and environment facts updated. A ledger line briefly overwritten during the move, restored word for word (494d99f). Controller: wrote the two lean rulings (one paper file per piece; infrastructure frozen) into the current ruling; fixed the moved handover's path in the specification (line 1311) and ADR 0008 (path only); ADR 0015's mentions of task-6dB-fix-round files are names in a record, left; make check exit 0. task-10-brief.md to regenerate at 10B's dispatch.
Task 7f second half: implementer DONE — wt-7f e7b0916, ac16d6e (rebased onto 5b56005): option pack 0.4.0 published, SHA-256 d005713b…01b3c8 (0.3.0 stays byte-identical, ADR 0011: a review is a new version); 62 of 129 records reviewed, 67 proposed, none left out; Q75, Q95, Q104, Q110, Q115 applied with spans and the PO's answer named; funding:F04 proposed (Q101 undecided); C12 UCAS class other with one short quote (the PO's rights decision), body not kept; new optional Offering.source_ids (ADR 0011 amendment; earlier versions byte-identical). make check exit 0 (2,182 / Vitest 472). Gap: 0.4.0 has no capability reference (the capability model pins 0.2.0). Disclosed: one scripted edit. Controller check: 0.1.0-0.3.0 unchanged; the corrected values present in 0.4.0; reviewed count 62/129. Integrate after acceptance run 10 (backend 466 passed; Playwright running). Hand-off to Task 12b: pin 0.4.0.
Acceptance run 10 (after 51c03eb: the conversation lost-input fix, draft-checklist readiness): pytest 466 passed; Storybook passed; Playwright 61 passed, 1 failed (world.spec.ts:204 WLD-05: data-motion stayed "still" after resuming; passed in runs 8 and 9); a focused re-run passed (R16: a flaky failure re-run once). Final-review list: the still-world journey is timing-sensitive under full-suite load (also seen in 6d C's run 1).
Acceptance: green on this Linux host as of run 10 (+ the one flaky re-run): the first full pass in the cloud container.
Task 7f: complete — second half integrated (rebased onto 4a05371; make check exit 0, 2,182 / Vitest 472; fast-forward to 932cfc1). Option pack 0.4.0 is the reviewed school-leaver version. Task 12bA (Options backend): dispatched (opus), worktree /home/user/careerwright-wt/12b (wt-12b from 4a05371), task-12bA-dispatch.md -> task-12bA-report.md; pins 0.4.0; the capability-reference gap for 0.4.0 to settle honestly or stop.
Task 12bA: implementer DONE_WITH_CONCERNS — wt-12b d9dbf8e..79bce14 (rebased onto b22194a): checkpoint facts and commands, pack 0.4.0 pinned (reference 0.2.0 carried unchanged, identity checked in code), focused integration (checkpoint, options, inputs, capability, skills, route solves with a real worker, migrations, targets) green under the lock; make check exit 0 (2,202 / Vitest 472). Concerns: the pin changes the pack label everywhere and adds the T Level option to bookkeeping; tests mostly written after the code (disclosed); P01 with figures supplied still unresolved without evidence (acceptance tests use synthetic evidence, as 13b's). Review dispatched (opus), appended to task-12bA-report.md (one paper file per piece).
Task 12bA review: needs fixes — 0 Critical / 1 Important / 6 Minor. I1 truth: a supplied cost turns a stated instalment plan into one first-month payment keeping its 'instalments' name (C04 'from £69.52/month' + supplied £3,336.72 -> one £3,336.72 payment, can falsely break the payment cap), and the supplied-figure label is set on the whole offering (C04's page-stated £2,995 pay-in-full route marked as resting on the person's figure); figures.py:178-184, compiler.py:383, figures.py:144. Review appended to task-12bA-report.md. Fix round: fresh implementer (original ~436k), wt-12b.
Task 12bA fix round 1: implementer DONE — 5dd0534 (rebased; earlier commits replayed 2f40790..d0a9709): a supplied cost fills only what a plan leaves unstated in its own shape; a stated schedule or a figure below the stated cost refused at the write (stated_schedule, below_stated_cost) or left unknown if stored; PaymentPlan.supplied_cost marks the filled plan, so only routes on it rest on the figure (C04's £2,995 pay-in-full no longer does); ADR 0013; client regenerated. RED then GREEN (C04 on 0.4.0, C10, the checker case); oracle examples; focused integration 26 passed. Changed expectation: C01's supplied cost asserted on the plan. Controller check: diff read (figures.py); make check on 5dd0534.
Acceptance run 11 (5dd0534, Task 12bA in): pytest 471 passed; Storybook passed; Playwright 61 passed, 1 failed (world.spec.ts:625 WLD-03 at 768x1024: the reduced-motion view lacked one of three long target names; passed in runs 9 and 10); a focused re-run passed 3/3 (R16). Final-review list: the world journeys (WLD-03 names, WLD-05 still) are timing-sensitive under full-suite load — two different ones in two runs; worth one hardening pass (wait for every target's name before comparing) before release.
Task 12bA: complete (one fix round, controller-checked, acceptance green with one flaky re-run). Screens half 12bB waits for session W2.
Dispatched (2026-11-02): Task 14A (Routes backend; opus; worktree /home/user/careerwright-wt/14a; task-14A-dispatch.md; the four planning-model gaps modelled or proposed as deferrals for the PO's yes, never recorded approved); the world-journey hardening (opus; main tree; test races in world.spec.ts:204 and :625; product fix if a real drop).
World-journey hardening: implementer DONE — 876be10: WLD-05 was a product bug (a resume click could be lost: a frame within ~1.3 ms of waking snapped motion to zero and stopped the loop; World.tsx now snaps only while settling; a Vitest reproducer RED first); WLD-03 a test race (names compared while the chapter still loaded; open() waits for loading to end and every target's name; comparison unchanged); one check added (aria-pressed false after the second click); 5/5 green under the lock; make check exit 0 (2,205 / Vitest 473). Same heading-only wait remains in 'names sit clear' (not flaked; final-review list).
Task 14A: implementer DONE_WITH_CONCERNS — wt-14a 85ce831, 150c2cc, bd4aaf2 (rebased onto f5356e3): Routes facts from real solver output (comparison, paged archive, chosen route), solve stage checks; make check exit 0 (2,229 / Vitest 473); focused integration 44+2 green after a test fix. Rulings to check: solves without limits or an economic solve without a baseline refused up front (was: unresolved); 'longer than the model' leads when nothing fits only because an option exceeds 24 months; the worker stores the solve's monthly input (older solves refused as out of date); scenario ranges only for a chosen route; the old solve endpoint still serves the whole result. Three proposed L0 deferrals for the PO (PLN-01 information-gathering/waiting actions; OPTN-04 search-and-review before an offer; OUT1-08 experience beyond a course's outcomes); PLN-04 modelled as a milestone. Disclosed: one sed edit. Review dispatched (opus), appended to task-14A-report.md.
Task 14A review: needs fixes — 0 Critical / 1 Important / 8 Minor. I1 truth: 'longer than the model' leads whenever a complete search finds no route and any option exceeds 24 months, nulling the no-route code (reproduced: a two-month course over the spending cap beside a 36-month degree hides the no-route and the breach; same with a starting breach); comparison.py:651, :532. Fix round sent to the original implementer (resumed a8603641204743dfc, ~362k).
Task 14A fix round 1: implementer DONE — aa807b9 (rebased onto d3b4601): 'longer than the model' leads only when length is the whole reason (no starting breach, no option set aside for a breach, nothing checked not feasible, no subtree pruned for a breach); otherwise no-route leads with its violations and the long options beside it; ADR 0016 decision 25; the reviewer's case and the starting-breach case RED then GREEN. Controller check: diff read (_only_length), make check on aa807b9 exit 0 (2,231 / Vitest 473). INTEGRATED: fast-forward to aa807b9. Acceptance run 12 next. Three proposed deferrals (PLN-01, OPTN-04, OUT1-08) await the PO.
Acceptance run 12 (aa807b9: Task 14A in, the world fixes in): exit 0 — pytest 472 passed; Storybook build passed; Playwright 62 passed, 0 failed. The first fully clean acceptance on this Linux host, no re-runs. Task 14A: complete.
Back on the Mac (2026-11-02): contracts, Environment facts and controller state name the Mac's paths again (b6515c7); memory already matched planning/claude-memory; make setup exit 0 (datasets present and hash-verified, images built).
Acceptance run 13 (the Mac, Docker Desktop, on b6515c7): exit 0 — pytest 472 passed; Storybook build passed; Playwright 62 passed, 0 failed. The containers' root-start-then-drop-privileges change (ADR 0004 amendment) works on Docker Desktop. Owed check done: Sam's title is on no list against the full ESCO release and the UK index (test_evaluation.py, in this run; its fixture fails without the datasets, so it ran).
PO answers (2026-11-02): yes to all three proposed L0 deferrals — PLN-01 (finding things out and waiting as actions), OPTN-04 (job search and review before an offer), OUT1-08 (experience beyond an offering's stated outcomes). Recorded: plan section 1's L0 deferrals, ADR 0016, register rows PLN-01, PLN-04, OPTN-04, OUT1-08, VIS2-08.
Demo video (docs/demo/demo-video-script.md, handover section 7) checked against the plan (2026-11-02): Options/Routes needs (loan to repay, a named missing fact with a box, time-cost chart, monthly table) are already in Tasks 12b and 14's cards; the closing shot is the Plan place (design README: "the chosen path made solid, the next move glowing at its start"), Task 15, not Task M (M adds only the committing animation); the script's "first gate lit" should read as the next step glowing (a lit gate could read as a passed condition). "Research this role" for Maya: add a no-list title as a Target role (e.g. "Biodiversity net gain officer", checked on no list). Sam's limit: the interview may propose minimum_salary only as a figure he states.
PO answer (2026-11-02): yes, Skills also reads "if you get your grades" beside a requirement the person expects to meet — added to Task 10's card and acceptance.
Session W2 live notes (PO, Maya to step 14 of the rehearsal): "not the best experience"; UI cluttered and didn't always flow logically; Maya's dislike of accounting was not saved to What we know (no field holds a dislike?); two synonyms for running a Brownie group offered as two facts to save (duplicate proposals); Muse's next question interrupted the scripted messages (the demo script must say "answer Muse's question, then add…").
Session W2 live notes (PO, Maya step 17): added 3 roles as targets, found no way to remove any; What we know's text overlaps; "The UI is broken."
Finding (controller, from the PO's step 17): targets are capped at 3 (MAX_TARGETS, profile/document.py:41) and the PO found no way to remove one, so a person who has made 3 suggestions targets cannot add a no-list title to reach "Research this role" — the dead end the handover's section 7 asked to check. Maya's steps 18–19 skipped; research rehearsed on Sam's title instead.
Session W2 live notes (PO, Sam): ESCO job suggestions too hard to read (title and description not easy to tell apart); after 'Client onboarding assistant' + 'Use my own words', the pay-cut message got no pounds question: Muse asked 'Do you already have a target role in mind, or would you like to explore options first?'; PO: 'Cannot continue testing.' Session stopped there (Maya to step 17, Sam to step 6; Jo not played).
Session W2 live notes (PO, after stopping): the role lights on the right-hand side (the world) can't be interacted with; would like click or right-click to see a summary of the role or remove it.
Session W2 investigated (two read-only agents; controller spot-checked Conversation.tsx:408, the .fact grid, and viewed the overlap screenshot): planning/session-w2-findings.md (10 findings with causes, fixes and sizes).
PO answers (2026-11-02): yes, fix the You chapter first (Task W2F, card added; 10B, 12bB and 14B wait for it and a short re-test); yes, a "Tasks you don't enjoy" answer (schema change); clickable world role names: yes, after the three screens.
Dispatched (2026-11-02): Task W2F slices A (worktree w2fa, Muse's turns), B (worktree w2fb, the conversation), C (main tree, What we know/targets/suggestions); task-W2F-{A,B,C}-dispatch.md.
Task W2F slice B: implementer DONE_WITH_CONCERNS — wt-w2fb a0917e7, e9b930a (rebased onto 223ce63): Send waits for the start choice and for a waiting card; card shows adds/removes and task hints; Save in the first screen at 1280x800 and 390x844; Meta key moved to the account menu. make check green (Vitest 483, backend 2118). Concerns: phone Save bar may cover the first Accept with long content; a shell heredoc used for two code blocks; slice A's new field's card hint is one line once A lands. Review dispatched.
Task W2F slice C: implementer DONE_WITH_CONCERNS — main tree 223ce63, cb3dca5, 941a03e: no label over its value (long-values visual state), Remove beside each target with Undo, removing or restoring a target leaves suggestions current (stays_current), Save in reach, suggestion card title/description/kind of work apart; ruling: removing the last target leaves target roles Unknown (ADR 0007). make check green (backend 2118, Vitest 481); focused integration 2 passed under the lock; Storybook spec 3 passed. Not run: acceptance (new e2e/what-we-know.spec.ts, visual you--what-we-know-long). Found, not fixed: the qualification box cuts off 'Expected: taking it, or waiting for results' at 390 and 1440 (final-review list). Slice A told: exclude the new answer from stays_current; round-trip it through inputFrom. Review dispatched.
Task W2F slice A: implementer DONE_WITH_CONCERNS — wt-w2fa b888737..1e8ac12 (rebased onto 50e01b2): disliked_tasks (schema v5, migration 0046), interview-turn-6, INT-18/INT-19 and INT-16's same-wording check, ADR 0006 amendment; the controller's two items (stays_current excludes it; inputFrom round-trips it) with RED-first tests. make check exit 0 (pytest 2137, Vitest 484); focused integration 71, 5, 54 passed under the lock. Concerns: prompt instructions 4,238 bytes vs the 4,250 guard; pre-existing: a full profile overflows the 8,500-byte prompt budget (12,327 measured; +~1,000 now) — final-review list; a list's last item can't be taken back by a proposal; INT-19 live-only (suggested capped make live-eval CASES=INT-16,INT-18,INT-19, worst case $0.0105); one early scripted test edit. Card hint for the new field: controller adds after B and A land. Review dispatched.
Task W2F slice C review: needs fixes — 0 Critical / 1 Important / 9 Minor. I1: the answer form's sticky Save bar hides keyboard focus (WCAG 2.2 2.4.11, Global Constraint 11; 8/4/7 controls at 1440/768/390), globals.css:1619-1628, ProfileEditor.tsx:335-337 — a regression this piece introduced, so fixed in its one fix round (controller's call). stays_current, Remove/Undo and 'Unknown' after the last target judged correct. Fix round sent to the original implementer.
Task W2F slice B review: approve — 0 Critical / 0 Important / 9 Minor (appended to task-W2F-B-report.md). Watch at the re-test: the phone Save bar over the first Accept with a live-length reply; 'Choose how to start, then send' shown at the job-title question. Not done from finding 9 (not in any slice's dispatch, the controller's omission): two places to type at the first question, the purpose line repeated — put to the PO at the re-test (session W2's S4 asks the first).
Task W2F slice C fix round 1: implementer DONE — 81cbbc1: the form measures its Save bar (ResizeObserver -> --form-save-height) and html scroll-padding keeps it clear (plus the sheet's peek when open); Storybook spec tabs the open form at 1440/768/390, RED first (13 covered), GREEN 3 runs; make check green. Controller check: diff read (globals.css, ProfileEditor.tsx; the drawer rule outranks by specificity). Slice C complete pending acceptance.
Task W2F slice B: INTEGRATED — rebased onto 1480a71 (89c88a1, 624151b), make check exit 0 in the worktree (backend 2118, Vitest 491), fast-forward. Slice A review: needs fixes — 0 Critical / 1 Important / 5 Minor. I1 safety: the demo interviewer proposes distress words as a dislike on a support turn (fixture_interviewer.py:92-95, 380-392). Migration, client drift, stays-out-of-suggestions and the prompt's rules judged correct; the 8,500-byte budget refusal is pre-existing (Minor 1, final-review list). Fix round sent to the original implementer, with the rebase and the card hint (CARD_HINTED).
Task W2F slice A fix round 1: implementer DONE — bf3dce0 (check_turn drops any change whose value or reason trips the support screen, on every turn; the live path had no such guard before — pre-existing safety defect, fixed; the demo interviewer the same), 5c9b30e (CARD_HINTED gets the new answer), d26d014 (PROF-09); test_origin's support-turn test relied on the defect, sentence changed (justified). Controller check: diff read (interview.py check_turn). INTEGRATED: fast-forward to d26d014; make check in the main tree exit 0 (pytest 2139, Vitest 494). Live check: make live-eval CASES=INT-19 on the test model — complete, 0 failures, leak scan clean, ledger row 55 (the live-eval scope had 2 calls left of 9, so INT-16 and INT-18 not run live). Acceptance run 14 started.
Acceptance run 14 (on 79a41d2, Task W2F A+B+C in): pytest 475 passed; Storybook passed; Playwright 68 passed, 1 failed — visual 390x844: you--what-we-know-long overflowed by 159 px. Cause: pre-existing — 'Add seniority or industry for <title>' (a .btn, white-space: nowrap) never wrapped; the new long-values state is the first with titles that long. Controller fix 048f983: .title-details-opener .btn wraps. The failing test re-run alone under the lock: passed; make check exit 0 (Vitest 494). Full suite not re-run yet: next acceptance after the PO's re-test.
Re-test part 1 (PO, 3 November 2026, the old Maya workspace): "All worked" (no overlap, Remove with Undo, Save in reach, suggestions readable, research ran). PO: actions like "Remove" and "Add another target role" must be a different colour to information text, "Fix this now" — controller: .btn-quiet and .btn-icon now take --action (teal; underline kept; the primary stays the only teal fill; teal text on every surface is already a measured pair); make check exit 0; Storybook accessibility spec running. PO: "you seem to lack a coherent, consistent design system" — a design system pass with the frontend-design skill, after every chapter module is built, before Task M (controller-state.md).
Research this role, "Biodiversity net gain officer" (PO's live run): not yet found — all five pages read were the sites' home pages (acquisition_targets: https://studentjob.co.uk/, jobs24.co.uk/, environmentjob.co.uk/, sercanto.co.uk/, recruitmenthub.solutions/), so no page could show the title. check_url keeps paths, so the search's own candidates were bare home pages. Constraints: one search request, search context "low", at most 2 tool calls, 8 candidates, 5 pages read (ADR 0009 decision 12), exact title on two independent sources.
PO answer (3 November 2026): widen role research — deeper search, up to 8 pages, no home pages; the found rule unchanged. PO asked how sites are found, and to use a Brave web search if we aren't searching: we are (Meta's own web search tool through Muse, ADR 0003); Brave would be a new provider, not proposed unless the wider Meta search still fails. Task W2F slice D dispatched (main tree, task-W2F-D-dispatch.md). Teal actions committed (8185dda), Storybook accessibility spec 4 passed; images rebuilt and the session restarted with them.
PO (3 November 2026): 'Up to 20 pages. We need to do this properly. Landing on the home page is useless. We need to use Meta web search more effectively.' Sent to slice D: 20 pages, ~30 candidates, up to 8 search calls with directed queries, specific page addresses grounded in the search's own sources, never a root, search-results or listing page; reservation from the registry.
Slice D finding: Meta's search sources are full page addresses (ledger: 21 sources across 9 hosts), but 0 of 5 and 0 of 8 role candidates matched one — Muse's candidates were not the pages its search returned; the code read ungrounded candidates. Fix: read only grounded candidates when any exist. PO answer (3 November 2026): yes, raise the caps for the wider search — session run cap $0.75 -> $1.60, default run limit $0.15 -> $0.50; $5/month per workspace unchanged (worst case on Wonder $0.502 an attempt with 8 tool calls).
