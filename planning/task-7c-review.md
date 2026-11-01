# Task 7c review: the reviewed England option pack (fa40db5..3b2fd87)

Reviewer: Task 7c task reviewer, read-only. I read the brief, the controller's dispatch, the
carry-forward note, the report and the diff. I read the diff in passes: tool and tests first,
then the generated pack and reference, then docs, manifest and register. I checked the
generated pack with my own scripts rather than taking it on trust. I ran no test suites and
made no live calls.

### Spec Compliance

- ❌ Issues found:
  - **Misunderstood (controller ruling):** the dispatch says "Where a 'no' or '?' gives no
    value you can cite that way, the field becomes unknown with the review's reason
    recorded" (`task-7c-dispatch.md:35`). The implementer kept the values for all 13 bare
    "?" answers (Q227, Q228, Q230-Q234, Q236-Q239, Q241, Q242) and for Q290. The report
    lists this as a ruling "the brief and dispatch did not settle" (`task-7c-report.md:137`,
    `:147`), but the dispatch does settle it. See Important 1
    (`backend/tools/session_2_pack.py:14-15`; `docs/adr/0011-england-option-pack-format.md:223`).
  - **Misunderstood (correction applied as removal):** Q187 gives the reading and quotes it
    from the same page: "earn below £25,750 or are unemployed", with no period and no gross
    basis. The brief says "a value the reviewer corrected is changed with its span cited".
    Instead the whole earnings rule was removed from `funding:F01.rules`. See Important 2
    (`backend/tools/session_2_pack.py:486-491`).
  - **Extra (justified):** capability reference 0.2.0. `check_reference` refuses any pack
    whose `pack_version` differs from the reference's (`capability/reference.py:157-158`).
    So without 0.2.0, no consumer could load pack 0.2.0. Its rubrics, gates and crosswalks
    are byte-for-byte the same JSON as 0.1.0. Only the version, date, `pack_version`,
    `label_review` and notes differ, and it stays `proposed`.
- ⚠️ Cannot verify from diff:
  - `make check` and `make acceptance` results. I did not re-run them, per the contract.
  - That no live call was made. The diff does not touch `docs/evidence/`, so the usage
    ledger is unchanged.
  - That the D-answers and the T and R answers handed to Tasks 10, 12, 8 and 13a reach those
    tasks. They are listed only in the report; the controller's ledger has to carry them.

**Risk checks (one focused check each):**

1. **Traceability.** I wrote my own parser for `session-2-answers.md` and for the question
   files' record column. Then I recomputed every record's rows: the Q rows, plus the T and R
   rows that name a pack record (minus T28-T31, which are the checker's conclusions). I
   checked all 121 records in 0.2.0, not a sample:
   - Every one of the 55 `reviewed` records has rows that are all yes.
   - Every record named in a "no" or "?" answer is `proposed`.
   - The only record with all-yes rows that is still `proposed` is `option:C05`, because of
     the Q153 extension (Minor 3).
   - Sample records I read in full: `job:J05` (Q1-Q8, product owner, 2026-10-29),
     `job:J12` (Q13-Q17, mixed provenance stated), `req:J05.1`, `req:J12.1`, `req:J20.3`,
     `outcome:C04.1` (Q66, T35, R47), `outcome:C09.2` (Q179, R56), `funding:F03`
     (Q208-Q219), `option:C02`, `offering:C09`, `job:J14`, `job:J19`.
   - The tool's Q-number-to-record mapping (`record_rows`) matches the question file exactly
     (0 differences across 344 rows). The answer counts match the report: Q 295/35/14,
     T 29/7/0, R 32/18/8.
2. **Corrections.** All 7 checked:
   - Four are located in the kept body: `C01.outcome_evidence.4`, `C05.assessment`,
     `F02.published_on` and `F02.rules_updated_on`. I hash-checked each body and found the
     exact excerpt at the stated offsets: count 1, first occurrence.
   - Three sit inside a stored claim's excerpt: `C04.access_period.corrected`,
     `F02.lle_interaction.corrected` and `F02.htq_interaction.corrected`. Each has the same
     span, excerpt and occurrences as the claim it replaces, and the body confirms them
     (count 2 for the F02 pair).
   - F02's "may need" lead-in sits at 5311-5383 in the body, as the claims' notes say.
   - C01's practice sentence comes after the "Communicating and presenting data" heading,
     with no other heading in between.
   - Every corrected value matches the reviewer's words. Nothing is invented.
3. **Fields made unknown.** All 14 reasons start "session 2, Qn (no): …".
   - Pages kept as excerpts only (J01, J04, J16, J18, C03, C04) cannot cite the reviewer's
     words, so unknown is right there.
   - "No" values still served unchanged: Q127 (C08.1 evidence kind), Q95/Q96 (C10.1/.2
     "exam"), Q142 (C02.2 topic mention), Q261 (J15.4 "no gate") and Q284 (J10 pay without
     "pro rata"). See Minor 1 and 2.
4. **0.1.0 is unchanged.** `git diff --quiet fa40db5 3b2fd87` on both 0.1.0 files exits 0.
   - The file hashes match `PINS`: pack 0.1.0 `d7ff17d7…`, 0.2.0 `b4afe250…`; reference
     0.1.0 `906b4e96…`, 0.2.0 `2df1c70d…`.
   - The app still pins 0.1.0 (`capability/commands.py:73-74`).
5. **Capability reference 0.2.0.** It is needed (see Extra above), its content is
   unchanged, and it stays `proposed`. Its R1-R40 tally (23 yes, 8 "?", 9 no) matches the
   record.
6. **Pack shape.** 0.2.0 is a full version, not a delta. It has 20 + 60 + 10 + 10 + 18 + 3
   = 121 records and 473 claims. It uses `dump_pack`'s one-item-per-line form, which is why
   it is 671 lines. `load_pack("0.2.0")` passes its pin and `check_pack`.
   - Sources, targets and skills are identical to 0.1.0.
   - The 466 claims it keeps are identical to 0.1.0's and in the same order. 15 were
     removed and 7 added, exactly as the report lists.
7. **`session_2_pack.py` and its tests.** The mapping is correct (check 1).
   - The golden test (`test_the_committed_version_is_the_record_applied_to_0_1_0`) ties
     the committed file to the tool, and the tool to `session-2-answers.md`.
   - The question file is itself pinned to `tools.option_pack_files`
     (`tests/tools/test_option_pack_files.py:26`), so the numbering cannot drift silently.
   - The tests check real invariants of the published pack: reviewed only when all yes,
     spans in bodies, called-wrong values gone. Some reuse the tool's own parsers (Minor 6).
8. **Interpretive readings.**
   - **Q25** (`req:J18.1` importance → `unknown`): this is what the record says ("not
     established as essential"). In the matrix, `derived_importance` ignores `unknown`, so
     the row no longer reads as essential from this posting. Fine.
   - **Q142** (C02.2 kept as unsupported) and **Q167** (C06.2 → `unsupported`): both match
     the substance of the answers, and R51 agrees. Fine.
   - **Q127** (C08.1 kept): R54 said yes to the same label, and Q127 agrees the page gives
     eligibility to register. Evidence kind has no "unknown". `pack_outcomes` sets
     `outcome_type` from the skill row, not from `evidence_kind`, so the label has no effect.
     Defensible.
   - **Q261** (J15.4 kept with no gate): adding a gate needs a typed gate in the capability
     reference, which is Task 10's to decide. The requirement still enters the matrix as a
     posting row (`capability/matrix.py:481`, `:631-654`). Defensible.
   - None of these amounts to the agent deciding something the record does not say. The two
     agent decisions that do go beyond the record are the bare "?" handling (Important 1)
     and the Q153 extension (Minor 3).

### Strengths

- **The published version is built from the record, not edited by hand.** One golden test
  makes every change in 0.2.0 trace to a numbered answer and a written decision. Removing
  any decision fails it, and the report's mutation runs confirm that.
- **0.1.0 is untouched.** Both pins are correct, and the earlier version stays loadable.
- **The partial-record rule is applied exactly.** No record is reviewed on a non-yes row,
  and no record is reviewed on rows nobody asked: the 29 unasked requirement rows carry no
  review.
- **Provenance is honest in every record.** It says whether the rows were the product
  owner's own (Q1-Q15) or AI-checked and adopted by the 2026-10-30 ruling. The decision
  date also follows this: 2026-10-29 for the product owner's own answers, 2026-10-30 for
  the rest.
- **Corrections are real span-cited claims.** They are checked in the hash-checked bodies or
  inside stored excerpts, and each note names its question.
- **Values that excerpts-only pages cannot cite become unknown, never guessed.**
- **Fail-safe choices:** T and R rows count as record rows, which stops five outcomes being
  wrongly reviewed. Levels stay null, and no protected gate is touched.
- **Disclosure is thorough.** The report states its own rulings, conflicts and carry-forwards
  clearly, including D8's ambiguity and the anchor answers that conflict with spec
  section 8.

### Issues

#### Critical

None.

#### Important

1. **Bare "?" answers keep their values, against the controller's explicit ruling**
   (`backend/tools/session_2_pack.py:14-15`, no `Decision` entries for Q227-Q242;
   `docs/adr/0011-england-option-pack-format.md:223`; `task-7c-report.md:147`).
   - **What.** The dispatch says a "no" or "?" with no citable value makes the field
     unknown with the review's reason. The implementer instead kept the values of the 13
     bare "?" fields on the Adzuna copies J02, J03 and J07. They also kept Q290's (though
     there the format cannot hold an unknown: `SkillRequirement.text` and `gate` are not
     `Ref`). The report then says the dispatch "did not settle" this.
   - **Why it matters.** J01, J02 and J07 are one vacancy
     (`vacancy:awd-junior-it-support-bristol`). Q224 says "AWD is the agency; the unnamed
     employer is described as 'our Client'". Yet 0.2.0 still serves employer "AWD online"
     on J02 and J07 (pack file lines 540 and 545), beside J01's unknown. The pack now
     gives two answers for one vacancy's employer, and one is a value the reviewer said is
     wrong. The departure from a controller ruling was also not escalated as a conflict
     (the brief's "undecided stays proposed" against the dispatch's "?" → unknown).
   - **Fix.** Ask the controller to rule. Either:
     - apply the dispatch: make the 13 fields unknown, with reasons like "session 2, Q227
       (?): the reviewer could not decide"; or
     - confirm the implementer's reading, and at least make the employer unknown on J02
       and J07 by Q224 (the same vacancy).

     0.2.0 is committed, so publish the change as 0.2.1 through the same tool unless the
     controller rules that the unpinned 0.2.0 may be replaced. Correct the report's ruling 3
     and ADR 0011 decision 15 to match.

2. **Q187's correction was applied as a removal, so F01 loses its earnings condition**
   (`backend/tools/session_2_pack.py:486-491`; `funding:F01` at pack file line 667).
   - **What.** The reviewer stated the reading and quoted it from F01's page: "earn below
     £25,750 or are unemployed", with no annual period and no gross basis. The implementer
     dropped `F01.rule_earnings`, saying the earnings shape cannot hold it (ruling 4). But
     `rules` takes each claim's own field shape: F01 already lists a text rule,
     `F01.rule_local_variation` (pack file line 511). F01's body is kept, and the words sit
     at 7233-7269. So a span-cited text rule quoting exactly those words, with a note
     naming Q187, fits the format and adds no interpretation.
   - **Why it matters.** 0.2.0's F01 now lists age, local variation and course levels but
     no earnings condition. Anyone reading the instrument's rules sees fewer conditions than
     the page states. The reason exists only in the record's review text, which planning
     (`planning/pack.py:345`) does not carry. A known condition disappearing is the opposite
     of "unknown is never ineligible".
   - **Fix.** In the next version, replace the drop with a corrected claim. It is text
     shaped (a field name not in `CLAIM_FIELD_SHAPES`, so it falls to text), with value
     "earn below £25,750 or are unemployed", span 7233-7269 and occurrences checked in the
     body, and a note citing Q187. Add a test that F01's rules still state the earnings
     condition.

#### Minor

1. **J10's pay is served without the qualification the reviewer said to keep**
   (`session_2_pack.py:566-570`).
   - Q284 says "retain the pro-rata qualification". `JobPosting.salary` is a `Ref`, so it
     could be unknown with the reason. The implementer kept the range because "the range
     stands".
   - J13 keeps "pro rata per annum" as a fact; J10 has nothing, since its excerpts do not
     hold the words.
   - Ask the controller whether a range missing its stated basis counts as "a value the
     reviewer said is wrong" under the dispatch.
2. **Labels the reviewer called wrong are still served where the format has no unknown.**
   - The labels are: C08.1 `assessed_work_sample` (Q127), C10.1/.2 `exam` (Q95/Q96),
     C02.2 `topic_mention` for reconciliation (Q142) and J15.4 "no gate" (Q261).
   - All are on `proposed` records with null levels and do not change readiness (check 8).
   - The report lists the format gaps (a credential evidence kind, a driving-licence
     gate). Make sure the controller's ledger carries them to Task 10.
3. **Q153 is also applied to `option:C05.assessment`** (`session_2_pack.py:473-478`).
   - Nobody was asked about that field, and Q143-Q145 on `option:C05` are all yes. The
     extension keeps an otherwise accepted record `proposed`.
   - It is the cautious choice: the old value "not stated on the page" contradicts Q153.
     It is documented in ADR 0011 decision 15.
   - It is still an agent decision beyond the row asked, so the controller should confirm
     it.
4. **Q38 drops the C01 course-hours fact entirely** (`session_2_pack.py:349-354`).
   - The reviewer's reading was "195 hours", just not guided learning hours. A text fact
     quoting "195 hours" (C01's body is kept) would keep what the page states without the
     wrong label.
   - Low impact, since hours give no pace in planning.
5. **The pack notes lose two statements from 0.1.0** (`session_2_pack.py:660-675`, `:802`).
   - 0.1.0's first note held the Task 7b curation provenance (33 real pages retrieved
     2026-10-29) and "never fills a live field". 0.2.0's notes drop both.
   - 0.2.0's second note limits "never shown as current" to proposed records, but R9
     applies it to every pack record, reviewed ones included.
   - Restore both in the next version's notes.
6. **The tool couples a historical fact to a constant that can change.**
   - `SOURCE_VERSION = PACKAGE_VERSION` (`session_2_pack.py:56`) ties "the version session 2
     reviewed" to `tools.option_pack_files.PACKAGE_VERSION`, which a later package may
     bump. Pin `"0.1.0"` literally.
   - Several tests also use the tool's own `answers()` and `record_rows()` as their oracle.
     This review's independent parse agrees with them, but a test with its own small
     parser of the record would not share a parser bug.
7. **Four of the seven corrections are checked only on the curating machine.**
   `test_a_correction_located_in_a_kept_body_is_exactly_its_text_there` skips without
   `var/evidence/corpus/` (`tests/tools/test_session_2_pack.py:201-202`), as on CI. That is
   acceptable under R3. The review package should say these checks ran only locally.
8. **"Labels reviewed" overstates partial completion.** The manifest status
   `collected_labels_reviewed_at_session_2` (`corpus/manifest.json:9`) and the README line
   "labels reviewed at session 2" sit beside 66 of 121 records still `proposed`, 29 of them
   never asked. "Label review applied (55 of 121 reviewed)" would not mislead.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The pack is built faithfully and checkably from the record: 0.1.0 is
untouched, every reviewed record traces to all-yes rows, and every correction is verified in
the source. Two things should not reach Tasks 10, 12, 8 and 13a without a fix or a ruling:
the "?" handling departs from the controller's explicit ruling and still serves an employer
the reviewer said is wrong, and F01 has lost its earnings condition. Both are fixed in a new
version, through the same tool, under a controller ruling on the "?" reading.
