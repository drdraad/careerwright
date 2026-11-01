# Task 6d slice B review, half B: the app, the truth and the tests (`app`)

Reviewed: f7f0e4d..21a397d (dff9c2e code; 2317e19 captures only; 21a397d ADRs, register and
runbook only, checked with `git show --stat`). I read the backend half of the review diff in
full, the tests and the evaluation changes in full, and the ADR, runbook and register lines.
Outside the diff I made one focused check per named risk, at 21a397d: the target-record CHECKs
and RLS in 0034; `soc2020_index_entries` in 0027 (`isco_code NOT NULL`, read policy for the API
role); `commit_profile_version`, `write_profile` and `apply_updates` (whether other role writes
touch the record); `record_targets`, `title_record` and `stored_targets`; `choose_target` (a
target's choice always takes ESCO's title); the ESCO type-ahead query; `normalise_label` and
`TextValue`; the setup path (`compose.yaml:59`, one `setup-database`); the worker (it never
resolves a title: the strength and the note inputs are built in the API); capability's stored
tables (`matrix_edits` keyed by target); and the web's `Start`, `FirstQuestion` and `useCommand`
only where they decide whether a backend fact is shown. I ran no tests (`make check` and `make
acceptance` are the implementer's runs).

### Spec Compliance
- ✅ Spec compliant for this slice's bullets, with one Important defect below.
  - The first question finds any UK title: ESCO and the pinned index as one list, ESCO first on
    ties, one entry per index title with every SOC 2020 and ISCO-08 group, none picked
    (`catalogue/taxonomy.py::match_titles`, `reference_store.uk_title_matches`).
  - "Use my own words" keeps the title as given (`exploration.py::name_role`). The 1–120
    character limit matches the field's `maxLength={120}`, so nothing the field accepts is
    refused. A title with only punctuation is kept too: its concept key is empty, which no
    CHECK forbids.
  - "Which of these is closest?": every group, none picked; an empty group stays shown; "None of
    these is my job" names no occupation and asks for none (`closest_offer`, `choose_closest`).
  - Title ideas: a reason code on each; an idea the index lists exactly becomes a suggestion in
    its own list, never in the slate's pool; an idea no list holds is "not yet found"
    (`compute_slate`, `TitleIdeaReason`). The slate's ranking is unchanged: the same-slate test
    still compares every case recorded before 6d.
  - The lines that said "isn't in ESCO" are now facts (`Resolution.uk_title`, `title_kept_as_own`,
    the title-idea reasons). The evaluation check reads `reason`, and DSC-20 is added.
  - Carried items: (1) the reason code and exhaustive maps (`TITLE_IDEA_SHOWN`, `FOUND_NO_WORK`,
    `TOO_GENERAL_BY`, `ROLE_KEPT`) are done. (2) "Only a choice cites a source" fits both new kinds
    (a closest choice is an `occupation_choice` with its source; "none of these" cites none). I
    agree no CHECK had to change; see M4 for what the CHECKs still don't repeat. (3) The other
    nursing fields are in the one `resolve_target`, a named constant with its reason, re-decided
    in 0036, and tested per field.
  - Migration 0036 is forward-only, adds no table and no policy, and doesn't edit 0034 or 0035. It
    runs safely on a 0035 database, and `test_0036` checks the migrated records against
    `resolve_target` (`after == decided`).
  - The pinned data only: the type-ahead and the resolver read only the imported, hash-checked
    tables. They make no network call and no model call. Without the index they refuse
    (`REFERENCE_DATA_UNAVAILABLE`); they never say "not listed" (`uk_titles.held_index`).
- The implementer's concerns:
  - **RED before GREEN for the domain rules only.** The other new tests would fail without their
    code: the two new commands didn't exist, `test_0036` checks before against after, and
    `reason` is a new field. They count as evidence. This is a process gap, not a finding.
  - **The first question before the entry choice.** The phone layout is half A's to judge. On the
    backend side, "Skip for now" calls nothing and saves nothing.
  - **Seeding needs the UK index first.** This is acceptable. There is one setup path
    (`cli.py` setup-database; `compose.yaml:59`), and it fails loudly if an import fails. Every
    test that seeds a fresh database was changed to match, and each change is disclosed.
  - **Not built: making a UK title idea a target from its list.** The card says such ideas
    "become suggestions", and acceptance 4 only asks that they show with their answers and the
    index line. Not required here. REC1-06 and ADR 0015 record it as open.
  - **Not built: asking "which do you mean" in the start.** Neither the card nor the acceptance
    asks for it. The origin still returns `ambiguous` with its `choices`, as before.
  - **The heredoc.** A process slip. The content was put back with Edit, so it has no effect on
    the product.
- ⚠️ Cannot verify from the diff:
  - That the real index holds the four acceptance titles with the groups the tests assert, and
    that DSC-20 passes on the full release (integration runs, under the lock).
  - The reported timings.
  - How fast the type-ahead is for a one- or two-letter start on the full index: not measured.
    For each matching title, the query checks ESCO's labels by concept key.
  - Everything in half A (words, focus, the phone's first screen).

### Strengths
- The strict reading of the index is right. Without it, the type-ahead, the resolver and the
  slate refuse, so a missing index can't become "Careerwright couldn't match it in the UK
  job-title index".
- One rule decides everything: an ONS title, a closest choice and "None of these" all go
  through the one `decide`. The migration's SQL is checked against `resolve_target` itself, and
  a constants test keeps 0036's copies equal to the resolver's.
- The slate's frozen rules are respected. UK-listed ideas never enter the pool, the evaluation
  check now reads what Careerwright did with each idea, and the earlier cases' slates are
  compared unchanged.
- The type-ahead's SQL is safe: the words are letters and digits only, and the LIKE wildcards
  are escaped. A title ESCO offers is never offered a second time as the index's.
- The disclosure is thorough: every changed test input and expectation is named, with why.

### Issues
#### Critical
None.

#### Important
**I-1. The role's closest choice is kept in two places, and they can disagree, so the person's
choice is lost.** (`profile/titles.py:50-58`; `profile/exploration.py:1490-1494`, `:1559-1560`;
`profile/commands.py:182` `write_profile` never touches the record)
- What: `choose_closest` records the choice twice:
  - as the source of the role field (an `occupation_choice`);
  - in the title's record (`link = occupation_choice`).

  The role's ESCO occupation is read from the field's source (`titles.current_role`). The
  closest decision is read from the record (`closest_offer`).

  Now suppose the role's words change through What we know or a conversation decision: even
  "Registered nurse" to "Registered Nurse", or to another title and back. The field gets a new
  direct-entry source, but the record (same concept key) is untouched. What follows:
  - The role loses its occupation: state `not_in_esco`, no usual skills, no destinations.
  - The origin's `role.closest` still says `decision: chosen` with the old occupation.
  - A target with the same title still names that occupation.
  - The start never asks again: it asks only while the decision is `not_yet`.
  - `choose_closest` with the occupation shown as chosen returns 200 "unchanged".
  - The discovery slate tells the person to "Choose the ESCO occupation closest to it".
- Why it matters: this is lost input. The person's choice silently stops seeding their role and
  the UI can't restore it. Two readers of one title disagree, which is exactly what storing each
  title once is meant to prevent.
- Fix: make the record the one truth for the role, as it is for targets. When the field's source
  is not an occupation choice, `current_role` takes the closest occupation from the role's
  record (`link = occupation_choice`). If the field's source must stay the truth instead, then:
  - any role write that changes the source re-decides the record (back to `not_yet`);
  - `choose_closest` commits again when the field doesn't cite the record's choice.

  Add an integration test: choose a closest occupation, change the role's words with PUT and
  back, then check that the origin's `state`, `occupation` and `closest` agree.

#### Minor
- **M-1. `RoleOut.kind` is wrong for a role chosen from ESCO by one of its other titles**
  (`targets.py:200`; `choose_role` stores no record). The earlier-choice rule matches only ESCO's
  preferred title, so a role chosen as, say, "IT support technician" (an alternative label)
  reads `kind: own_words` or `ons`, though the field documents `esco` as "an ESCO title chosen as
  such". No sentence uses it today (`ROLE_KEPT` is gated on `not_in_esco`). Fix: `choose_role`
  stores the role's record with its choice, or `kind` follows the field's source.
- **M-2. No test that the type-ahead, "Use my own words" and the slate refuse without the
  index** (`uk_titles.py:22`). The behaviour is right, but nothing guards it. It protects "unknown
  is never 'not listed'". Add one call to `GET /v1/taxonomy/titles` in the existing
  no-reference-data database, expecting 503 `REFERENCE_DATA_UNAVAILABLE`.
- **M-3. The other-field rule lists the fields to block, not the qualifiers to allow**
  (`targets.py:62`). "(paediatric)", "(child)", "(RMN)", "(psychiatric)" and "(mental)" still
  reach the pack's adult nurse. By R11 these are hypothetical forms: record them as a known
  limit. The fail-safe alternative (the bracket rule reaches a pack target only for known-neutral
  qualifiers) is a policy choice, so it is a one-line question for the product owner, not a fix
  here.
- **M-4. The CHECKs don't repeat this slice's new rules.** These are kept in code only:
  - an ONS record has at least one SOC and one ISCO-08 code (`only_an_ons_title_has_ons_codes`
    checks only the other direction);
  - `none_of_these` is set only on an ONS title, with `recorded_by`.

  An ONS record with no codes would silently never ask the closest question.
- **M-5. "None of these is my job" from `not_yet` makes no profile version**
  (`exploration.py:1573`). The decision appears only in the record. A stale tab sending the same
  expected version can override it without a conflict, and a pinned discovery's fewer-reason
  changes on read. Low effect on a one-person local app.
- **M-6. Exact spelling against the concept key.** Two known limits to record (R11), not to fix
  now:
  - A record is keyed by concept but its kind is decided on the exact spelling of whichever
    write came first. "Registered nurse." and "Registered nurses" share the record for
    "Registered nurse".
  - The type-ahead drops an index title that ESCO holds as a concept (`reference_store.py:368`),
    but ESCO's own list matches word beginnings. An index title whose ESCO twin is written with
    "&" or an accent can drop out of both lists and fall to the partial list.
- **M-7. Things migration 0036 doesn't say:**
  - Importance edits made against the adult pack's rows for a target it re-decides stay stored
    but no longer apply. 0036 and ADR 0012's line don't say so.
  - On a 0035 database without the index, own-words records stay own-words after the index
    arrives: nothing re-decides them. Setup's order makes this unlikely.
  - The `lower()` against `casefold()` difference is disclosed.
- **M-8. Coverage gaps.** No test for:
  - a closest choice for the role becoming a same-titled target's occupation (ruling 1's
    consequence);
  - a "Use my own words" title with only punctuation;
  - the failure path of the new `title_idea_reasons` check.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The type-ahead, the index's corroboration, the facts, 0036 and the evaluation case
are correct, offline and honest about a missing index. But a closest occupation the person
chose can silently stop seeding their role while the record and the API still say it is chosen,
and the UI can't restore it (I-1).
