# Session W2 (2 November 2026, stopped early): findings and causes

The product owner played Maya (to step 17 of the rehearsal) and Sam (to step 6), live on Muse
Wonder, and stopped: "Cannot continue testing." Causes from two read-only investigations
(controller-dispatched, 2 November), spot-checked by the controller. Sizes are agent hours.

## Bugs
1. **What we know's text overlaps** (reproduced in Storybook at 390 and 1280 px; controller
   viewed the screenshot). `.fact` uses `minmax(0, 1fr) minmax(0, auto)`
   (`apps/web/src/app/globals.css:1597-1604`): a long value takes the row and the label column
   shrinks to 0. Fix: give the label column a floor, e.g. `minmax(min(8rem, 40%), 1fr)`
   (verified by injection); add a long-values state to the visual spec, whose overprint check
   (`e2e/visual.spec.ts:826-917`) only sees short fixture values. ~1 h.
2. **No visible way to remove a target** (3 is the cap, `profile/document.py:41`). A path
   exists but is buried: Edit answers directly → Remove (`fields.tsx:315-324`, only with 2+
   items) → Save changes ~3,400 px down (`ProfileEditor.tsx:335-343`). The card's full-targets
   line names no place (`Directions.tsx:441-447`). No remove command: a `PUT /profile` that
   changes targets marks the slate as on earlier answers, so "Suggest again" (paid) becomes
   the bright action (`exploration.py:258-272`). Fix: a Remove beside each target (a short
   "Your targets" list in What we know, and the card's saved box) through the existing save,
   with Undo; keep the slate current when only a target is removed (backend rule). 3.5–6 h.
3. **The start choice disappears for good once a message is sent** (`Conversation.tsx:408`:
   `entryNeeded` needs `turns.length === 0`); Send is never blocked (`YouChapter.tsx:231-238`).
   Sam's turn went out with no choice, so Muse asked the choice itself. Also a lost-input
   path: a message sent while a review card waits replaces that card, and nothing from it is
   saved (`lib/conversation.ts:149-165`). Fix: Send waits for the start choice and for the
   card to be saved or "Keep none". 1–2 h.

## Muse's turns (prompt and review card)
4. **Dislikes have nowhere to go.** No profile field holds one (`profile/interview.py:95-111`),
   yet the explore prompt asks what is "draining" (`interview.py:511`); the spec lists
   "disliked tasks" (`Careerwright_Product_Specification.md:222`). Fix (schema change, needs
   the PO's yes): a `disliked_tasks` list field that informs and never searches or filters
   (kept out of discovery's field set, `profile/discovery.py:47-53`); schema 5, a migration,
   prompt `interview-turn-6`, labels, client. 4–6 h.
5. **One activity offered twice** (Brownies as "done" and as "enjoyed", most likely): nothing
   compares fields or synonyms (`interview.py:409-411`, `document.py:418-422`); the tray hides
   the field hints that tell them apart (`ReviewTray.tsx:211-213`). Fix: one prompt line (the
   same words in each field) and the three task fields' hints in the tray. 1–1.5 h.
6. **A taken-back fact can stay**: a list proposal is the whole list and replaces the saved one
   (`interview.py:490-491`, `document.py:446-454`), but the model decides what "still applies"
   and never sees rejections; the tray doesn't show removals (`lib/profile.ts:52-55`). Fix:
   the tray shows "adds / removes" against what is saved; one prompt line. 2–2.5 h.
7. **A hinted money limit isn't asked for in pounds next**: no prompt rule ranks it
   (`interview.py:480-481`, `508-511`; spec line 236 puts practical limits first). Fix: one
   prompt line. ~1 h with item 5's and 6's lines, plus one capped live check.

## Clutter and readability
8. **Suggestion title and description hard to tell apart**: "Kind of work: {ISCO group}" reads
   as a second title (`Directions.tsx:423`); the ESCO description has no heading and sits as
   14 px text after the action row (`Directions.tsx:470`). Fix: a "What the work is" heading
   or a 16 px lead line under the title; move or relabel "Kind of work". 1–2 h.
9. **Clutter**: two places to type at the first question; the purpose line repeated; the Meta
   key card under every conversation (`YouChapter.tsx:367-376`); the tray's Save off the first
   screen with 3+ changes (y≈838); the form's Save ~3,400 px down; an open suggestion card
   ~900 px tall. Fix: keep Save in view, move the key card out of the conversation. 3–4 h.

## A new request
10. **World role lights can't be clicked** (verified: names are `pointer-events: none` under
    `.app`, `globals.css:140-147`, `World.tsx:744-762`). The PO would like click or right-click
    to see a summary or remove. Smallest correct way: destination names as buttons on a layer
    above `.app`, opening What we know at that target (with item 2's Remove); keyboard reach;
    no right-click menu (no keyboard equivalent). 5–7 h, after item 2.

## The rehearsal and demo script
- Sam's steps (in the package and the controller's rehearsal) lacked "choose how to start".
- The script must say: save the review card (or Keep none), answer Muse's question, then add.
- The demo shows Sam's money limit in the same reply as Muse's question; it can appear only
  after he gives a figure (`docs/demo/demo-video-script.md:146-148`).
- Not verified: today's sealed Muse outputs (which fields held the two Brownie wordings).
