# Session 2 package: the England option pack 0.1.0 (H-07)

Generated from the pinned pack by `tools.option_pack_files` (from `backend/`: `uv run
--locked python -m tools.option_pack_files`). Do not edit it by hand: a fast test checks
it against the tool's output, so its question numbers are stable for Task 7c.

- **Status:** agent preparation (Task 7b). The review is not run - requires human
  (H-07, ruling R2). Nothing in this file is an answer.
- **For:** the H-07 domain reviewer at session 2. Task 7c applies the answers by
  question number.
- **What:** 331 yes/no questions. They cover every consequential field of every
  record in
  `backend/src/nessa/catalogue/packs/england_option_pack/england-option-pack-0.1.0.json`,
  each beside the span it cites. Consequential means pay and its basis, money, dates and
  deadlines, durations and schedules, entry requirements and gates, eligibility rules,
  award status, outcome levels and the conflicts a page leaves open. P02 has no target in
  the fixture, so it has no records.

## The three parts

Answer the parts in order, and stop at the end of any part. Each part closes its gate on
its own; a part left unanswered leaves its records `proposed`.

| Part | Questions | Rows | About | Closes |
|---|---|---|---|---|
| Part 1: P01, every row | Q1–Q65 | 65 | 17 min | the TRACE-01 review of P01's real option set |
| Part 2: P03–P05's courses, then the funding | Q66–Q215 | 150 | 38 min | H-07 for Sprints 4–5 (the options, offerings, outcomes and funding) |
| Part 3: P03–P05's job postings and requirements | Q216–Q331 | 116 | 29 min | the job labels; Task 8 may take any rows left over |

In all: 331 rows, about 83 minutes at 15 seconds a row.

## How to answer

1. Read the row's excerpt. Open the page if you need its context: each slot's URL is in
   `corpus/manifest.json`.
2. Write **yes** if the page states the value as shown, with its unit, period and basis. For
   an "unknown" row, yes means the page does not state it.
3. Write **no** otherwise, with the right reading and where it is on the page.
4. Leave a row blank if you cannot decide.

## What Task 7c does with the answers

- **A record becomes `review_state: reviewed`**, with reviewer and date, only when every one
  of its rows is answered yes. Each record's rows are all in one part.
- **Otherwise it stays `proposed`.** A blank row leaves it undecided, and a "no" records the
  correction, with its span, for a later version.
- **The decisions are published as a new dated pack version.** Version 0.1.0 is not
  changed.

## Reading the rows

- **Money** is shown in pounds and pence. "up to" and "from" mark a bound the page states.
  "advertised" or "predicted" is the pay basis. "per unstated period" means the source gives
  no period (Adzuna's figures).
- **Durations** say how the course is taken (full time, part time, self-paced) where the
  excerpt does.
- **Excerpts** are shown as code, exactly as in the hashed text, with runs of whitespace
  collapsed. So HTML appears as written: `&#163;`, `&pound;` and `&#xA3;` are £, and
  `&#8217;` is ’. Adzuna excerpts are the API's JSON, cut at 120 characters.
- **Offsets** index the page's text after redaction (third parties' contact details are
  removed before hashing). A pointer is a JSON pointer into the Adzuna response.
- **The live page may have changed** since 2026-10-29. Answer from the excerpt, and note any
  difference you see.
- **Outcome rows** give the evidence kind (topic_mention, practice, exam or
  assessed_work_sample), then the level, then the confidence. No rubric exists yet, so no
  outcome has a level (Task 9 adds them).
- **"fact:" rows** are further span-cited facts a record keeps beside its fields, such as the
  second of two statements that disagree.
- **Requirement rows** are asked when the requirement is mapped to a target's skill row,
  carries a gate, or is an essential credential or eligibility requirement ("no gate" asks
  whether that is right).
- **Not asked:** titles, posting dates and source IDs. Rights are a separate human gate
  (OI-07); C08 is pending rights review.

## Part 1: P01, every row (Q1–Q65, about 17 minutes)

Closes the TRACE-01 review of P01's real option set.

### P01: Data quality analyst, Manchester (`data-quality-analyst-manchester`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q1 | `job:J05` | salary | £31,049.00–£37,796.00 per year, advertised | `£31,049 to £37,796 a year` (J05.salary, offsets 17643–17668) | yes / no |
| Q2 | `job:J05` | valid_through | unknown: the closed page shows no closing date | (no span) | yes / no |
| Q3 | `job:J05` | location | M14 7LU (postal code M14 7LU) | `M14 7LU` (J05.location, offsets 19177–19184) | yes / no |
| Q4 | `job:J05` | status | closed | `This job is now closed` (J05.status, offsets 13331–13353) | yes / no |
| Q5 | `job:J05` | advertiser | employer | `North West Ambulance Service NHS Trust` (J05.advertiser, offsets 12947–12985) | yes / no |
| Q6 | `job:J05` | employer | North West Ambulance Service NHS Trust | `North West Ambulance Service NHS Trust` (J05.employer, offsets 12947–12985) | yes / no |
| Q7 | `job:J05` | fact: contract_duration | 12 months | `12 months` (J05.contract_duration, offsets 17986–17995) | yes / no |
| Q8 | `req:J05.1` | requirement (essential, skill, row independent-querying) | Proficiency in SQL (T-SQL) for data extraction and manipulation | `Proficiency in SQL (T-SQL) for data extraction and manipulation` (J05.requirement, offsets 24187–24250) | yes / no |
| Q9 | `req:J05.2` | requirement (essential, experience, row data-validation) | Experience of investigating and resolving data quality issues | `Experience of investigating and resolving data quality issues` (J05.requirement.2, offsets 24440–24501) | yes / no |
| Q10 | `req:J05.5` | requirement (essential, credential, no gate) | Educated to degree level or equivalent | `Educated to degree level or equivalent` (J05.requirement.5, offsets 22944–22982) | yes / no |
| Q11 | `req:J05.6` | requirement (essential, skill, row communication) | Effective communication at all levels, both internally and externally | `Effective communication at all levels, both internally and externally` (J05.requirement.6, offsets 22273–22343) | yes / no |
| Q12 | `job:J12` | salary | £38,000.00–£45,000.00 per year, advertised | `£38,000 - £45,000 per annum` (J12.salary, offsets 33623–33650) | yes / no |
| Q13 | `job:J12` | valid_through | 2026-11-03T23:55:00+00:00 | `2026-11-03T23:55:00.000Z` (J12.valid_through, offsets 7236–7260) | yes / no |
| Q14 | `job:J12` | location | Greater Manchester | `Greater Manchester / Hybrid role (2-3 days on-site)` (J12.location, offsets 3539–3590) | yes / no |
| Q15 | `job:J12` | advertiser | agency | `Cathcart Technology is acting as an Employment Agency in relation to this vacancy.` (J12.advertiser, offsets 6986–7068) | yes / no |
| Q16 | `job:J12` | employer | unknown (null) | `An established and highly successful digital business is looking for a Data Analyst` (J12.employer, offsets 3617–3700) | yes / no |
| Q17 | `req:J12.1` | requirement (preferred, skill, row independent-querying) | Good SQL skills and confidence querying relational databases | `Good SQL skills and confidence querying relational databases` (J12.requirement, offsets 6081–6141) | yes / no |
| Q18 | `req:J12.3` | requirement (preferred, skill, row communication) | Strong communication skills and the confidence to explain findings to non-technical stakeholders | `Strong communication skills and the confidence to explain findings to non-technical stakeholders` (J12.requirement.3, offsets 6312–6408) | yes / no |
| Q19 | `job:J18` | salary | £44,000.00–£46,500.00 per year, advertised | `£44,000 - £46,500 per annum` (J18.salary, offsets 31749–31776) | yes / no |
| Q20 | `job:J18` | valid_through | 2026-12-02T23:59:59+00:00 | `2026-12-02T23:59:59.000Z` (J18.valid_through, offsets 5495–5519) | yes / no |
| Q21 | `job:J18` | location | Manchester, Lancashire (locality Manchester) | `Manchester, Lancashire` (J18.location, offsets 32090–32112) | yes / no |
| Q22 | `job:J18` | advertiser | unknown | `Consula Group LTD` (J18.advertiser, offsets 5381–5398) | yes / no |
| Q23 | `job:J18` | employer | unknown (null) | `A well-regarded organisation is looking for a capable Data Analyst` (J18.employer, offsets 3501–3568) | yes / no |
| Q24 | `req:J18.1` | requirement (essential, skill, row independent-querying) | Strong skills in Excel and at least one tool such as SQL, Power BI or Python. | `Strong skills in Excel and at least one tool such as SQL, Power BI or Python.` (J18.requirement, offsets 4618–4695) | yes / no |
| Q25 | `req:J18.2` | requirement (essential, task, row data-validation) | Maintaining data quality, accuracy and consistency in reporting. | `Maintaining data quality, accuracy and consistency in reporting.` (J18.requirement.2, offsets 4299–4363) | yes / no |
| Q26 | `req:J18.3` | requirement (essential, skill, row communication) | The ability to explain analysis simply to non-technical colleagues. | `The ability to explain analysis simply to non-technical colleagues.` (J18.requirement.3, offsets 4784–4851) | yes / no |
| Q27 | `job:J20` | salary | £35,000.00–£45,000.00 per year, advertised | `£35,000 - £45,000 per annum` (J20.salary, offsets 33521–33548) | yes / no |
| Q28 | `job:J20` | valid_through | 2026-12-07T23:55:00+00:00 | `2026-12-07T23:55:00.000Z` (J20.valid_through, offsets 7689–7713) | yes / no |
| Q29 | `job:J20` | location | Manchester (locality Manchester) | `Hybrid working in Manchester, 2 days per week` (J20.location, offsets 6164–6209) | yes / no |
| Q30 | `job:J20` | advertiser | agency | `We’re working with a growing retail business that’s investing heavily in data` (J20.advertiser, offsets 3602–3679) | yes / no |
| Q31 | `job:J20` | employer | unknown (null) | `We’re working with a growing retail business that’s investing heavily in data` (J20.employer, offsets 3602–3679) | yes / no |
| Q32 | `req:J20.1` | requirement (essential, skill, row independent-querying) | Strong SQL skills | `Strong SQL skills` (J20.requirement, offsets 5535–5552) | yes / no |
| Q33 | `req:J20.3` | requirement (essential, skill, row communication) | Strong communication skills and confidence working with stakeholders | `Strong communication skills and confidence working with stakeholders` (J20.requirement.3, offsets 5777–5845) | yes / no |
| Q34 | `option:C01` | credential | NCFE Level 3 Certificate in Data | `NCFE Level 3 Certificate in Data` (C01.credential, offsets 58911–58943) | yes / no |
| Q35 | `option:C01` | level | 3 | `NCFE Level 3 Certificate in Data` (C01.level, offsets 58911–58943) | yes / no |
| Q36 | `option:C01` | assessment | unknown (null) | `Learn, certify, succeed` (C01.assessment, offsets 60061–60084) | yes / no |
| Q37 | `option:C01` | fact: guided_hours | 195 | `195 hours` (C01.guided_hours, offsets 57939–57948) | yes / no |
| Q38 | `offering:C01` | fee_total | unknown (null) | `Take on our fully funded data analyst course` (C01.fee_total, offsets 53424–53468) | yes / no |
| Q39 | `offering:C01` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q40 | `offering:C01` | intake | unknown: no start date is stated | (no span) | yes / no |
| Q41 | `offering:C01` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q42 | `offering:C01` | duration | 10 weeks (full time); 17 weeks (part time) | `10 weeks full-time, 17 weeks part-time` (C01.duration, offsets 55850–55888) | yes / no |
| Q43 | `offering:C01` | schedule | unknown: no weekly hours or timetable are stated | (no span) | yes / no |
| Q44 | `offering:C01` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q45 | `offering:C01` | funding_route | Adult Skills Fund / Free Courses for Jobs | `Adult Skills Fund / Free Courses for Jobs` (C01.funding_route, offsets 59794–59835) | yes / no |
| Q46 | `offering:C01` | eligibility_area | Greater Manchester or the West Midlands | `You live in the West Midlands or Greater Manchester` (C01.eligibility_area, offsets 62203–62254) | yes / no |
| Q47 | `offering:C01` | eligibility_age | {"minimum_age": 19} | `You&#8217;re aged 19 or over` (C01.eligibility_age, offsets 62482–62510) | yes / no |
| Q48 | `offering:C01` | eligibility_earnings | {"below_annual_gross": {"currency": "GBP", "minor_units": 3240000}, "area": "Greater Manchester"} | `You earn below the gross annual wage cap of £34,194 (West Midlands)/£32,400 (Manchester)` (C01.eligibility_earnings, offsets 62738–62826) | yes / no |
| Q49 | `offering:C01` | eligibility_no_other_funded_training | true | `You&#8217;re not currently undertaking any other government-funded training` (C01.eligibility_no_other_funded_training, offsets 63054–63129) | yes / no |
| Q50 | `outcome:C01.1` | outcome for `independent-querying` | topic_mention, no level (no rubric yet), unsupported | `and manipulation techniques to help you prep raw data for analysis, including using SQL.` (C01.outcome_evidence, offsets 71869–71957) | yes / no |
| Q51 | `outcome:C01.2` | outcome for `data-validation` | topic_mention, no level (no rubric yet), unsupported | `Data validation and quality` (C01.outcome_evidence.2, offsets 72928–72955) | yes / no |
| Q52 | `outcome:C01.3` | outcome for `communication` | topic_mention, no level (no rubric yet), unsupported | `Communicating and presenting data` (C01.outcome_evidence.3, offsets 73856–73889) | yes / no |
| Q53 | `option:C04` | credential | Power BI Data Analyst (PL-300) | `Power BI Data Analyst (PL-300)` (C04.credential, offsets 4495–4525) | yes / no |
| Q54 | `option:C04` | fact: offer_kind | training course | `Training Course` (C04.offer_kind, offsets 32731–32746) | yes / no |
| Q55 | `option:C04` | fact: provider_outcome_claim | 98% of students secure a role upon graduation | `98% of students secure a role upon graduation` (C04.provider_outcome_claim, offsets 5503–5548) | yes / no |
| Q56 | `offering:C04` | fee_total | £2,995.00 | `£2995 or from £69.52/month` (C04.fee_total, offsets 6676–6702) | yes / no |
| Q57 | `offering:C04` | instalment | from £69.52 per month | `£2995 or from £69.52/month` (C04.instalment, offsets 6676–6702) | yes / no |
| Q58 | `offering:C04` | intake | unknown: not stated on the page | (no span) | yes / no |
| Q59 | `offering:C04` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q60 | `offering:C04` | duration | 6–8 months | `one year of 24/7 access to all training material, with an average completion time of 6-8 months` (C04.duration, offsets 5809–5904) | yes / no |
| Q61 | `offering:C04` | schedule | unknown: not stated on the page | (no span) | yes / no |
| Q62 | `offering:C04` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q63 | `offering:C04` | funding | self-funded | `Self-funded career programme with a guaranteed job on completion, or 100% of your course fees back` (C04.funding, offsets 6713–6811) | yes / no |
| Q64 | `outcome:C04.1` | outcome for `independent-querying` | practice, no level (no rubric yet), provisional | `Write and optimise SQL queries, clean and manipulate datasets with Python` (C04.outcome_evidence, offsets 4951–5024) | yes / no |
| Q65 | `outcome:C04.2` | outcome for `data-validation` | practice, no level (no rubric yet), unsupported | `clean and manipulate datasets with Python` (C04.outcome_evidence.2, offsets 4983–5024) | yes / no |

## Part 2: P03–P05's courses, then the funding (Q66–Q215, about 38 minutes)

Closes H-07 for Sprints 4–5 (the options, offerings, outcomes and funding).

### P03: IT support technician, Bristol (`it-support-technician-bristol`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q66 | `option:C07` | level | 3 | `Education level</th> <td class="govuk-table__cell"><span id="awarding-organisation">3</span>` (C07.level, offsets 21651–21751) | yes / no |
| Q67 | `option:C07` | assessment | the opportunity to sit CompTIA A+ and Microsoft exams | `You will prove that you have the skills and knowledge, by taking the opportunity to achieve the CompTIA A+ and Microsoft exams.` (C07.assessment, offsets 26728–26855) | yes / no |
| Q68 | `option:C07` | fact: description_inconsistency | an IT course whose text also speaks of data skills and data careers | `No prior experience is needed, just a keen interest in working with data.` (C07.description_inconsistency, offsets 24343–24416) | yes / no |
| Q69 | `offering:C07` | fee_total | £0.00 | `£0.00` (C07.fee_total, offsets 23145–23150) | yes / no |
| Q70 | `offering:C07` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q71 | `offering:C07` | intake | 2026-11-16 | `16th November 2026` (C07.intake, offsets 22904–22922) | yes / no |
| Q72 | `offering:C07` | application_deadline | unknown: no application deadline is stated | (no span) | yes / no |
| Q73 | `offering:C07` | duration | 12 weeks | `The 12-week programme will enable you to develop the skills and knowledge needed to start your career in IT` (C07.duration, offsets 26555–26662) | yes / no |
| Q74 | `offering:C07` | schedule | unknown: not stated on the page | (no span) | yes / no |
| Q75 | `offering:C07` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q76 | `offering:C07` | eligibility_age | {"minimum_age": 19} | `Aged 19+` (C07.eligibility_age, offsets 25563–25571) | yes / no |
| Q77 | `offering:C07` | eligibility_residency | ["London", "North Yorkshire", "West Midlands", "North East England"] | `Must reside in London, North Yorkshire, West Midlands or the Northeast area of England.` (C07.eligibility_residency, offsets 25605–25692) | yes / no |
| Q78 | `offering:C07` | eligibility_work_rights | right to work in the UK | `Have the right to work in the UK` (C07.eligibility_work_rights, offsets 25572–25604) | yes / no |
| Q79 | `outcome:C07.1` | outcome for `hardware-troubleshooting` | exam, no level (no rubric yet), provisional | `completing official courses in CompTIA A+, and Microsoft 365` (C07.outcome_evidence, offsets 26666–26726) | yes / no |
| Q80 | `outcome:C07.2` | outcome for `windows-m365-support` | exam, no level (no rubric yet), provisional | `completing official courses in CompTIA A+, and Microsoft 365` (C07.outcome_evidence.2, offsets 26666–26726) | yes / no |
| Q81 | `option:C10` | credential | professional certification | `Professional certification` (C10.credential, offsets 111285–111311) | yes / no |
| Q82 | `option:C10` | fact: fee_was | £495.00 | `inc VAT (was &#163;495)` (C10.fee_was, offsets 108508–108531) | yes / no |
| Q83 | `option:C10` | fact: price_valid_until | 2026-10-31 | `Offer ends 31 October 2026` (C10.price_valid_until, offsets 108607–108633) | yes / no |
| Q84 | `offering:C10` | fee_total | £295.00 | `<span class="current-price">&#163;295</span>` (C10.fee_total, offsets 108437–108481) | yes / no |
| Q85 | `offering:C10` | instalment | 3 payments, amount not stated | `evenly with 3 Easy Payments` (C10.instalment, offsets 109039–109066) | yes / no |
| Q86 | `offering:C10` | intake | unknown: not stated on the page | (no span) | yes / no |
| Q87 | `offering:C10` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q88 | `offering:C10` | duration | 60 hours | `60 hours` (C10.duration, offsets 110468–110476) | yes / no |
| Q89 | `offering:C10` | schedule | unknown: not stated on the page | (no span) | yes / no |
| Q90 | `offering:C10` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q91 | `offering:C10` | exam_fee | unknown (null) | `CompTIA exam fees are not included` (C10.exam_fee, offsets 137827–137861) | yes / no |
| Q92 | `outcome:C10.1` | outcome for `hardware-troubleshooting` | exam, no level (no rubric yet), provisional | `Module 1 - CompTIA A+ 220-1101 Devices, Setups, and Installs` (C10.outcome_evidence, offsets 139987–140047) | yes / no |
| Q93 | `outcome:C10.2` | outcome for `windows-m365-support` | exam, no level (no rubric yet), provisional | `Module 1 - CompTIA A+ 220-1102 Operating System Management` (C10.outcome_evidence.2, offsets 140843–140901) | yes / no |

### P04: Registered nurse, Manchester (`registered-nurse-manchester`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q94 | `option:C03` | credential | no formal qualification | `No formal qualification` (C03.qualification, offsets 110609–110632) | yes / no |
| Q95 | `option:C03` | assessment | no other assessment | `Apart from this, you do not need to sit for any other assessments.` (C03.assessment, offsets 133685–133751) | yes / no |
| Q96 | `option:C03` | fact: stated_purpose | skills to work as a nursing assistant | `will teach you the skills and techniques needed to work as a Nursing Assistant.` (C03.stated_purpose, offsets 2840–2919) | yes / no |
| Q97 | `offering:C03` | fee_total | £19.00 | `<span class="current-price">&#163;19</span>` (C03.fee_total, offsets 109362–109405) | yes / no |
| Q98 | `offering:C03` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q99 | `offering:C03` | intake | unknown: not stated on the page | (no span) | yes / no |
| Q100 | `offering:C03` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q101 | `offering:C03` | duration | 18 hours | `18 hours` (C03.duration, offsets 109983–109991) | yes / no |
| Q102 | `offering:C03` | schedule | unknown: not stated on the page | (no span) | yes / no |
| Q103 | `offering:C03` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q104 | `offering:C03` | extra_cost | £13.99 | `Certificate of completion - &pound;13.99` (C03.extra_cost, offsets 110944–110984) | yes / no |
| Q105 | `outcome:C03.1` | outcome for `nmc-registration` | topic_mention, no level (no rubric yet), unsupported | `No formal qualification` (C03.outcome_evidence, offsets 110609–110632) | yes / no |
| Q106 | `option:C08` | credential | a degree and eligibility to register with the Nursing and Midwifery Council (NMC) | `Become eligible to register with the Nursing and Midwifery Council (NMC) while also receiving a degree at the end of three years of study.` (C08.credential, offsets 55358–55496) | yes / no |
| Q107 | `option:C08` | recognising_body | Nursing and Midwifery Council (NMC) | `The course is approved by the Nursing and Midwifery Council (NMC), the UK regulator for nursing and midwifery professions.` (C08.recognising_body, offsets 86904–87026) | yes / no |
| Q108 | `option:C08` | assessment | written and multiple-choice exams, essays, case studies and online work | `Unit assessments vary and include written and multiple-choice exams, essays, case studies and online work.` (C08.assessment, offsets 67600–67706) | yes / no |
| Q109 | `option:C08` | entry requirement | BBC including specific subjects | `BBC including specific subjects` (C08.entry_requirement, offsets 48983–49014) | yes / no |
| Q110 | `option:C08` | fact: fee_per_year_home | £10,050.00 per year | `£10,050 per annum` (C08.fee_per_year_home, offsets 109059–109076) | yes / no |
| Q111 | `option:C08` | fact: fee_per_year_international | £35,300.00 per year | `£35,300 per annum` (C08.fee_per_year_international, offsets 109126–109143) | yes / no |
| Q112 | `option:C08` | fact: practice_assessment | skills in practice assessed by practice assessors and supervisors | `Most units of learning also include the assessment of relevant skills in practice, which are carried out by practice assessors and practice supervisors.` (C08.practice_assessment, offsets 67718–67870) | yes / no |
| Q113 | `option:C08` | fact: pass_rule | all theory and practice assessments must be passed | `To complete the course, you are required to pass all theory and practice assessments.` (C08.pass_rule, offsets 67882–67967) | yes / no |
| Q114 | `option:C08` | fact: conditions | health screening and an Enhanced DBS check | `All offers of a place are subject to satisfactory health screening and an Enhanced Disclosure and Barring Service (DBS) check` (C08.conditions, offsets 115606–115731) | yes / no |
| Q115 | `offering:C08` | fee_total | unknown: a per-year fee is stated (C08.fee_per_year_home, from September 2027); no total over the three years is stated | (no span) | yes / no |
| Q116 | `offering:C08` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q117 | `offering:C08` | intake | 2027-09 | `Tuition fees for home students commencing their studies in September 2027 will be £10,050 per annum.` (C08.intake, offsets 108977–109077) | yes / no |
| Q118 | `offering:C08` | application_deadline | unknown: the UCAS deadline is not on this page | (no span) | yes / no |
| Q119 | `offering:C08` | duration | 3 years | `3 years/4 years for MNurs` (C08.duration, offsets 48124–48149) | yes / no |
| Q120 | `offering:C08` | schedule | unknown: not stated on the page | (no span) | yes / no |
| Q121 | `offering:C08` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q122 | `offering:C08` | support_grant | at least £5,000.00 per year | `will receive a payment of at least £5,000 a year which they will not need to pay back` (C08.support_grant, offsets 110239–110324) | yes / no |
| Q123 | `outcome:C08.1` | outcome for `nmc-registration` | assessed_work_sample, no level (no rubric yet), provisional | `Become eligible to register with the Nursing and Midwifery Council (NMC) while also receiving a degree at the end of three years of study.` (C08.outcome_evidence, offsets 55358–55496) | yes / no |

### P05: Bookkeeping assistant, Leeds (`bookkeeping-assistant-leeds`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q124 | `option:C02` | level | 1 | `, Level 1` (C02.level, offsets 153468–153477) | yes / no |
| Q125 | `option:C02` | assessment | unknown (null) | `Learning outcomes:` (C02.assessment, offsets 158248–158266) | yes / no |
| Q126 | `option:C02` | entry requirement | Maths and English, preferably level 2 (GCSE), or assessments | `You will need a good standard of Maths and English, preferably at Level 2 (GCSE) or equivalent.` (C02.entry_requirement, offsets 158784–158879) | yes / no |
| Q127 | `option:C02` | fact: duration | 14 weeks | `Taking the form of a 14-week online programme, this course will introduce the` (C02.duration, offsets 157315–157392) | yes / no |
| Q128 | `option:C02` | fact: duration_conflict | 12 weeks | `12 weeks` (C02.duration_conflict, offsets 160870–160878) | yes / no |
| Q129 | `offering:C02` | fee_total | £900.00 | `Fees: £900` (C02.fee_total, offsets 158048–158058) | yes / no |
| Q130 | `offering:C02` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q131 | `offering:C02` | intake | unknown: not stated on the page | (no span) | yes / no |
| Q132 | `offering:C02` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q133 | `offering:C02` | duration | unknown: the page states two durations (C02.duration, C02.duration_conflict): unresolved | (no span) | yes / no |
| Q134 | `offering:C02` | schedule | part time | `Part time` (C02.study_type, offsets 161196–161205) | yes / no |
| Q135 | `offering:C02` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q136 | `offering:C02` | fee_condition | may be free depending on circumstances (ask the college) | `Please note this course may be free depending on student circumstances,` (C02.fee_condition, offsets 157924–157995) | yes / no |
| Q137 | `outcome:C02.1` | outcome for `records` | topic_mention, no level (no rubric yet), unsupported | `Process customer and supplier transactions` (C02.outcome_evidence, offsets 158601–158643) | yes / no |
| Q138 | `outcome:C02.2` | outcome for `reconciliation` | topic_mention, no level (no rubric yet), unsupported | `Process receipts and payments` (C02.outcome_evidence.2, offsets 158651–158680) | yes / no |
| Q139 | `option:C05` | credential | eligibility for AAT associate bookkeeping membership (AATQB) | `associate bookkeeping membership and achieve professional AATQB status. You will` (C05.credential, offsets 160152–160232) | yes / no |
| Q140 | `option:C05` | level | 3 | `, Level 3` (C05.level, offsets 153207–153216) | yes / no |
| Q141 | `option:C05` | entry requirement | AAT2 Certificate in Accounting with merit or distinction, or equivalent | `Completion of the AAT2 Certificate in Accounting with Merit or` (C05.prerequisite, offsets 162692–162754) | yes / no |
| Q142 | `offering:C05` | fee_total | unknown (null) | `Please note this course may be free depending on student circumstances,` (C05.fee_total, offsets 161319–161390) | yes / no |
| Q143 | `offering:C05` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q144 | `offering:C05` | intake | 2027-09-13 | `13/09/2027` (C05.intake, offsets 165073–165083) | yes / no |
| Q145 | `offering:C05` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q146 | `offering:C05` | duration | 1 years | `1 year` (C05.duration, offsets 164769–164775) | yes / no |
| Q147 | `offering:C05` | schedule | part time | `The course is ‘part-time online taught’ on a morning AND afternoon and will` (C05.schedule, offsets 160347–160422) | yes / no |
| Q148 | `offering:C05` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q149 | `outcome:C05.1` | outcome for `records` | topic_mention, no level (no rubric yet), unsupported | `Financial Accounting: Preparing Financial Statements: Covers the` (C05.outcome_evidence, offsets 161689–161753) | yes / no |
| Q150 | `option:C06` | level | 2 | `, Level 2` (C06.level, offsets 153190–153199) | yes / no |
| Q151 | `option:C06` | assessment | exams taken at the college | `Online taught, only exams to be taken in the college` (C06.assessment, offsets 157004–157056) | yes / no |
| Q152 | `option:C06` | entry requirement | level 2 maths and English (GCSE grade 4 or above) or equivalent, or assessments | `hold a level 2 mathematics and English qualification (GCSE at level 4 or` (C06.entry_requirement, offsets 159121–159193) | yes / no |
| Q153 | `option:C06` | fact: intakes_stated | ["2026-02", "2026-03"] | `Start dates in February and March 2026` (C06.intakes_stated, offsets 156400–156438) | yes / no |
| Q154 | `offering:C06` | fee_total | £1,265.00 | `Fees: £1265` (C06.fee_total, offsets 158053–158064) | yes / no |
| Q155 | `offering:C06` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q156 | `offering:C06` | intake | unknown: no future intake stated: the page's start dates (C06.intakes_stated) are before its retrieval date | (no span) | yes / no |
| Q157 | `offering:C06` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q158 | `offering:C06` | duration | 1 years | `1 year` (C06.duration, offsets 161868–161874) | yes / no |
| Q159 | `offering:C06` | schedule | part time | `Part time` (C06.study_type, offsets 162192–162201) | yes / no |
| Q160 | `offering:C06` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q161 | `offering:C06` | fee_condition | may be free depending on circumstances (ask the college) | `Please note this course may be free depending on student circumstances,` (C06.fee_condition, offsets 157936–158007) | yes / no |
| Q162 | `outcome:C06.1` | outcome for `records` | exam, no level (no rubric yet), provisional | `Principles of Bookkeeping Controls:` (C06.outcome_evidence, offsets 158371–158406) | yes / no |
| Q163 | `outcome:C06.2` | outcome for `reconciliation` | exam, no level (no rubric yet), provisional | `Introduction to Bookkeeping:` (C06.outcome_evidence.2, offsets 158194–158222) | yes / no |
| Q164 | `option:C09` | credential | AAT Level 3 Diploma in Accounting (within the apprenticeship) | `It includes the AAT Level 3 Diploma in Accounting` (C09.credential, offsets 32412–32461) | yes / no |
| Q165 | `option:C09` | entry requirement | GCSE maths and English at grade 4 or above | `Maths &amp; English (grade 4 and above)` (C09.entry_requirement, offsets 33614–33653) | yes / no |
| Q166 | `option:C09` | fact: standard | Assistant accountant (level 3) | `Assistant accountant (level 3)` (C09.standard, offsets 24463–24493) | yes / no |
| Q167 | `offering:C09` | fee_total | unknown: the page states no fee or cost to the apprentice (that apprentices pay no training fee is a funding rule this page does not state): unknown, never 0 | (no span) | yes / no |
| Q168 | `offering:C09` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q169 | `offering:C09` | intake | 2027-01-04 | `Monday 4 January 2027` (C09.intake, offsets 25379–25400) | yes / no |
| Q170 | `offering:C09` | application_deadline | 2026-11-30 | `Closes on Monday 30 November 2026` (C09.application_deadline, offsets 19272–19305) | yes / no |
| Q171 | `offering:C09` | duration | 18 months | `1 year 6 months` (C09.duration, offsets 25761–25776) | yes / no |
| Q172 | `offering:C09` | schedule | 35 hours a week | `35 hours a week` (C09.weekly_hours, offsets 24972–24987) | yes / no |
| Q173 | `offering:C09` | wage | £14,560.00 per year, advertised | `&#xA3;14,560 a year` (C09.wage, offsets 23588–23607) | yes / no |
| Q174 | `outcome:C09.1` | outcome for `reconciliation` | practice, no level (no rubric yet), provisional | `Complete bank and account reconciliations and resolve discrepancies` (C09.outcome_evidence, offsets 27115–27182) | yes / no |
| Q175 | `outcome:C09.2` | outcome for `records` | practice, no level (no rubric yet), provisional | `Maintain purchase and sales ledger records` (C09.outcome_evidence.2, offsets 27063–27105) | yes / no |

### Funding (P01, P03, P05)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q176 | `funding:F01` | instrument kind and award state | fee_waiver, award state not_assessed | `If you’re eligible, you will not have to pay for your qualification. The government will pay the course fees.` (F01.instrument_kind, offsets 5262–5371) | yes / no |
| Q177 | `funding:F01` | eligible_costs | course fees only | `The government will pay the course fees.` (F01.eligible_costs, offsets 5331–5371) | yes / no |
| Q178 | `funding:F01` | published_on | 2021-04-01 | `1 April 2021` (F01.published_on, offsets 44102–44114) | yes / no |
| Q179 | `funding:F01` | rules_updated_on | 2025-07-29 | `29 July 2025` (F01.rules_updated_on, offsets 44238–44250) | yes / no |
| Q180 | `funding:F01` | timing | unknown: when and to whom it is paid is not stated on the page | (no span) | yes / no |
| Q181 | `funding:F01` | repayment | unknown: not a loan | (no span) | yes / no |
| Q182 | `funding:F01` | rule_age | {"minimum_age": 19} | `aged 19 or over` (F01.rule_age, offsets 4290–4305) | yes / no |
| Q183 | `funding:F01` | rule_earnings | {"below_annual_gross": {"currency": "GBP", "minor_units": 2575000}, "or_unemployed": true} | `earn below £25,750 or are unemployed` (F01.rule_earnings, offsets 7233–7269) | yes / no |
| Q184 | `funding:F01` | rule_local_variation | in some areas the earnings limit and prior-qualification rules differ: check with the local provider | `In some areas, there may be slightly different rules about the maximum amount you can earn and the qualifications you already have.` (F01.rule_local_variation, offsets 7318–7449) | yes / no |
| Q185 | `funding:F01` | eligible_courses_level_3 | a level 3 qualification in a listed subject (including accounting and finance, digital, health and social care) | `Study for a level 3 qualification in:` (F01.eligible_courses_level_3, offsets 5564–5601) | yes / no |
| Q186 | `funding:F01` | eligible_courses_level_2 | a level 2 qualification in construction, engineering or manufacturing | `in construction, engineering or manufacturing` (F01.eligible_courses_level_2, offsets 4712–4757) | yes / no |
| Q187 | `funding:F01` | fact: rules_version_note | earnings threshold £25,750 under the adult skills fund funding and performance management rules 2025 to 2026 | `Updated the earnings threshold from £25,000 to £25,750 to reflect the adult skills fund: funding and performance management rules 2025 to 2026.` (F01.rules_version_note, offsets 45194–45337) | yes / no |
| Q188 | `funding:F01` | fact: eligible_subject_digital | digital | `digital` (F01.eligible_subject_digital, offsets 5918–5925) | yes / no |
| Q189 | `funding:F01` | fact: eligible_subject_accounting | accounting and finance | `accounting and finance` (F01.eligible_subject_accounting, offsets 5651–5673) | yes / no |
| Q190 | `funding:F01` | fact: award_status | not awarded: eligibility is checked by the provider at admission | `If you’re accepted, you will not have to pay a course fee.` (F01.award_status, offsets 8665–8723) | yes / no |
| Q191 | `funding:F01` | fact: universal_credit_interaction | many claimants can train full-time for up to 16 weeks and keep claiming | `Many Universal Credit claimants can take full-time training for up to 16 weeks and continue to claim benefit.` (F01.universal_credit_interaction, offsets 10004–10113) | yes / no |
| Q192 | `funding:F02` | instrument kind and award state | loan, award state not_assessed | `Whether you qualify for an Advanced Learner Loan depends on your:` (F02.instrument_kind, offsets 4553–4618) | yes / no |
| Q193 | `funding:F02` | eligible_costs | unknown: not stated on the page | (no span) | yes / no |
| Q194 | `funding:F02` | published_on | unknown: not stated on the page | (no span) | yes / no |
| Q195 | `funding:F02` | rules_updated_on | unknown: not stated on the page | (no span) | yes / no |
| Q196 | `funding:F02` | timing | unknown: when and to whom it is paid is not stated on the page | (no span) | yes / no |
| Q197 | `funding:F02` | repayment | Advanced Learner Loans, repaid when earning over a threshold | `are available to help you cover the costs of learning, which you pay back when you’re earning over a certain amount.` (F01.alternative_if_ineligible, offsets 10504–10620) | yes / no |
| Q198 | `funding:F02` | rule_age | {"minimum_age": 19, "on": "first day of the course"} | `You must be 19 or older on the first day of your course.` (F02.rule_age, offsets 4884–4940) | yes / no |
| Q199 | `funding:F02` | rule_course_level | {"levels": [3, 4, 5, 6]} | `Level 3, 4, 5 or 6 qualification` (F02.rule_course_level, offsets 5107–5139) | yes / no |
| Q200 | `funding:F02` | rule_provider | an approved college or training provider in England | `at an approved college or training provider in England` (F02.rule_provider, offsets 5208–5262) | yes / no |
| Q201 | `funding:F02` | rule_residency | living in the UK on the first day; a UK national, Irish citizen or settled; 3 years' residence before the course (with listed exceptions) | `have been living in the UK, British overseas territories, the Channel Islands or the Isle of Man for 3 years in a row before the first day of your course` (F02.rule_residency, offsets 6573–6726) | yes / no |
| Q202 | `funding:F02` | lle_interaction | {"levels": [4, 5, 6], "courses_starting_on_or_after": "2027-01-01", "use_instead": "Lifelong Learning Entitlement funding"} | `studying a level 4, 5 or 6 qualification on a course that starts on or after 1 January 2027 - apply for student finance through your` (F02.lle_interaction, offsets 5653–5785) | yes / no |
| Q203 | `funding:F02` | htq_interaction | level 4 or 5 Higher Technical Qualifications use undergraduate funding instead | `studying a level 4 or 5 qualification with Higher Technical Qualification approval - apply for` (F02.htq_interaction, offsets 5433–5527) | yes / no |
| Q204 | `funding:F03` | instrument kind and award state | programme, award state not_assessed | (no claim) | yes / no |
| Q205 | `funding:F03` | eligible_costs | unknown: not stated on the page | (no span) | yes / no |
| Q206 | `funding:F03` | published_on | unknown: not stated on the page | (no span) | yes / no |
| Q207 | `funding:F03` | rules_updated_on | unknown: not stated on the page | (no span) | yes / no |
| Q208 | `funding:F03` | timing | unknown: when and to whom it is paid is not stated on the page | (no span) | yes / no |
| Q209 | `funding:F03` | repayment | unknown: not a loan | (no span) | yes / no |
| Q210 | `funding:F03` | rule_age | {"minimum_age": 19} | `You need to be 19 or over to do a Skills Bootcamp.` (F03.rule_age, offsets 123142–123192) | yes / no |
| Q211 | `funding:F03` | rule_course_specific | some bootcamps add entry requirements, listed in the course details | `Some courses may have additional entry requirements, such as needing you to have a certain qualification or experience.` (F03.rule_course_specific, offsets 123442–123561) | yes / no |
| Q212 | `funding:F03` | duration_limit | up to 16 weeks | `Skills Bootcamps take up to 16 weeks to complete.` (F03.duration_limit, offsets 122564–122613) | yes / no |
| Q213 | `funding:F03` | fact: outcome_offer | a guaranteed job interview with an employer after finishing | `After you’ve finished your Skills Bootcamp, you’re guaranteed a job interview with an employer.` (F03.outcome_offer, offsets 126470–126565) | yes / no |
| Q214 | `funding:F03` | fact: cost_to_learner | unknown (null) | `course fees` (F03.cost_to_learner, offsets 127384–127395) | yes / no |
| Q215 | `funding:F03` | fact: digital_subjects | digital, including data engineering, software development and marketing | `, including data engineering, software development and marketing` (F03.digital_subjects, offsets 121542–121606) | yes / no |

## Part 3: P03–P05's job postings and requirements (Q216–Q331, about 29 minutes)

Closes the job labels; Task 8 may take any rows left over.

### P03: IT support technician, Bristol (`it-support-technician-bristol`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q216 | `job:J01` | salary | up to £28,000.00 per year, advertised | `Up to £28,000 per annum (depending on experience) + Benefits` (J01.salary, offsets 4557–4617) | yes / no |
| Q217 | `job:J01` | valid_through | 2026-11-27T23:59:59+00:00 | `2026-11-27T23:59:59.000Z` (J01.valid_through, offsets 9451–9475) | yes / no |
| Q218 | `job:J01` | location | Bristol, South West England (locality Bristol; region South West England) | `Hybrid - Bristol, South West England` (J01.location, offsets 4651–4687) | yes / no |
| Q219 | `job:J01` | advertiser | unknown | `AWD online` (J01.advertiser, offsets 9069–9079) | yes / no |
| Q220 | `job:J01` | employer | AWD online | `AWD online` (J01.employer, offsets 9069–9079) | yes / no |
| Q221 | `job:J01` | fact: salary_point | £28,000.00 per year, advertised | `{"@type":"MonetaryAmount","currency":"GBP","value":{"@type":"QuantitativeValue","value":28000,"unitText":"YEAR"}}` (J01.salary_point, offsets 9842–9955) | yes / no |
| Q222 | `req:J01.4` | requirement (essential, eligibility, gate: work rights) | Right to work in the UK is required; visa sponsorship is not available | `Right to work in the UK is required; visa sponsorship is not available` (J01.requirement.4, offsets 8290–8360) | yes / no |
| Q223 | `job:J02` | salary | £28,000.00 per unstated period, advertised | `{"salary_min": 28000, "salary_max": 28000, "salary_is_predicted": "0"}` (J02.salary, pointer /results/6) | yes / no |
| Q224 | `job:J02` | valid_through | unknown: not stated on the page | (no span) | yes / no |
| Q225 | `job:J02` | location | Bristol, South West England (region South West England) | `{"__CLASS__": "Adzuna::API::Response::Location", "area": ["UK", "South West England", "Bristol"], "display_name": "Brist` (J02.location, pointer /results/6/location) | yes / no |
| Q226 | `job:J02` | advertiser | unknown | `{"display_name": "AWD online", "__CLASS__": "Adzuna::API::Response::Company"}` (J02.advertiser, pointer /results/6/company) | yes / no |
| Q227 | `job:J02` | employer | AWD online | `{"display_name": "AWD online", "__CLASS__": "Adzuna::API::Response::Company"}` (J02.employer, pointer /results/6/company) | yes / no |
| Q228 | `job:J02` | fact: duplicate_of | J01 | `"Junior IT Support Technician / Service Desk Analyst – Full Training Provided Build your IT support career in a collabor` (J02.duplicate_of, pointer /results/6/description) | yes / no |
| Q229 | `job:J03` | salary | £34,275.31 per unstated period, predicted | `{"salary_min": 34275.31, "salary_max": 34275.31, "salary_is_predicted": "1"}` (J03.salary, pointer /results/0) | yes / no |
| Q230 | `job:J03` | valid_through | unknown: not stated on the page | (no span) | yes / no |
| Q231 | `job:J03` | location | Temple Meads, Bristol (locality Temple Meads; region South West England) | `{"area": ["UK", "South West England", "Bristol", "Temple Meads"], "display_name": "Temple Meads, Bristol", "__CLASS__":` (J03.location, pointer /results/0/location) | yes / no |
| Q232 | `job:J03` | advertiser | unknown | `{"__CLASS__": "Adzuna::API::Response::Company", "display_name": "Tekever"}` (J03.advertiser, pointer /results/0/company) | yes / no |
| Q233 | `job:J03` | employer | Tekever | `{"__CLASS__": "Adzuna::API::Response::Company", "display_name": "Tekever"}` (J03.employer, pointer /results/0/company) | yes / no |
| Q234 | `job:J07` | salary | £28,000.00 per unstated period, advertised | `{"salary_min": 28000, "salary_max": 28000, "salary_is_predicted": "0"}` (J07.salary, pointer /results/5) | yes / no |
| Q235 | `job:J07` | valid_through | unknown: not stated on the page | (no span) | yes / no |
| Q236 | `job:J07` | location | Bristol, South West England (region South West England) | `{"display_name": "Bristol, South West England", "area": ["UK", "South West England", "Bristol"], "__CLASS__": "Adzuna::A` (J07.location, pointer /results/5/location) | yes / no |
| Q237 | `job:J07` | advertiser | unknown | `{"display_name": "AWD online", "__CLASS__": "Adzuna::API::Response::Company"}` (J07.advertiser, pointer /results/5/company) | yes / no |
| Q238 | `job:J07` | employer | AWD online | `{"display_name": "AWD online", "__CLASS__": "Adzuna::API::Response::Company"}` (J07.employer, pointer /results/5/company) | yes / no |
| Q239 | `job:J14` | salary | £16.37 per hour, advertised | `£16.37 per hour` (J14.salary, offsets 3797–3812) | yes / no |
| Q240 | `job:J14` | valid_through | 2026-11-18T23:55:00+00:00 | `2026-11-18T23:55:00.000Z` (J14.valid_through, offsets 8592–8616) | yes / no |
| Q241 | `job:J14` | location | Yate, Bristol (locality Yate) | `Yate, Bristol` (J14.location, offsets 3705–3718) | yes / no |
| Q242 | `job:J14` | advertiser | agency | `Adecco are pleased to be recruiting for a` (J14.advertiser, offsets 3539–3580) | yes / no |
| Q243 | `job:J14` | employer | South Gloucestershire Council | `to work within the South Gloucestershire Council.` (J14.employer, offsets 3622–3671) | yes / no |
| Q244 | `job:J14` | fact: contract_end | 2027-01 | `January, 2027` (J14.contract_end, offsets 3843–3856) | yes / no |
| Q245 | `req:J14.1` | requirement (essential, credential, no gate) | Relevant qualification (e.g., NVQ Level 3) or equivalent practical experience. | `Relevant qualification (e.g., NVQ Level 3) or equivalent practical experience.` (J14.requirement, offsets 6051–6129) | yes / no |
| Q246 | `req:J14.3` | requirement (essential, skill, row service-desk-ticketing) | Familiarity with ITIL-aligned service processes and a solid understanding of Halo ITSM. | `Familiarity with ITIL-aligned service processes and a solid understanding of Halo ITSM.` (J14.requirement.3, offsets 6237–6324) | yes / no |
| Q247 | `req:J14.4` | requirement (essential, skill, row windows-m365-support) | Proficient in Windows devices, Microsoft 365, SCCM, Azure, Intune, Active Directory, and Microsoft Entra ID. | `Proficient in Windows devices, Microsoft 365, SCCM, Azure, Intune, Active Directory, and Microsoft Entra ID.` (J14.requirement.4, offsets 6333–6441) | yes / no |
| Q248 | `job:J15` | salary | £32,073.00–£39,043.00 per year, advertised | `£32,073 to £39,043 a year` (J15.salary, offsets 18656–18681) | yes / no |
| Q249 | `job:J15` | valid_through | 2026-10-30 | `The closing date is 30 October 2026` (J15.valid_through, offsets 13292–13327) | yes / no |
| Q250 | `job:J15` | location | BS2 8EJ (postal code BS2 8EJ) | `BS2 8EJ` (J15.location, offsets 19982–19989) | yes / no |
| Q251 | `job:J15` | advertiser | employer | `Bristol NHS Foundation Trust` (J15.advertiser, offsets 12947–12975) | yes / no |
| Q252 | `job:J15` | employer | Bristol NHS Foundation Trust | `Bristol NHS Foundation Trust` (J15.employer, offsets 12947–12975) | yes / no |
| Q253 | `req:J15.2` | requirement (essential, skill, row windows-m365-support) | Sound knowledge of Windows operating systems and M365 applications | `Sound knowledge of Windows operating systems and M365 applications` (J15.requirement.2, offsets 24073–24139) | yes / no |
| Q254 | `req:J15.3` | requirement (essential, skill, row hardware-troubleshooting) | Demonstrable hardware fault finding/resolution ability | `Demonstrable hardware fault finding/resolution ability for desktop computer equipment, peripherals, and mobile devices` (J15.requirement.3, offsets 24306–24424) | yes / no |
| Q255 | `req:J15.4` | requirement (essential, eligibility, no gate) | Valid UK driving license | `Valid UK driving license` (J15.requirement.4, offsets 25431–25455) | yes / no |
| Q256 | `req:J15.5` | requirement (essential, credential, no gate) | Educated to A level standard or equivalent | `Educated to A level standard or equivalent` (J15.requirement.5, offsets 21583–21625) | yes / no |
| Q257 | `req:J15.6` | requirement (preferred, credential, row service-desk-ticketing) | ITIL Practitioner | `ITIL Practitioner` (J15.requirement.6, offsets 22224–22241) | yes / no |

### P04: Registered nurse, Manchester (`registered-nurse-manchester`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q258 | `job:J06` | salary | unknown: the page states two pay ranges that disagree (J06.salary, J06.salary_conflict): unresolved | (no span) | yes / no |
| Q259 | `job:J06` | valid_through | 2026-12-31 | `The closing date is 31 December 2026` (J06.valid_through, offsets 13274–13310) | yes / no |
| Q260 | `job:J06` | location | M13 0YL (postal code M13 0YL) | `M13 0YL` (J06.location, offsets 18105–18112) | yes / no |
| Q261 | `job:J06` | advertiser | employer | `Equilibrium Healthcare` (J06.advertiser, offsets 12947–12969) | yes / no |
| Q262 | `job:J06` | employer | Equilibrium Healthcare | `Equilibrium Healthcare` (J06.employer, offsets 12947–12969) | yes / no |
| Q263 | `job:J06` | fact: occupation_crosswalk | {"candidates": ["2235 Registered mental health nurses", "2237 Other registered nursing professionals"], "resolved": null} | `Registered Nurse (RMN/RGN)` (J06.occupation_crosswalk, offsets 13065–13091) | yes / no |
| Q264 | `job:J06` | fact: salary | £17.50–£20.23 per hour, advertised | `£17.50 to £20.23 an hour` (J06.salary, offsets 16673–16697) | yes / no |
| Q265 | `job:J06` | fact: salary_conflict | £18.50–£20.23 per hour, advertised | `Salary: £18.50-£20.23 per hour (40,000 to 44,000)` (J06.salary_conflict, offsets 20618–20667) | yes / no |
| Q266 | `req:J06.1` | requirement (essential, credential, gate: statutory registration, row nmc-registration) | NMC registration | `NMC registration` (J06.requirement, offsets 20878–20894) | yes / no |
| Q267 | `req:J06.2` | requirement (essential, credential, gate: statutory registration, row nmc-registration) | active NMC pin | `active NMC pin` (J06.requirement.2, offsets 14610–14624) | yes / no |
| Q268 | `job:J09` | salary | £33,353.66–£37,522.87 per year, advertised | `£33,353.66 to £37,522.87 a year` (J09.salary, offsets 17096–17127) | yes / no |
| Q269 | `job:J09` | valid_through | 2026-11-09 | `The closing date is 09 November 2026` (J09.valid_through, offsets 13279–13315) | yes / no |
| Q270 | `job:J09` | location | M14 6XG (postal code M14 6XG) | `M14 6XG` (J09.location, offsets 18586–18593) | yes / no |
| Q271 | `job:J09` | advertiser | employer | `MSI Reproductive Choices` (J09.advertiser, offsets 12947–12971) | yes / no |
| Q272 | `job:J09` | employer | MSI Reproductive Choices | `MSI Reproductive Choices` (J09.employer, offsets 12947–12971) | yes / no |
| Q273 | `job:J09` | fact: work_locations | ["Greater Manchester", "Blackpool", "Liverpool", "Preston"] | `Travel is an essential part of this role, with work across Greater Manchester and our centres in Blackpool, Liverpool and Preston.` (J09.work_locations, offsets 14900–15030) | yes / no |
| Q274 | `req:J09.1` | requirement (essential, credential, gate: statutory registration, row nmc-registration) | Registered Adult Nurse or Registered Midwife with a current and valid Nursing and Midwifery Council Pin | `You must be a Registered Adult Nurse or Registered Midwife with a current and valid Nursing and Midwifery Council Pin` (J09.requirement, offsets 14058–14175) | yes / no |
| Q275 | `req:J09.2` | requirement (essential, credential, gate: statutory registration, row nmc-registration) | current UK professional registration | `Applicants must have current UK professional registration.` (J09.requirement.2, offsets 21583–21641) | yes / no |
| Q276 | `job:J10` | salary | £32,073.00–£39,043.00 per year, advertised | `£32,073 to £39,043 a year` (J10.salary, offsets 18107–18132) | yes / no |
| Q277 | `job:J10` | valid_through | 2026-11-11 | `The closing date is 11 November 2026` (J10.valid_through, offsets 13304–13340) | yes / no |
| Q278 | `job:J10` | location | OL6 6NG (postal code OL6 6NG) | `OL6 6NG` (J10.location, offsets 19538–19545) | yes / no |
| Q279 | `job:J10` | advertiser | employer | `Tameside and Glossop Integrated Care NHS Foundation Trust` (J10.advertiser, offsets 12947–13004) | yes / no |
| Q280 | `job:J10` | employer | Tameside and Glossop Integrated Care NHS Foundation Trust | `Tameside and Glossop Integrated Care NHS Foundation Trust` (J10.employer, offsets 12947–13004) | yes / no |
| Q281 | `req:J10.1` | requirement (essential, credential, gate: statutory registration (pending allowed within two months), row nmc-registration) | Registered nurse or pending registration within two months | `Registered nurse or pending registration within two months` (J10.requirement, offsets 21668–21726) | yes / no |
| Q282 | `req:J10.2` | requirement (essential, eligibility, no gate) | Ability to travel to various locations between Tameside and Glossop | `Ability to travel to various locations between Tameside and Glossop` (J10.requirement.2, offsets 21896–21963) | yes / no |
| Q283 | `job:J11` | salary | £36,486.00 per year, advertised | `£36,486 a year` (J11.salary, offsets 16973–16987) | yes / no |
| Q284 | `job:J11` | valid_through | 2026-10-30 | `The closing date is 30 October 2026` (J11.valid_through, offsets 13258–13293) | yes / no |
| Q285 | `job:J11` | location | M6 7DU (postal code M6 7DU) | `M6 7DU` (J11.location, offsets 18257–18263) | yes / no |
| Q286 | `job:J11` | advertiser | employer | `Elysium Healthcare` (J11.advertiser, offsets 12947–12965) | yes / no |
| Q287 | `job:J11` | employer | Elysium Healthcare | `Elysium Healthcare` (J11.employer, offsets 12947–12965) | yes / no |
| Q288 | `job:J11` | fact: occupation_crosswalk | {"candidates": ["2235 Registered mental health nurses", "2237 Other registered nursing professionals"], "resolved": null} | `As a qualified Nurse (RMN or RNLD)` (J11.occupation_crosswalk, offsets 14897–14931) | yes / no |
| Q289 | `req:J11.1` | requirement (essential, credential, gate: statutory registration, row nmc-registration) | A relevant nursing qualification, NMC registration | `A relevant nursing qualification, NMC registration` (J11.requirement, offsets 30500–30550) | yes / no |
| Q290 | `job:J13` | salary | £32,073.00–£39,043.00 per year, advertised | `£32,073 to £39,043 a year` (J13.salary, offsets 18108–18133) | yes / no |
| Q291 | `job:J13` | valid_through | 2026-11-03 | `The closing date is 03 November 2026` (J13.valid_through, offsets 13277–13313) | yes / no |
| Q292 | `job:J13` | location | SK2 7JE (postal code SK2 7JE) | `SK2 7JE` (J13.location, offsets 19468–19475) | yes / no |
| Q293 | `job:J13` | advertiser | employer | `Stockport NHS Foundation Trust` (J13.advertiser, offsets 12947–12977) | yes / no |
| Q294 | `job:J13` | employer | Stockport NHS Foundation Trust | `Stockport NHS Foundation Trust` (J13.employer, offsets 12947–12977) | yes / no |
| Q295 | `job:J13` | fact: salary_basis_note | pro rata per annum | `pro rata per annum` (J13.salary_basis_note, offsets 18149–18167) | yes / no |
| Q296 | `job:J19` | salary | £24.95 per hour, advertised | `£24.95 per hour` (J19.salary, offsets 3933–3948) | yes / no |
| Q297 | `job:J19` | valid_through | 2026-12-09T23:55:00+00:00 | `2026-12-09T23:55:00.000Z` (J19.valid_through, offsets 6653–6677) | yes / no |
| Q298 | `job:J19` | location | unknown: the page states two places that disagree (J19.location, J19.location_conflict): unresolved | (no span) | yes / no |
| Q299 | `job:J19` | advertiser | employer | `We are offering a rewarding career as a` (J19.advertiser, offsets 3546–3585) | yes / no |
| Q300 | `job:J19` | employer | Excelcare Holdings | `Excelcare Holdings` (J19.employer, offsets 6538–6556) | yes / no |
| Q301 | `job:J19` | fact: salary_annual_statement | up to £62,275.00 per year, advertised | `Up to £62,275 per annum - £24.95 per hour (Breaks Unpaid)` (J19.salary_annual_statement, offsets 3907–3964) | yes / no |
| Q302 | `job:J19` | fact: location | Greater Manchester, Lancashire | `Greater Manchester, Lancashire` (J19.location, offsets 35347–35377) | yes / no |
| Q303 | `job:J19` | fact: location_conflict | Park Avenue Care Home, Bromley (locality Bromley) | `Registered Nurse at our Park Avenue Care Home in Bromley.` (J19.location_conflict, offsets 3594–3651) | yes / no |
| Q304 | `req:J19.1` | requirement (essential, credential, gate: statutory registration, row nmc-registration) | A valid UK NMC Pin number | `A valid UK NMC Pin number` (J19.requirement, offsets 5337–5362) | yes / no |

### P05: Bookkeeping assistant, Leeds (`bookkeeping-assistant-leeds`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q305 | `job:J04` | salary | unknown (null) | `Salary: Based on Experience` (J04.salary, offsets 3589–3616) | yes / no |
| Q306 | `job:J04` | valid_through | 2026-11-26T23:55:00+00:00 | `2026-11-26T23:55:00.000Z` (J04.valid_through, offsets 5183–5207) | yes / no |
| Q307 | `job:J04` | location | Yeadon, Leeds (locality Yeadon) | `Location: Yeadon, Leeds` (J04.location, offsets 3545–3568) | yes / no |
| Q308 | `job:J04` | advertiser | agency | `Verelogic Recruitment` (J04.advertiser, offsets 5065–5086) | yes / no |
| Q309 | `job:J04` | employer | unknown (null) | `Our client is seeking a full-time Bookkeeper to join their growing accountancy team based in Yeadon, Leeds.` (J04.employer, offsets 3664–3771) | yes / no |
| Q310 | `job:J04` | fact: salary_shown | Competitive salary | `Competitive salary` (J04.salary_shown, offsets 31155–31173) | yes / no |
| Q311 | `req:J04.2` | requirement (essential, task, row reconciliation) | Completing bank reconciliations | `Completing bank reconciliations` (J04.requirement.2, offsets 4143–4174) | yes / no |
| Q312 | `job:J08` | salary | £30,000.00–£35,000.00 per year, advertised | `£30,000 - £35,000 per annum` (J08.salary, offsets 30939–30966) | yes / no |
| Q313 | `job:J08` | valid_through | 2026-12-03T23:59:59+00:00 | `2026-12-03T23:59:59.000Z` (J08.valid_through, offsets 5159–5183) | yes / no |
| Q314 | `job:J08` | location | Leeds, West Yorkshire (locality Leeds) | `Leeds, West Yorkshire` (J08.location, offsets 31280–31301) | yes / no |
| Q315 | `job:J08` | advertiser | agency | `Synergem Recruitment` (J08.advertiser, offsets 5042–5062) | yes / no |
| Q316 | `job:J08` | employer | unknown (null) | `We're working with an established and growing business looking to recruit an experienced Accounts Assistant` (J08.employer, offsets 3557–3664) | yes / no |
| Q317 | `req:J08.2` | requirement (essential, skill, row records) | Is comfortable working across purchase and sales ledger | `Is comfortable working across purchase and sales ledger` (J08.requirement.2, offsets 4420–4475) | yes / no |
| Q318 | `job:J16` | salary | £35,000.00–£38,000.00 per year, advertised | `£35,000 - £38,000 per annum, inc benefits` (J16.salary, offsets 32309–32350) | yes / no |
| Q319 | `job:J16` | valid_through | 2026-11-02T23:59:59+00:00 | `2026-11-02T23:59:59.000Z` (J16.valid_through, offsets 6113–6137) | yes / no |
| Q320 | `job:J16` | location | Leeds City Centre (locality Leeds) | `Leeds City Centre` (J16.location, offsets 3723–3740) | yes / no |
| Q321 | `job:J16` | advertiser | unknown | `PRATAP PARTNERSHIP LTD` (J16.advertiser, offsets 5994–6016) | yes / no |
| Q322 | `job:J16` | employer | PRATAP PARTNERSHIP LTD | `PRATAP PARTNERSHIP LTD` (J16.employer, offsets 5994–6016) | yes / no |
| Q323 | `job:J17` | salary | £25,760.00–£27,476.00 per year, advertised | `£25,760 to £27,476 a year` (J17.salary, offsets 17980–18005) | yes / no |
| Q324 | `job:J17` | valid_through | 2026-11-02 | `The closing date is 02 November 2026` (J17.valid_through, offsets 13284–13320) | yes / no |
| Q325 | `job:J17` | location | LS11 0DL (postal code LS11 0DL) | `LS11 0DL` (J17.location, offsets 19454–19462) | yes / no |
| Q326 | `job:J17` | advertiser | employer | `Leeds Community Healthcare NHS Trust` (J17.advertiser, offsets 12947–12983) | yes / no |
| Q327 | `job:J17` | employer | Leeds Community Healthcare NHS Trust | `Leeds Community Healthcare NHS Trust` (J17.employer, offsets 12947–12983) | yes / no |
| Q328 | `job:J17` | fact: contract_duration | 4 months | `4 months` (J17.contract_duration, offsets 18298–18306) | yes / no |
| Q329 | `job:J17` | fact: contract_end | 2027-03-31 | `This role is fixed term until 31st March 2027.` (J17.contract_end, offsets 15638–15684) | yes / no |
| Q330 | `job:J17` | fact: early_close | may close early when the maximum number of applicants is reached | `Adverts will close early where the maximum number of applicants is reached.` (J17.early_close, offsets 15804–15879) | yes / no |
| Q331 | `req:J17.1` | requirement (essential, eligibility, gate: work rights) | the right to work in the UK | `Employment is conditional on confirmation of the right to work in the UK` (J17.requirement, offsets 16957–17029) | yes / no |
