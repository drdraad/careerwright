# Task 6d slice B fix round 1, scoped re-review, half B (`app`)

Reviewed: 81c3695..667426e (2e05426 to 30c1606 code, captures and ADRs; 667426e the register).
I read the backend half of `review-81c3695..667426e.diff` in full, the backend tests in full,
the ADR lines, and the "Fix round 1" part of the report (unverified claims). I ran no suite.
Outside the diff, at 667426e, I made one check per named risk:
- every caller of `commit_profile_version` now passes `pack` (otherwise a role change would
  hit its INTERNAL_ERROR);
- every reader of the role goes through `role_record`;
- 0034's existing CHECKs, against what 0038 adds;
- the API access log records the path only, never the query string (`api/guard.py:130`),
  since the type-ahead is now a support-screen input.

### Spec Compliance
- ✅ Every item in my half is addressed. Two new Minors below.

| Item | Status | Where |
|---|---|---|
| A-I1: the record is the role's one truth (fix item 4) | **Addressed** | `targets.py:271` `role_record` reads the stored record; with none it decides as it would store, using the role's own choice. `titles.py:52,58`: the role comes only from its record. `commands.py:163,173`: every change of the role stores it through `record_role` (`targets.py:287`). A decision replaces the record of that title; any other change keeps it (`:305`). `choose_role` (`exploration.py:1409`), `choose_closest` (`:1631`) and the refusal (`:1486`) pass their decision. Test: `test_role_space.py:373` (closest choice, then capitals, away and back in What we know: state, occupation, `closest.chosen`, `chosen` and the usual skills agree; a target with the same title names the choice). |
| A-M1: `kind` for an ESCO other title (in item 4) | **Addressed** | `exploration.py:1409`; test `test_role_space.py:433` (`kind: esco`, the record cites the choice). |
| A-M5 with design I-2: the refusal as a versioned command (item 2) | **Addressed** | `NameRole.none_of_these` (`exploration.py:1423`) goes through `run_idempotent` with its expected version and Idempotency-Key. The same answer again is 200 (`:1467`). `choose_closest` now always makes a profile version (`:1631`). After a refusal the role's fact is `title_kept_as_own`, otherwise `role_not_matched` (`:921`); neither asks for another job. Tests: `test_role_space.py:209` (stale 409, 201, 200, a later refusal is a new version) and `:250` (a stale tab conflicts); `test_discovery.py` (the slate after the refusal). |
| A-M4: the CHECKs (item 5) | **Addressed, with an accepted departure** (below) | `r0038_record_checks.py`; test `test_role_space.py:469` refuses each case on its named constraint. |
| A-M2: refusals without the index (item 6) | **Addressed** | `test_reference_data.py:278`: the type-ahead, "Use my own words" and a role typed in What we know each answer 503 `REFERENCE_DATA_UNAVAILABLE`, and the offline slate raises that code. |
| A-M6 and A-M7: words (item 7) | **Addressed** | ADR 0015 records the four known limits (concept key against exact spelling; "&" and accent twins; own-words records on a database that got the index later; `lower()` against `casefold()`). ADR 0012 records the importance edits on re-decided rows, and A-M3's named fields as a policy question. |
| A-M8: tests (item 8) | **Addressed** | The same-titled target: inside `test_role_space.py:373`. Punctuation only: `:270` ("--" kept, empty concept key). The failure path: `tests/eval/test_evaluation.py:233` (a wrong, an extra and a missing reason each fail). |

- **The departure: 0038 allows "None of these is my job" on the person's own words too.**
  **Accepted.**
  - My M-4 said "only on an ONS title" because at that time only the closest step could record
    a refusal, and it asks only for ONS titles.
  - Fix item 2 now records the type-ahead's refusal, and the partial list it belongs to appears
    only when no title holds every typed word, so that title is almost always own words.
  - A CHECK limited to ONS titles would refuse item 2's own writes. As written, the CHECK
    repeats the rule as it now stands: never on an ESCO title, always with `recorded_by`. No
    code path can produce an ESCO-kind refusal, because `decide` makes a record ESCO only with
    a non-closest choice, and a refusal passes none.
- **Migration 0038**:
  - It is forward-only (`downgrade` raises) and changes nothing outside the target-records
    table.
  - It is safe at 0037, and no existing row is refused. Every ONS record got its codes from the
    index: `resolve_target` and 0036 both take them from `array_agg` over entries whose codes
    are `NOT NULL`. Every refusal stored before was written by `name_role` or `choose_closest`
    with the actor's ID. The paths that store with no actor (the seed and `record_targets`)
    never write a refusal, and the demo reset deletes its workspace's records first.
  - Its two CHECKs repeat the domain rules, and the test fires each one by name.
- **The refusal is a versioned command**: expected version, `Idempotency-Key`, a stale request
  refused 409, a replay 200. This is tested for both places it is offered.
- ⚠️ Cannot verify from the diff:
  - the implementer's `make check` and `make acceptance` runs, and the RED runs;
  - that 0038 applies on a populated database: there is no test that upgrades data through 0038.
    I argued above, from what wrote the rows, that it does.

### Strengths
- I-1 is fixed at its cause, not patched. The role is now read exactly like a target, from one
  record, and every write path stores it through the one write path. The test checks what the
  person would see after the edits that broke it (the origin, the skills, a same-titled target).
- A role saved before records existed is handled without a migration: `role_record` decides it
  as it would be stored, from the role's own choice.
- The support screen on the first question keeps nothing:
  - the panel comes with every refusal, a stale one included;
  - the test proves there is no version, source, record or receipt;
  - the type-ahead's words never reach the access log, which records the path only.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
- **N-M1. A role chosen from ESCO before this round can be overridden by another record of the
  same title.** (`targets.py:282`)
  - `role_record` returns any stored record for the title as a concept before it looks at the
    role's own choice.
  - Before this round, `choose_role` stored no record. So if a record already existed for that
    title (an own-words answer of the same title, or a target with the same title that ESCO
    holds several times), that record now decides the role. An ambiguous "bookkeeper" target
    would make a role the person chose as one bookkeeper ambiguous again.
  - It is reachable only on data saved before this round, and the start answers once, so it is
    unlikely outside development and demo databases.
  - Fix: either record it as a known limit in ADR 0015's line, or add a forward migration that
    stores a record for each current role whose source cites a choice and whose record names no
    ESCO occupation.
- **N-M2. The conversation's change of the role isn't tested.** The fix list names "What we know
  or the conversation", and the test drives only What we know. Both go through
  `commit_profile_version`, so the risk is low. One decision on a role proposal, checked with
  the same `seeded` assertions, would close it.
- Note for half A: the screened type-ahead response still returns the typed words in `query`
  (`catalogue_schemas.py`, `TitleMatchesOut.screened`). They are never stored or logged, but
  the web must never show them.

### Assessment
**Task quality:** Approved
**Reasoning:** Every item in my half is addressed with a test that would fail without its fix.
0038 is safe and its own-words departure is right. The two new Minors are a data-before-this-
round edge case and one untested path through the same write path, and both can wait for the
final review.
