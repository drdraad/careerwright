# Task 6d slice B fix round 2, scoped re-review, half B (`app`)

Reviewed: 667426e..51ca593 (aa0e66e, 64c958e and adc3080 hold the code and tests; 4590743 the
review shots; 4bac1c6 the ADRs; 071ea61 the captures; 51ca593 the register). I read the
backend half of `review-667426e..51ca593.diff` in full and the backend tests in full. I also
read the "Fix round 2" section of the report, as unverified claims. I ran no suite.

Outside the diff, at 51ca593, I made one check per named risk:
- `ProfileInput`'s value types, to see whether any free text escapes the What we know screen;
- `store.profile_version`, the base version the screen compares against, which runs in the
  actor's transaction and is therefore limited by row-level security;
- `_invalid`'s error details, to see whether a refusal can echo input;
- the conversation's typed edits (`conversation.py`);
- that the reused risk-word input already existed before this round
  (`test_interview_choices.py:265` at 667426e).

No distress text was written for this review.

### Spec Compliance
- ✅ Every item in my half is addressed.

| Item | Status | Where |
|---|---|---|
| 5: the screened type-ahead returns no typed words | **Addressed** | `catalogue_schemas.py:240` (`query` may be null) and `:283` (null when screened); the route `routes_taxonomy.py` no longer passes the words. Test: `test_role_space.py:184` checks `query` is null, and that the fixture's words appear nowhere in the body. |
| 5: no other new response echoes input | **Holds** | Below the table. |
| 4: What we know's direct entries screened (`support-policy-9`) | **Addressed** | Below the table. |
| 3: a screened title kept by the person's choice | **Addressed** | `NameRole.keep_as_typed` (`exploration.py:1430`). `:1465` refuses a screened title only when the flag is off. With it, the title goes through the same `name_role` command: expected version, `Idempotency-Key`, a direct-entry source and the role's record. Test: `test_role_space.py:218` (refused 422 with the panel; a stale keep 409 with the panel; kept 201 at version 1, exactly as typed; again 200; own words; one source of kind `direct_entry`; no receipt holds a support note). |
| 9: the conversation's change of the role | **Addressed** | `test_origin.py:413`: a demo workspace, "Registered nurse", closest "specialist nurse", then the demo interviewer's proposal "Registered Nurse" decided. The test checks version 3, `esco`, chosen, `ons`, the chosen occupation and the usual skills. The RED run (with the keep path disabled) is reported, not seen by me. |

**Item 5: no other new response echoes request input.**
- The new refusals (`ProfileRefusedOut`, `TitleRefusedOut`) carry the existing error body,
  whose message and details are fixed strings (`document.py:298`), plus the fixed panel.
- The two successes, `ProfileSavedOut` and the kept title's `ProfileOut`, return the saved
  profile. That is the resource itself, as every profile write already did, not request input
  echoed back.

**Item 4: What we know's direct entries screened.**
- **Where the screen runs:** `routes_profile.py:79-80` screens the edit's new entries, using
  `commands.entered_words` (`commands.py:212`), before anything can refuse the edit.
- **The entry is still saved:** `run_idempotent` runs unchanged, and the panel is added only to
  the answer (`:114`) or to a refusal (`:106`).
- **Recomputed every time, never stored:** the receipt keeps the plain `ProfileOut`, so a replay
  computes the same panel again.
- **Nothing used for suitability:** the support flag never reaches `write_profile`.
- **The policy is updated:** `safety.py` has `support-policy-9`, a review status that names both
  new screens as not yet reviewed as built, and two new lines. ADR 0007 has its amendment line.
- **The test:** `test_workspaces_and_profiles.py:168` covers the save (201 with the panel), the
  replay (the same panel), the same words beside another change (no panel), a stale save (409
  with the "not saved" panel), and both receipts free of the panel.

**Item 4: can an edit slip a risk word past "only the entries a save adds"?**
- **Not a newly typed one.**
  - Every free-text field is a `str` or a `list[str]` (`ProfileInput`). The others (hours,
    money, the salary floor) hold no words.
  - A changed string is screened, and so is every list item not already in the same field of
    the version the edit was made against. An edited item is a new string, so it is screened. A
    word moved to another field is new there, so it is screened.
  - If that version can't be read (version 0, or not visible), every entry is screened.
  - The base version is read under row-level security, so another workspace's words can never
    be compared against. Nobody can use the panel to learn what someone else's profile holds.
  - The base version never changes, so a replay gives the same answer.
- **What the design leaves unscreened, by choice (ADR 0007's line says so):** words already
  saved in that field and re-saved unchanged. Those came in before policy 9, from the fixture,
  from an undo, or from the conversation's typed edits (see the Minor below).
- **Per-entry screening:** each entry is screened on its own, so a listed construction split
  across two list items isn't joined. That matches splitting it across two messages. It is a
  known form of the rule, not a slip.

- ⚠️ Cannot verify from the diff:
  - the implementer's `make check` and `make acceptance` runs, and the RED runs;
  - the web half (the panel's placement, the keep button, the phone screen), which is half A's.

### Strengths
- Item 4 reuses the message panel's pattern exactly: screened before anything can refuse,
  added after the receipt, recomputed on replay, never in the receipt. The test checks the
  receipts directly.
- The "new entries only" rule compares against an immutable, access-controlled version. So it
  is stable on replay, and it can't be used to probe another workspace.
- The keep path is the same command and source as "Use my own words", so a screened title the
  person keeps is in every way like any other title they typed.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
- **R2-M1. The conversation's typed edits are direct entries, and they aren't screened**
  (`conversation.py:88-95`, `:392-400`; the decision route screens nothing).
  - When the person types their own answer instead of a proposal, the decision saves it with a
    `DIRECT_ENTRY` source labelled "Direct entry", the same kind as What we know's. A listed
    word typed there is saved with no panel.
  - The product owner's decision names What we know, and the implementer has already raised
    this, so it is a scope question, not a defect here.
  - One-line question for the product owner: "Should answers you type in the conversation's
    review step go through the support screen, as What we know's do?" If yes, the decision
    route screens the edits' words the same way `put_profile` does.

### Assessment
**Task quality:** Approved
**Reasoning:**
- Items 3, 4, 5 and 9 are addressed in the changed code, each with a test that checks what the
  person would see and what is stored.
- No new or edited entry can slip past the What we know screen.
- The only gap is the conversation's typed edits, which the decision didn't cover: a question
  for the product owner.
