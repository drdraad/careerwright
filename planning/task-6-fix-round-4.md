# Task 6 — fix round 4 (FIX_BASE 6b1d3b9): support screen redesign

## Why this round changes the design
Rounds 1–3 tried to classify intent with hand-written patterns (a blocking tier for
first-person intent, a note tier for the rest). Each round traded false positives for
false negatives: the latest re-review (task-6-rereview-3.md) found shapes that now reach no
tier at all (Critical C-1), tier-1 blocking on career text (N-I1) and more no-tier shapes
(N-I2). Two failed fixes in one direction mean the hypothesis is wrong: precise intent
classification by pattern is not achievable here. Controller ruling: remove the intent
classifier.

## Required design (spec §4 line ~291; plan S2.6 "minimal reviewed response policy for
## explicit acute distress … separate from career suitability")
1. One deterministic, recall-first screen: any listed risk stem, in any inflection,
   contracted or uncontracted negation, any person or tense, triggers the support flow.
   Nothing containing a listed stem may pass unflagged. No blocking tier, no attempt to
   decide intent.
2. The support flow: a calm, non-diagnostic support panel with current UK resources
   (keep the reviewed resource list already in `profile/safety.py`), announced through a
   polite live region, dismissible, focus not stolen, shown beside the conversation. The
   person's message proceeds normally (no hold, no extra click).
3. For that turn only, the interview prompt receives a fixed instruction: acknowledge
   briefly, offer a smaller next step, ask no career question this turn (spec §4 line
   ~291). The model never sees a label naming the screen or the matched stem.
4. Separate from career suitability: the flag never reaches the profile, proposals,
   discovery, the slate, exports or logs; receipts store no support text (recompute on
   replay, as now).
5. Remove the code, tests, ADR text and register claims for the old tier 1, and the
   "send anyway" path if it only served tier 1.
6. Tests: one table — every stem × inflection/negation/tense row → flow; ordinary career
   messages with no stem (the reviewers' career examples: lifeguard, lifelong, life
   sciences, life savings, workplace cuts, "without meetings", etc.) → no flow unless they
   contain a stem; a stem inside career phrasing → flow (accepted false positive, listed
   in H-12). Plus: the prompt instruction is added only on flagged turns; the flag reaches
   no stored record; the panel is announced and dismissible. Build test inputs from the
   reviewers' descriptions and the existing stems; keep any new example text minimal and
   clinical.
7. Replaying a receipt stored by the round-2 code must not 500 (read old receipts
   tolerantly, or migrate them), with a test.
8. ADR 0007: record the redesign and why (provisional, H-12). H-12 checklist lists the
   known limits: finite English stem list, false positives show the panel, no intent
   judgement.
