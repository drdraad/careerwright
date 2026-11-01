# Review: L0 assessment handover applied (commits 3d2f377, 9151d84, 28a2a27, d676aee)

Reviewer: independent, read-only. Inputs: `docs/plan/l0-assessment-handover.md`, the controller
additions in the dispatch, `plan-update-report.md` (treated as unverified claims), the diff
`review-26fdb95..d676aee.diff` (b543fd3 skipped) and the full current documents. I read the
diff in four passes, one per commit. Checks I ran: `git show --stat` per commit; a scripted
column-by-column comparison of every register row before (b543fd3) and after (d676aee); a
stdout-only replica of the `make-brief.sh` awk for every remaining task ID; hand
re-derivation of Σ C(24,k)·2^k; and focused reads of ADR 0001, ADR 0005, ADR 0007 decision 6,
`docs/reviews/sprint-1.md`, `docs/design/pre-review-sprint-0.md`, `docs/reviews/sprint-0.md`,
`docs/reviews/sprint-2.md` and `corpus/manifest.json` open items.

### Spec Compliance

- ✅ Spec compliant against the handover. Every one of P1–P8, S1–S3 and T1–T7, and every
  controller addition, is applied. Two coherence gaps in the dependency and ownership model
  remain (Important 1 and 2 below). Neither is a handover requirement the agent missed: the
  handover is silent on both.

| Item | Status | Evidence |
|---|---|---|
| P1 Review sessions | Applied | plan:23 (sizing unit, 16 h), plan:183 ("Human review hours" column), plan:219 (section 6 paragraph), plan:685–693 (section 10 table: three sessions, gates closed, preconditions); every remaining card has a `**Preconditions:**` line |
| P2 Option pack | Applied | plan:635–645 (section 9: shapes, R7 or commit, labelling, live writes `proposed`), plan:652 (Evaluation outputs row), plan:339 / 375 / 393 / 409 (Sprint 3–5 live-versus-reviewed scoring; P01 real option set), plan:717 (section 11 row) |
| P3 Critical-chain order | Applied | plan:206–217 (eight ordered steps), plan:333 (S3.5 deferred position), plan:335 (reduced S3.6) |
| P4 Sprint 6 split | Applied | plan:417 (6a, S6.7 and measured sizes in acceptance at plan:443), plan:449 (6b with its own acceptance). Every v1.0 Sprint 6 deliverable and acceptance clause reappears in 6a or 6b |
| P5 Formative session | Applied | plan:177 (section 5), plan:411 (Sprint 5 card: one person, 30 min, synthetic data, three questions, product owner, session 2) |
| P6 Adzuna | Applied | plan:329 (S3.3), tasks:107 (R4) |
| P7 Risks | Applied | plan:766–767 |
| P8 Version | Applied | plan:5 (v1.1, dated), plan:31 (change note pointing at the handover), plan:740 (spec 1.3 is the authority) |
| S1 Pack as an evidence pack | Applied | spec:50 (BND-1 row), spec:628 and spec:630 (section 11 M0 option pack paragraph) |
| S2 OPT-1 disclosure | Applied | spec:801 (section 12; 10,161,633 re-derived: 1+48+1,104+16,192+170,016+1,360,128+8,614,144), spec:1177 (section 18) |
| S3 Span-cited explanation | Applied | spec:255 (REC-1) |
| Section 22 | Applied | spec:1294–1302 (v1.3 table; D1 and D3 accepted (confirmed), S2 accepted as a disclosure), spec:5 (header 1.3, dated). The spec diff touches only these lines (20+/4−) |
| T1 Task 7b | Applied | tasks:479–522; consumption in Tasks 8 (tasks:536), 10 (tasks:591), 12 (tasks:650); Task 11 real option set (tasks:622–625) |
| T2 Rules and order | Applied | tasks:173–195 (11 rules, the suggested order, session 1 placement) |
| T3 Preconditions | Applied | 14 cards, one `**Preconditions:**` line each; R10 at tasks:149–151 records "blocked: awaiting session N" |
| T4 Task 13 split | Applied | tasks:657 (13a, report at tasks:678–682), tasks:684 (13b) |
| T5 Scope notes | Applied | tasks:447–463 (Task 7), tasks:534–537 (Task 8) |
| T6 Rulings | Applied | tasks:107 (R4), tasks:140 (R9), tasks:149 (R10) |
| T7 Register | Applied | reg:261–262 (OPT1-15/16), reg:487–489 (OPTN-08..10), reg:328–329 (TEST1-13/14), reg:118 (REC1-11), reg:643 (H-13), reg:645 (sessions table), amended H-01/06/07/12 (reg:636–642), TEST1-09 and OUT1-10 owners |
| Controller: Task 6b | Applied | tasks:344–382: one bounded call per slate, verified quotes, one repair then `invalid_model_output`, deterministic provenance underneath and cited by exports; live runs use the test model on synthetic data, capped and ledgered; plan:303 (S2.7) |
| Controller: Task 6c | Applied | tasks:384–437: V-01, V-03–V-06, V-09, V-10; S0-V03, S0-V04, S0-V06, S0-V07 (Routes); compositions corrected and recaptured; `next` 16.4.1 exception removal. The IDs match `sprint-1.md:500` and `sprint-0.md:243`. One wording error (Minor 3) |
| Controller: sequential execution | Applied | tasks:168–171, plan:217, ADR 0008:70–73 |
| Controller: heading form | Applied | `## Task <id>:` for 6b, 6c, 7, 7b, 8–12, 13a, 13b, 14–16. The awk replica extracts each one (18–55 lines, one Preconditions line each); "13" extracts nothing; the preamble ends at `## Task 1:` and carries R9, R10 and the rules |
| Controller: Session 1 contents | Applied | tasks:154–159, plan:691, reg:651 (H-06 policy and H-12; D1–D3 need no session time) |
| Only five documents changed | Applied | `git show --stat`: 3d2f377 = spec; 9151d84 = plan; 28a2a27 = task file and ADR 0008; d676aee = register. Working tree clean |

Section 6 (must not change): preserved.
- The spec section 1 invariants are untouched. The only section 1 edit is the BND-1 "Research and
  caching" cell.
- ADR 0001 is unchanged, and nothing in the change needs hosting or a shared cache.
- The durable core is not simplified anywhere.
- `fixtures/m0` is untouched. R9 and OPTN-08 keep synthetic data out of the pack.
- R2 and R5 text is unchanged (the only removed ruling lines are R4's).
- All three requested features remain: the dendrite (S3.5 "deliverable unchanged", Task 8), the
  three Pareto layers (13a) and the sliders (Task 14).
- Register: the scripted comparison over 398 old rows shows no ID removed, renumbered or
  duplicated, and 17 IDs added. In the 54 amended rows only Owner, Evidence, When or Checklist
  changed. The exception is the H-06 gate text, whose two-part form P1 mandates (a person sets
  the policy; out-of-class pages stay with a person). No Status cell changed and no
  requirement text changed.

Planning agent's decisions:
- "Same catalogue" means the same record contract inside the workspace. This is correct. It is
  the only reading consistent with spec:628 ("user research is not reused for other testers")
  and the M1 cross-tenant deferral. It is recorded consistently at spec:630, plan:645, R9,
  OPTN-09 and ADR 0008:52–58.
- Session 2 also precedes Tasks 10, 12 and 8. This is consistent with the handover's suggested
  order and with P1's "dispatch precondition for the task after it". It does not contradict
  "10 and 12 may run in parallel with 8".
- S2.7 for Task 6b is sound. The task file only slices the plan. The handover's "nothing else
  changed" applies to the spec, which has no extra edit.
- H-06 as a Session 1 policy is mandated by P1, and R2 holds. See Minor 5 for the missing
  cross-reference in R2's own text.
- Keeping the S3.6 imports is accepted by the controller. It keeps AIR1-03, AIR1-07, AIR1-11
  and TAX1-07 owned, and it relaxes nothing.
- Decision 9 (sessions table in register section 6) is correct. The register's section 5 is
  the spec section 20 checks (reg:608), so the handover miscounted.

None of these decisions contradicts the handover or the specification.

- ⚠️ Cannot verify from the diff:
  - The product owner's confirmation date. The handover's tick line (handover:33) still reads
    "(product owner, date)". The documents state 28 October 2026 on the controller's word.
  - Adzuna credentials under `NESSA_HOME`. Not inspected; R4 relies on the handover's
    verified state.
  - That `make-brief.sh` writes correct briefs. I replicated only its awk to stdout; nothing
    was written.

### Strengths

- The application is complete and precise. The wording is tight and carries no new rule; for
  example, the S2 disclosure keeps "No rule changes" at spec:801 and adds nothing to the caps.
- The Sprint 6 split is lossless. Each v1.0 S6.3–S6.5 clause and acceptance sentence is in 6a
  or 6b. 6b also gains a cross-check: on completing instances its archive and ranks must equal
  6a's peeled layers (plan:465).
- The register's ownership move from T13 to T13a/T13b is consistent across 41 cells. Rows that
  span both parts name both (for example OPT1-05 and LIMITS-05), and the bare "T13" remains
  only as the split note at reg:75.
- R10's "only the product owner's own record establishes an outcome; an agent may transcribe,
  never supply" closes the self-certification hole that scheduled sessions could open.
- Everything the commits removed from the task cards reappears in Tasks 7b, 8, 10, 12, 13a or
  13b, so no deliverable fell out with the corpus move.

### Issues

#### Critical

None.

#### Important

1. **No task turns session 2's review into a reviewed pack** (`docs/plan/l0-sprint-tasks.md`
   lines 505, 598, 653, 659, 675).
   - What: Task 7b builds every record `review_state: proposed` (tasks:505). Plan section 9
     says the session 2 review "moves it to reviewed" (plan:637). But Tasks 10 and 12 only
     *record* the H-07 outcome in their sprint reviews (tasks:598, 653). No task writes the
     product owner's decisions into a new pack version (reviewed or rejected, with reviewer
     and date), and none closes OI-08 (label review) or the job-postings part of H-07.
   - Why it matters: several tasks need reviewed records.
     - Task 13a's precondition and deliverable need "the reviewed option pack" (tasks:659,
       675).
     - OPT1-01 searches "the reviewed finite monthly catalogue".
     - OPTN-09 keeps `proposed` records out of unqualified results.
     - Tasks 8, 10 and 12 score against "the reviewed values" (TEST1-13).

     As written, Task 13a either runs on an all-`proposed` pack, or an implementer changes
     review states in an ad hoc step that no brief defines or reviews.
   - Fix: add a named step to the first task after session 2 (Task 10 in the suggested order,
     or a short dedicated step). It transcribes the product owner's H-07 record into a new
     pack version, validated by the Task 7b validator, with reviewer provenance, and updates
     OI-08 in `corpus/manifest.json`. Then make Tasks 12, 8 and 13a depend on that step in
     rules 6, 8 and 9 and in their Preconditions lines. R10 already allows transcription.

2. **The release task does not depend on the Roles, Skills or Options chapters**
   (`docs/plan/l0-sprint-tasks.md` lines 190, 754).
   - What: rule 11 and Task 16's Preconditions require only Task 15, which requires Task 14,
     then 13b and 13a. Tasks 8, 10 and 12 are prerequisites of nothing.
   - Why it matters: Task 8 is the task most likely to wait, on session 1. Under R10 the
     controller then records "blocked: awaiting session 1" and proceeds with whatever the
     rules allow. That is 13a through 16, so release qualification (P01–P05 end to end across
     all six chapters; plan roadmap Sprint 9 dependency "Complete product journey") can be
     dispatched with no Roles chapter.
   - Fix: "Task 16 after Tasks 8, 10, 12 and 15", in rule 11 and in Task 16's Preconditions.

#### Minor

1. `docs/plan/l0-sprint-tasks.md:178`, `:554–555` versus `:561`: rule 3 and Task 9's card say
   Task 9 has no dependency on Task 7b. Yet Task 9 loads the pack "in the Task 7b format", and
   ADR 0008:167 says Task 7b owns that format. Because tasks:168–171 allow "∥" pairs "in either
   order", running Task 9 first is permitted and would break. Fix: make Task 9 follow Task 7b
   (already the suggested order), or move pack loading out of Task 9.
2. `docs/plan/l0-sprint-tasks.md:381`: "amend ADR 0007 decision 6's last two sentences".
   Those two sentences are the `replaces` sentence, which is still valid, and "Model-written
   explanations are not used in L0" (`docs/adr/0007-conversation-discovery-and-support.md:144–147`).
   The decision title "…not model prose" (adr/0007:133) also contradicts D3. Fix: name the
   sentence by quotation, as ADR 0008:117 does, and include the title.
3. `docs/plan/l0-sprint-tasks.md:418`, `:420`, and Task 8's card at `:539–550`:
   - Task 6c says "Task 6 fixed the app for … S0-V05 … in You". But S0-V05 is a Roles finding
     (`docs/design/pre-review-sprint-0.md:131`), and `docs/reviews/sprint-2.md:213` says "The
     Roles card itself is T8's".
   - Task 6c hands the S0-V07 and S0-V08 Roles parts to Task 8, but Task 8's card names none
     of S0-V05, S0-V07 (Roles) or S0-V08 (failed Roles).

   Fix: correct the parenthetical, and list the three Roles findings in Task 8's deliverables.
4. `docs/plan/l0-sprint-tasks.md:548`, `docs/requirements-register.md:642`: H-12 closes at
   session 1, but no task transcribes its outcome. Task 8 records only H-06. Fix: Task 8, or
   the first task after session 1, also transcribes H-12 into ADR 0007's checklist and the
   register.
5. `docs/plan/l0-sprint-tasks.md:95–101`: R2 still says "source rights review cannot be
   performed by an agent". It does not mention R10's session 1 policy, under which agents
   classify pages. ADR 0008:97–100 reconciles the two, but every brief carries R2 verbatim.
   This is not a relaxation, since P1 mandates the policy. Fix: one clause in R2 such as "(after
   session 1, agents classify pages against the person's policy; a page outside it stays with a
   person; R10)".
6. `docs/adr/0008-option-pack-order-and-review-schedule.md:159`: it lists plan "sections 1, 5,
   6, 9–12" as changed. Plan section 1 did not change; the edits are in the header, "Delivery
   envelope" and "How to use this plan", which precede section 1. Fix: "the preamble, sections
   5, 6, 9–12".

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The handover and the controller additions are applied completely, faithfully and
without relaxing any requirement, invariant or register row. Two ownership and dependency gaps
need short document edits before the controller relies on the rules to dispatch:
- no step turns the session 2 review into a reviewed pack, which Tasks 13a, 8 and 12 need;
- Task 16 does not wait for Tasks 8, 10 and 12.
