# Session 2 package: the England option pack 0.1.0 (H-07)

- **Status:** agent preparation (Task 7b, 2026-10-29). The review is not run - requires
  human (H-07, ruling R2). Nothing in this file is an answer.
- **For:** the H-07 domain reviewer at session 2. Task 7c applies the answers.
- **What:** 314 yes/no questions. They cover every consequential field of every record in
  `backend/src/nessa/catalogue/packs/england_option_pack/england-option-pack-0.1.0.json`,
  grouped by persona target, each beside the span it cites.
  - Consequential means pay and its basis, fees, dates, deadlines, award status, outcome
    levels, gates, eligibility rules and the conflicts a page leaves open.
  - P02 has no target in the fixture, so it has no records. Its cities are covered by the
    other targets.
- **Time:** about 80 minutes at 15 seconds a row. If session time is short, answer
  "Answer these first" below. An undecided record stays `proposed`.

## How to answer

1. Read the row's excerpt. Open the page if you need its context: each slot's URL is in
   `corpus/manifest.json`.
2. Write **yes** if the page states the value as shown, with its unit, period and basis. For
   an "unknown" row, yes means the page does not state it.
3. Write **no** otherwise, with the right reading and where it is on the page.
4. Leave a row blank if you cannot decide.

What Task 7c does with the answers (OPTN-10):

- It publishes them as a new dated pack version.
- An accepted record becomes `review_state: reviewed`, with reviewer and date.
- A rejected record is left out.
- A corrected value is cited to its span.
- An undecided record stays `proposed`.
- Version 0.1.0 is not changed.

## Reading the rows

- **Money** is shown in pounds and pence. "?" is a bound the page does not state.
  "advertised" or "predicted" is the pay basis. "per unstated period" means the source gives
  no period (Adzuna's figures).
- **Excerpts** are shown as code, exactly as in the hashed text, with runs of whitespace
  collapsed. So HTML appears as written: `&#163;`, `&pound;` and `&#xA3;` are £, and
  `&#8217;` is ’. Adzuna excerpts are the API's JSON, cut at 120 characters.
- **Offsets** index the page's text after redaction (third parties' contact details are
  removed before hashing). A pointer is a JSON pointer into the Adzuna response.
- **The live page may have changed** since 2026-10-29. Answer from the excerpt, and note
  any difference you see.
- **Outcome rows** give the evidence kind (topic_mention, practice, exam or
  assessed_work_sample), then the level, then the confidence. No rubric exists yet, so no
  outcome has a level (Task 9 adds them).
- **Requirement rows** are asked only when the requirement is mapped to a target's skill row
  or carries a gate (registration, right to work).
- **Not asked:** titles, posting dates and source IDs. Rights are a separate human gate
  (OI-07); C08 is pending rights review.

## Answer these first

These are the labels where the agent made a judgment call, or where a wrong answer changes a
route:

- **Conflicts left open:** Q129 and Q135 (J06's two pay ranges), Q169 and Q171 (J19's
  place), Q230, Q231 and Q236 (C02's two durations).
- **Pay read as a bound:** Q64 (J01's "Up to £28,000", although the JSON-LD gives one
  value) and Q170 (J19).
- **Fees unknown, never 0:** Q36 (C01), Q192 (C08), Q244 (C05), Q266 (C09), Q313 (F03).
- **Gates and eligibility:** Q113 (C07's residency rule excludes Bristol), Q136, Q144,
  Q151, Q158 and Q172 (NMC registration), Q282 and Q283 (F01's earnings rule).
- **Award states and outcomes:** Q275, Q289, Q291, Q296 and Q303, and every outcome row
  marked `provisional`.

## P01: Data quality analyst, Manchester (`data-quality-analyst-manchester`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q1 | `job:J05` | salary | £31,049.00–£37,796.00 per year, advertised | `£31,049 to £37,796 a year` (J05.salary, offsets 17643–17668) | yes / no |
| Q2 | `job:J05` | valid_through | unknown: the closed page shows no closing date | (no span) | yes / no |
| Q3 | `job:J05` | status | closed | `This job is now closed` (J05.status, offsets 13331–13353) | yes / no |
| Q4 | `job:J05` | advertiser | employer | `North West Ambulance Service NHS Trust` (J05.advertiser, offsets 12947–12985) | yes / no |
| Q5 | `job:J05` | employer | North West Ambulance Service NHS Trust | `North West Ambulance Service NHS Trust` (J05.employer, offsets 12947–12985) | yes / no |
| Q6 | `job:J05` | location | {"label": "Estuary Point/Middlebrook/Parkway, M14 7LU", "postal_code": "M14 7LU"} | `M14 7LU` (J05.location, offsets 19177–19184) | yes / no |
| Q7 | `job:J05` | contract_duration | {"months": 12} | `12 months` (J05.contract_duration, offsets 17986–17995) | yes / no |
| Q8 | `req:J05.1` | requirement (essential, row independent-querying) | Proficiency in SQL (T-SQL) for data extraction and manipulation | `Proficiency in SQL (T-SQL) for data extraction and manipulation` (J05.requirement, offsets 24187–24250) | yes / no |
| Q9 | `req:J05.2` | requirement (essential, row data-validation) | Experience of investigating and resolving data quality issues | `Experience of investigating and resolving data quality issues` (J05.requirement.2, offsets 24440–24501) | yes / no |
| Q10 | `req:J05.6` | requirement (essential, row communication) | Effective communication at all levels, both internally and externally | `Effective communication at all levels, both internally and externally` (J05.requirement.6, offsets 22273–22343) | yes / no |
| Q11 | `job:J12` | salary | £38,000.00–£45,000.00 per year, advertised | `£38,000 - £45,000 per annum` (J12.salary, offsets 33623–33650) | yes / no |
| Q12 | `job:J12` | valid_through | 2026-11-03T23:55:00+00:00 | `2026-11-03T23:55:00.000Z` (J12.valid_through, offsets 7236–7260) | yes / no |
| Q13 | `job:J12` | advertiser | agency | `Cathcart Technology is acting as an Employment Agency in relation to this vacancy.` (J12.advertiser, offsets 6986–7068) | yes / no |
| Q14 | `job:J12` | employer | unknown (null) | `An established and highly successful digital business is looking for a Data Analyst` (J12.employer, offsets 3617–3700) | yes / no |
| Q15 | `job:J12` | location | {"label": "Greater Manchester", "locality": "Manchester", "region": "North West England"} | `Greater Manchester / Hybrid role (2-3 days on-site)` (J12.location, offsets 3539–3590) | yes / no |
| Q16 | `req:J12.1` | requirement (preferred, row independent-querying) | Good SQL skills and confidence querying relational databases | `Good SQL skills and confidence querying relational databases` (J12.requirement, offsets 6081–6141) | yes / no |
| Q17 | `req:J12.3` | requirement (preferred, row communication) | Strong communication skills and the confidence to explain findings to non-technical stakeholders | `Strong communication skills and the confidence to explain findings to non-technical stakeholders` (J12.requirement.3, offsets 6312–6408) | yes / no |
| Q18 | `job:J18` | salary | £44,000.00–£46,500.00 per year, advertised | `£44,000 - £46,500 per annum` (J18.salary, offsets 31749–31776) | yes / no |
| Q19 | `job:J18` | valid_through | 2026-12-02T23:59:59+00:00 | `2026-12-02T23:59:59.000Z` (J18.valid_through, offsets 5495–5519) | yes / no |
| Q20 | `job:J18` | advertiser | unknown | `Consula Group LTD` (J18.advertiser, offsets 5381–5398) | yes / no |
| Q21 | `job:J18` | employer | unknown (null) | `A well-regarded organisation is looking for a capable Data Analyst` (J18.employer, offsets 3501–3568) | yes / no |
| Q22 | `job:J18` | location | {"label": "Manchester, Lancashire", "locality": "Manchester"} | `Manchester, Lancashire` (J18.location, offsets 32090–32112) | yes / no |
| Q23 | `req:J18.1` | requirement (essential, row independent-querying) | Strong skills in Excel and at least one tool such as SQL, Power BI or Python. | `Strong skills in Excel and at least one tool such as SQL, Power BI or Python.` (J18.requirement, offsets 4618–4695) | yes / no |
| Q24 | `req:J18.2` | requirement (essential, row data-validation) | Maintaining data quality, accuracy and consistency in reporting. | `Maintaining data quality, accuracy and consistency in reporting.` (J18.requirement.2, offsets 4299–4363) | yes / no |
| Q25 | `req:J18.3` | requirement (essential, row communication) | The ability to explain analysis simply to non-technical colleagues. | `The ability to explain analysis simply to non-technical colleagues.` (J18.requirement.3, offsets 4784–4851) | yes / no |
| Q26 | `job:J20` | salary | £35,000.00–£45,000.00 per year, advertised | `£35,000 - £45,000 per annum` (J20.salary, offsets 33521–33548) | yes / no |
| Q27 | `job:J20` | valid_through | 2026-12-07T23:55:00+00:00 | `2026-12-07T23:55:00.000Z` (J20.valid_through, offsets 7689–7713) | yes / no |
| Q28 | `job:J20` | advertiser | agency | `We’re working with a growing retail business that’s investing heavily in data` (J20.advertiser, offsets 3602–3679) | yes / no |
| Q29 | `job:J20` | employer | unknown (null) | `We’re working with a growing retail business that’s investing heavily in data` (J20.employer, offsets 3602–3679) | yes / no |
| Q30 | `job:J20` | location | {"label": "Manchester", "locality": "Manchester"} | `Hybrid working in Manchester, 2 days per week` (J20.location, offsets 6164–6209) | yes / no |
| Q31 | `req:J20.1` | requirement (essential, row independent-querying) | Strong SQL skills | `Strong SQL skills` (J20.requirement, offsets 5535–5552) | yes / no |
| Q32 | `req:J20.3` | requirement (essential, row communication) | Strong communication skills and confidence working with stakeholders | `Strong communication skills and confidence working with stakeholders` (J20.requirement.3, offsets 5777–5845) | yes / no |
| Q33 | `option:C01` | credential | NCFE Level 3 Certificate in Data | `NCFE Level 3 Certificate in Data` (C01.credential, offsets 58911–58943) | yes / no |
| Q34 | `option:C01` | level | 3 | `NCFE Level 3 Certificate in Data` (C01.level, offsets 58911–58943) | yes / no |
| Q35 | `option:C01` | assessment | unknown (null) | `Learn, certify, succeed` (C01.assessment, offsets 60061–60084) | yes / no |
| Q36 | `offering:C01` | fee_total | unknown (null) | `Take on our fully funded data analyst course` (C01.fee_total, offsets 53424–53468) | yes / no |
| Q37 | `offering:C01` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q38 | `offering:C01` | intake | unknown: no start date is stated | (no span) | yes / no |
| Q39 | `offering:C01` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q40 | `offering:C01` | duration | {"full_time_weeks": 10, "part_time_weeks": 17} | `10 weeks full-time, 17 weeks part-time` (C01.duration, offsets 55850–55888) | yes / no |
| Q41 | `offering:C01` | schedule | unknown: no weekly hours or timetable are stated | (no span) | yes / no |
| Q42 | `offering:C01` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q43 | `offering:C01` | funding_route | Adult Skills Fund / Free Courses for Jobs | `Adult Skills Fund / Free Courses for Jobs` (C01.funding_route, offsets 59794–59835) | yes / no |
| Q44 | `offering:C01` | eligibility_area | Greater Manchester or the West Midlands | `You live in the West Midlands or Greater Manchester` (C01.eligibility_area, offsets 62203–62254) | yes / no |
| Q45 | `offering:C01` | eligibility_age | {"minimum_age": 19} | `You&#8217;re aged 19 or over` (C01.eligibility_age, offsets 62482–62510) | yes / no |
| Q46 | `offering:C01` | eligibility_earnings | {"below_annual_gross": {"currency": "GBP", "minor_units": 3240000}, "area": "Greater Manchester"} | `You earn below the gross annual wage cap of £34,194 (West Midlands)/£32,400 (Manchester)` (C01.eligibility_earnings, offsets 62738–62826) | yes / no |
| Q47 | `offering:C01` | eligibility_no_other_funded_training | true | `You&#8217;re not currently undertaking any other government-funded training` (C01.eligibility_no_other_funded_training, offsets 63054–63129) | yes / no |
| Q48 | `outcome:C01.1` | outcome for `independent-querying` | topic_mention, no level (no rubric yet), unsupported | `and manipulation techniques to help you prep raw data for analysis, including using SQL.` (C01.outcome_evidence, offsets 71869–71957) | yes / no |
| Q49 | `outcome:C01.2` | outcome for `data-validation` | topic_mention, no level (no rubric yet), unsupported | `Data validation and quality` (C01.outcome_evidence.2, offsets 72928–72955) | yes / no |
| Q50 | `outcome:C01.3` | outcome for `communication` | topic_mention, no level (no rubric yet), unsupported | `Communicating and presenting data` (C01.outcome_evidence.3, offsets 73856–73889) | yes / no |
| Q51 | `option:C04` | credential | Microsoft Power BI Data Analyst (PL-300) among four Microsoft certifications | `Power BI Data Analyst (PL-300)` (C04.credential, offsets 4495–4525) | yes / no |
| Q52 | `option:C04` | offer_kind | training course listed as a job | `Training Course` (C04.offer_kind, offsets 32731–32746) | yes / no |
| Q53 | `option:C04` | provider_outcome_claim | 98% of students secure a role upon graduation (no method or denominator) | `98% of students secure a role upon graduation` (C04.provider_outcome_claim, offsets 5503–5548) | yes / no |
| Q54 | `offering:C04` | fee_total | £2,995.00 | `£2995 or from £69.52/month` (C04.fee_total, offsets 6676–6702) | yes / no |
| Q55 | `offering:C04` | instalment | £69.52 per month | `£2995 or from £69.52/month` (C04.instalment, offsets 6676–6702) | yes / no |
| Q56 | `offering:C04` | intake | unknown: not stated on the page | (no span) | yes / no |
| Q57 | `offering:C04` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q58 | `offering:C04` | duration | {"typical_months": "6-8", "access_months": 12} | `one year of 24/7 access to all training material, with an average completion time of 6-8 months` (C04.duration, offsets 5809–5904) | yes / no |
| Q59 | `offering:C04` | schedule | unknown: not stated on the page | (no span) | yes / no |
| Q60 | `offering:C04` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q61 | `offering:C04` | funding | self-funded | `Self-funded career programme with a guaranteed job on completion, or 100% of your course fees back` (C04.funding, offsets 6713–6811) | yes / no |
| Q62 | `outcome:C04.1` | outcome for `independent-querying` | practice, no level (no rubric yet), provisional | `Write and optimise SQL queries, clean and manipulate datasets with Python` (C04.outcome_evidence, offsets 4951–5024) | yes / no |
| Q63 | `outcome:C04.2` | outcome for `data-validation` | practice, no level (no rubric yet), unsupported | `clean and manipulate datasets with Python` (C04.outcome_evidence.2, offsets 4983–5024) | yes / no |

## P03: IT support technician, Bristol (`it-support-technician-bristol`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q64 | `job:J01` | salary | ?–£28,000.00 per year, advertised | `Up to £28,000 per annum (depending on experience) + Benefits` (J01.salary, offsets 4557–4617) | yes / no |
| Q65 | `job:J01` | valid_through | 2026-11-27T23:59:59+00:00 | `2026-11-27T23:59:59.000Z` (J01.valid_through, offsets 9451–9475) | yes / no |
| Q66 | `job:J01` | advertiser | unknown | `AWD online` (J01.advertiser, offsets 9069–9079) | yes / no |
| Q67 | `job:J01` | employer | AWD online | `AWD online` (J01.employer, offsets 9069–9079) | yes / no |
| Q68 | `job:J01` | location | {"label": "Bristol, South West England", "locality": "Bristol", "region": "South West England"} | `Hybrid - Bristol, South West England` (J01.location, offsets 4651–4687) | yes / no |
| Q69 | `req:J01.4` | requirement (essential, gate: work rights) | Right to work in the UK is required; visa sponsorship is not available | `Right to work in the UK is required; visa sponsorship is not available` (J01.requirement.4, offsets 8290–8360) | yes / no |
| Q70 | `job:J02` | salary | £28,000.00–£28,000.00 per unstated period, advertised | `{"salary_min": 28000, "salary_max": 28000, "salary_is_predicted": "0"}` (J02.salary, pointer /results/6) | yes / no |
| Q71 | `job:J02` | valid_through | unknown: not stated on the page | (no span) | yes / no |
| Q72 | `job:J02` | advertiser | unknown | `{"display_name": "AWD online", "__CLASS__": "Adzuna::API::Response::Company"}` (J02.advertiser, pointer /results/6/company) | yes / no |
| Q73 | `job:J02` | employer | AWD online | `{"display_name": "AWD online", "__CLASS__": "Adzuna::API::Response::Company"}` (J02.employer, pointer /results/6/company) | yes / no |
| Q74 | `job:J02` | location | {"label": "Bristol, South West England", "region": "South West England"} | `{"__CLASS__": "Adzuna::API::Response::Location", "area": ["UK", "South West England", "Bristol"], "display_name": "Brist` (J02.location, pointer /results/6/location) | yes / no |
| Q75 | `job:J02` | duplicate_of | J01 | `"Junior IT Support Technician / Service Desk Analyst – Full Training Provided Build your IT support career in a collabor` (J02.duplicate_of, pointer /results/6/description) | yes / no |
| Q76 | `job:J03` | salary | £34,275.31–£34,275.31 per unstated period, predicted | `{"salary_min": 34275.31, "salary_max": 34275.31, "salary_is_predicted": "1"}` (J03.salary, pointer /results/0) | yes / no |
| Q77 | `job:J03` | valid_through | unknown: not stated on the page | (no span) | yes / no |
| Q78 | `job:J03` | advertiser | unknown | `{"__CLASS__": "Adzuna::API::Response::Company", "display_name": "Tekever"}` (J03.advertiser, pointer /results/0/company) | yes / no |
| Q79 | `job:J03` | employer | Tekever | `{"__CLASS__": "Adzuna::API::Response::Company", "display_name": "Tekever"}` (J03.employer, pointer /results/0/company) | yes / no |
| Q80 | `job:J03` | location | {"label": "Temple Meads, Bristol", "locality": "Temple Meads", "region": "South West England"} | `{"area": ["UK", "South West England", "Bristol", "Temple Meads"], "display_name": "Temple Meads, Bristol", "__CLASS__":` (J03.location, pointer /results/0/location) | yes / no |
| Q81 | `job:J07` | salary | £28,000.00–£28,000.00 per unstated period, advertised | `{"salary_min": 28000, "salary_max": 28000, "salary_is_predicted": "0"}` (J07.salary, pointer /results/5) | yes / no |
| Q82 | `job:J07` | valid_through | unknown: not stated on the page | (no span) | yes / no |
| Q83 | `job:J07` | advertiser | unknown | `{"display_name": "AWD online", "__CLASS__": "Adzuna::API::Response::Company"}` (J07.advertiser, pointer /results/5/company) | yes / no |
| Q84 | `job:J07` | employer | AWD online | `{"display_name": "AWD online", "__CLASS__": "Adzuna::API::Response::Company"}` (J07.employer, pointer /results/5/company) | yes / no |
| Q85 | `job:J07` | location | {"label": "Bristol, South West England", "region": "South West England"} | `{"display_name": "Bristol, South West England", "area": ["UK", "South West England", "Bristol"], "__CLASS__": "Adzuna::A` (J07.location, pointer /results/5/location) | yes / no |
| Q86 | `job:J14` | salary | £16.37–£16.37 per hour, advertised | `£16.37 per hour` (J14.salary, offsets 3797–3812) | yes / no |
| Q87 | `job:J14` | valid_through | 2026-11-18T23:55:00+00:00 | `2026-11-18T23:55:00.000Z` (J14.valid_through, offsets 8592–8616) | yes / no |
| Q88 | `job:J14` | advertiser | agency | `Adecco are pleased to be recruiting for a` (J14.advertiser, offsets 3539–3580) | yes / no |
| Q89 | `job:J14` | employer | South Gloucestershire Council | `to work within the South Gloucestershire Council.` (J14.employer, offsets 3622–3671) | yes / no |
| Q90 | `job:J14` | location | {"label": "Yate, Bristol", "locality": "Yate"} | `Yate, Bristol` (J14.location, offsets 3705–3718) | yes / no |
| Q91 | `job:J14` | contract_end | 2027-01 | `January, 2027` (J14.contract_end, offsets 3843–3856) | yes / no |
| Q92 | `req:J14.3` | requirement (essential, row service-desk-ticketing) | Familiarity with ITIL-aligned service processes and a solid understanding of Halo ITSM. | `Familiarity with ITIL-aligned service processes and a solid understanding of Halo ITSM.` (J14.requirement.3, offsets 6237–6324) | yes / no |
| Q93 | `req:J14.4` | requirement (essential, row windows-m365-support) | Proficient in Windows devices, Microsoft 365, SCCM, Azure, Intune, Active Directory, and Microsoft Entra ID. | `Proficient in Windows devices, Microsoft 365, SCCM, Azure, Intune, Active Directory, and Microsoft Entra ID.` (J14.requirement.4, offsets 6333–6441) | yes / no |
| Q94 | `job:J15` | salary | £32,073.00–£39,043.00 per year, advertised | `£32,073 to £39,043 a year` (J15.salary, offsets 18656–18681) | yes / no |
| Q95 | `job:J15` | valid_through | 2026-10-30 | `The closing date is 30 October 2026` (J15.valid_through, offsets 13292–13327) | yes / no |
| Q96 | `job:J15` | advertiser | employer | `Bristol NHS Foundation Trust` (J15.advertiser, offsets 12947–12975) | yes / no |
| Q97 | `job:J15` | employer | Bristol NHS Foundation Trust | `Bristol NHS Foundation Trust` (J15.employer, offsets 12947–12975) | yes / no |
| Q98 | `job:J15` | location | {"label": "Digital HQ, 40 Southwell Street, Bristol, BS2 8EJ", "locality": "Bristol", "postal_code": "BS2 8EJ"} | `BS2 8EJ` (J15.location, offsets 19982–19989) | yes / no |
| Q99 | `req:J15.2` | requirement (essential, row windows-m365-support) | Sound knowledge of Windows operating systems and M365 applications | `Sound knowledge of Windows operating systems and M365 applications` (J15.requirement.2, offsets 24073–24139) | yes / no |
| Q100 | `req:J15.3` | requirement (essential, row hardware-troubleshooting) | Demonstrable hardware fault finding/resolution ability | `Demonstrable hardware fault finding/resolution ability for desktop computer equipment, peripherals, and mobile devices` (J15.requirement.3, offsets 24306–24424) | yes / no |
| Q101 | `req:J15.6` | requirement (preferred, row service-desk-ticketing) | ITIL Practitioner | `ITIL Practitioner` (J15.requirement.6, offsets 22224–22241) | yes / no |
| Q102 | `option:C07` | level | 3 | `Education level</th> <td class="govuk-table__cell"><span id="awarding-organisation">3</span>` (C07.level, offsets 21651–21751) | yes / no |
| Q103 | `option:C07` | assessment | the opportunity to sit CompTIA A+ and Microsoft exams | `You will prove that you have the skills and knowledge, by taking the opportunity to achieve the CompTIA A+ and Microsoft exams.` (C07.assessment, offsets 26728–26855) | yes / no |
| Q104 | `option:C07` | description_inconsistency | an IT course whose text also speaks of data skills and data careers | `No prior experience is needed, just a keen interest in working with data.` (C07.description_inconsistency, offsets 24343–24416) | yes / no |
| Q105 | `offering:C07` | fee_total | £0.00 | `£0.00` (C07.fee_total, offsets 23145–23150) | yes / no |
| Q106 | `offering:C07` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q107 | `offering:C07` | intake | 2026-11-16 | `16th November 2026` (C07.intake, offsets 22904–22922) | yes / no |
| Q108 | `offering:C07` | application_deadline | unknown: no application deadline is stated | (no span) | yes / no |
| Q109 | `offering:C07` | duration | {"weeks": 12} | `The 12-week programme will enable you to develop the skills and knowledge needed to start your career in IT` (C07.duration, offsets 26555–26662) | yes / no |
| Q110 | `offering:C07` | schedule | unknown: not stated on the page | (no span) | yes / no |
| Q111 | `offering:C07` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q112 | `offering:C07` | eligibility_age | {"minimum_age": 19} | `Aged 19+` (C07.eligibility_age, offsets 25563–25571) | yes / no |
| Q113 | `offering:C07` | eligibility_residency | ["London", "North Yorkshire", "West Midlands", "North East England"] | `Must reside in London, North Yorkshire, West Midlands or the Northeast area of England.` (C07.eligibility_residency, offsets 25605–25692) | yes / no |
| Q114 | `offering:C07` | eligibility_work_rights | right to work in the UK | `Have the right to work in the UK` (C07.eligibility_work_rights, offsets 25572–25604) | yes / no |
| Q115 | `outcome:C07.1` | outcome for `hardware-troubleshooting` | exam, no level (no rubric yet), provisional | `completing official courses in CompTIA A+, and Microsoft 365` (C07.outcome_evidence, offsets 26666–26726) | yes / no |
| Q116 | `outcome:C07.2` | outcome for `windows-m365-support` | exam, no level (no rubric yet), provisional | `completing official courses in CompTIA A+, and Microsoft 365` (C07.outcome_evidence.2, offsets 26666–26726) | yes / no |
| Q117 | `option:C10` | credential | CompTIA A+ (professional certification, issued by CompTIA on passing its exams) | `Professional certification` (C10.credential, offsets 111285–111311) | yes / no |
| Q118 | `option:C10` | price_valid_until | 2026-10-31 | `Offer ends 31 October 2026` (C10.price_valid_until, offsets 108607–108633) | yes / no |
| Q119 | `offering:C10` | fee_total | £295.00 | `<span class="current-price">&#163;295</span>` (C10.fee_total, offsets 108437–108481) | yes / no |
| Q120 | `offering:C10` | instalment | {"count": 3, "interest_free": true} | `evenly with 3 Easy Payments` (C10.instalment, offsets 109039–109066) | yes / no |
| Q121 | `offering:C10` | intake | unknown: not stated on the page | (no span) | yes / no |
| Q122 | `offering:C10` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q123 | `offering:C10` | duration | {"hours": 60, "self_paced": true} | `60 hours` (C10.duration, offsets 110468–110476) | yes / no |
| Q124 | `offering:C10` | schedule | unknown: not stated on the page | (no span) | yes / no |
| Q125 | `offering:C10` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q126 | `offering:C10` | exam_fee | unknown (null) | `CompTIA exam fees are not included` (C10.exam_fee, offsets 137827–137861) | yes / no |
| Q127 | `outcome:C10.1` | outcome for `hardware-troubleshooting` | exam, no level (no rubric yet), provisional | `Module 1 - CompTIA A+ 220-1101 Devices, Setups, and Installs` (C10.outcome_evidence, offsets 139987–140047) | yes / no |
| Q128 | `outcome:C10.2` | outcome for `windows-m365-support` | exam, no level (no rubric yet), provisional | `Module 1 - CompTIA A+ 220-1102 Operating System Management` (C10.outcome_evidence.2, offsets 140843–140901) | yes / no |

## P04: Registered nurse, Manchester (`registered-nurse-manchester`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q129 | `job:J06` | salary | unknown: the page states two pay ranges that disagree (J06.salary, J06.salary_conflict): unresolved | (no span) | yes / no |
| Q130 | `job:J06` | valid_through | 2026-12-31 | `The closing date is 31 December 2026` (J06.valid_through, offsets 13274–13310) | yes / no |
| Q131 | `job:J06` | advertiser | employer | `Equilibrium Healthcare` (J06.advertiser, offsets 12947–12969) | yes / no |
| Q132 | `job:J06` | employer | Equilibrium Healthcare | `Equilibrium Healthcare` (J06.employer, offsets 12947–12969) | yes / no |
| Q133 | `job:J06` | location | {"label": "Oaklands House Nursing Home, Dickenson Road, Manchester, M13 0YL", "locality": "Manchester", "postal_code": "M13 0YL"} | `M13 0YL` (J06.location, offsets 18105–18112) | yes / no |
| Q134 | `job:J06` | occupation_crosswalk | {"candidates": ["2235 Registered mental health nurses", "2237 Other registered nursing professionals"], "resolved": null} | `Registered Nurse (RMN/RGN)` (J06.occupation_crosswalk, offsets 13065–13091) | yes / no |
| Q135 | `job:J06` | salary_conflict | £18.50–£20.23 per hour, advertised | `Salary: £18.50-£20.23 per hour (40,000 to 44,000)` (J06.salary_conflict, offsets 20618–20667) | yes / no |
| Q136 | `req:J06.1` | requirement (essential, gate: statutory registration, row nmc-registration) | NMC registration (an active NMC pin) | `NMC registration` (J06.requirement, offsets 20878–20894) | yes / no |
| Q137 | `req:J06.2` | requirement (essential, gate: statutory registration, row nmc-registration) | active NMC pin | `active NMC pin` (J06.requirement.2, offsets 14610–14624) | yes / no |
| Q138 | `job:J09` | salary | £33,353.66–£37,522.87 per year, advertised | `£33,353.66 to £37,522.87 a year` (J09.salary, offsets 17096–17127) | yes / no |
| Q139 | `job:J09` | valid_through | 2026-11-09 | `The closing date is 09 November 2026` (J09.valid_through, offsets 13279–13315) | yes / no |
| Q140 | `job:J09` | advertiser | employer | `MSI Reproductive Choices` (J09.advertiser, offsets 12947–12971) | yes / no |
| Q141 | `job:J09` | employer | MSI Reproductive Choices | `MSI Reproductive Choices` (J09.employer, offsets 12947–12971) | yes / no |
| Q142 | `job:J09` | location | {"label": "5 Wynnstay Grove, Manchester, M14 6XG", "locality": "Manchester", "postal_code": "M14 6XG"} | `M14 6XG` (J09.location, offsets 18586–18593) | yes / no |
| Q143 | `job:J09` | work_locations | ["Greater Manchester", "Blackpool", "Liverpool", "Preston"] | `Travel is an essential part of this role, with work across Greater Manchester and our centres in Blackpool, Liverpool and Preston.` (J09.work_locations, offsets 14900–15030) | yes / no |
| Q144 | `req:J09.1` | requirement (essential, gate: statutory registration, row nmc-registration) | Registered Adult Nurse or Registered Midwife with a current and valid Nursing and Midwifery Council Pin | `You must be a Registered Adult Nurse or Registered Midwife with a current and valid Nursing and Midwifery Council Pin` (J09.requirement, offsets 14058–14175) | yes / no |
| Q145 | `req:J09.2` | requirement (essential, gate: statutory registration, row nmc-registration) | current UK professional registration | `Applicants must have current UK professional registration.` (J09.requirement.2, offsets 21583–21641) | yes / no |
| Q146 | `job:J10` | salary | £32,073.00–£39,043.00 per year, advertised | `£32,073 to £39,043 a year` (J10.salary, offsets 18107–18132) | yes / no |
| Q147 | `job:J10` | valid_through | 2026-11-11 | `The closing date is 11 November 2026` (J10.valid_through, offsets 13304–13340) | yes / no |
| Q148 | `job:J10` | advertiser | employer | `Tameside and Glossop Integrated Care NHS Foundation Trust` (J10.advertiser, offsets 12947–13004) | yes / no |
| Q149 | `job:J10` | employer | Tameside and Glossop Integrated Care NHS Foundation Trust | `Tameside and Glossop Integrated Care NHS Foundation Trust` (J10.employer, offsets 12947–13004) | yes / no |
| Q150 | `job:J10` | location | {"label": "Tameside DN Bases, Tameside, OL6 6NG", "locality": "Tameside", "postal_code": "OL6 6NG"} | `OL6 6NG` (J10.location, offsets 19538–19545) | yes / no |
| Q151 | `req:J10.1` | requirement (essential, gate: statutory registration (pending allowed within two months), row nmc-registration) | Registered nurse or pending registration within two months | `Registered nurse or pending registration within two months` (J10.requirement, offsets 21668–21726) | yes / no |
| Q152 | `job:J11` | salary | £36,486.00–£36,486.00 per year, advertised | `£36,486 a year` (J11.salary, offsets 16973–16987) | yes / no |
| Q153 | `job:J11` | valid_through | 2026-10-30 | `The closing date is 30 October 2026` (J11.valid_through, offsets 13258–13293) | yes / no |
| Q154 | `job:J11` | advertiser | employer | `Elysium Healthcare` (J11.advertiser, offsets 12947–12965) | yes / no |
| Q155 | `job:J11` | employer | Elysium Healthcare | `Elysium Healthcare` (J11.employer, offsets 12947–12965) | yes / no |
| Q156 | `job:J11` | location | {"label": "Braeburn House, Salford, M6 7DU", "locality": "Salford", "postal_code": "M6 7DU"} | `M6 7DU` (J11.location, offsets 18257–18263) | yes / no |
| Q157 | `job:J11` | occupation_crosswalk | {"candidates": ["2235 Registered mental health nurses", "2237 Other registered nursing professionals"], "resolved": null} | `As a qualified Nurse (RMN or RNLD)` (J11.occupation_crosswalk, offsets 14897–14931) | yes / no |
| Q158 | `req:J11.1` | requirement (essential, gate: statutory registration, row nmc-registration) | A relevant nursing qualification, NMC registration | `A relevant nursing qualification, NMC registration` (J11.requirement, offsets 30500–30550) | yes / no |
| Q159 | `job:J13` | salary | £32,073.00–£39,043.00 per year, advertised | `£32,073 to £39,043 a year` (J13.salary, offsets 18108–18133) | yes / no |
| Q160 | `job:J13` | valid_through | 2026-11-03 | `The closing date is 03 November 2026` (J13.valid_through, offsets 13277–13313) | yes / no |
| Q161 | `job:J13` | advertiser | employer | `Stockport NHS Foundation Trust` (J13.advertiser, offsets 12947–12977) | yes / no |
| Q162 | `job:J13` | employer | Stockport NHS Foundation Trust | `Stockport NHS Foundation Trust` (J13.employer, offsets 12947–12977) | yes / no |
| Q163 | `job:J13` | location | {"label": "Ward C6, Stepping Hill Hospital, Poplar Grove, Stockport, SK2 7JE", "locality": "Stockport", "postal_code": "SK2 7JE"} | `SK2 7JE` (J13.location, offsets 19468–19475) | yes / no |
| Q164 | `job:J13` | salary_basis_note | pro rata per annum | `pro rata per annum` (J13.salary_basis_note, offsets 18149–18167) | yes / no |
| Q165 | `job:J19` | salary | £24.95–£24.95 per hour, advertised | `£24.95 per hour` (J19.salary, offsets 3933–3948) | yes / no |
| Q166 | `job:J19` | valid_through | 2026-12-09T23:55:00+00:00 | `2026-12-09T23:55:00.000Z` (J19.valid_through, offsets 6653–6677) | yes / no |
| Q167 | `job:J19` | advertiser | employer | `We are offering a rewarding career as a` (J19.advertiser, offsets 3546–3585) | yes / no |
| Q168 | `job:J19` | employer | Excelcare Holdings | `Excelcare Holdings` (J19.employer, offsets 6538–6556) | yes / no |
| Q169 | `job:J19` | location | unknown (null) | `Greater Manchester, Lancashire` (J19.location, offsets 35347–35377) | yes / no |
| Q170 | `job:J19` | salary_annual_statement | ?–£62,275.00 per year, advertised | `Up to £62,275 per annum - £24.95 per hour (Breaks Unpaid)` (J19.salary_annual_statement, offsets 3907–3964) | yes / no |
| Q171 | `job:J19` | location_conflict | {"label": "Park Avenue Care Home, Bromley", "locality": "Bromley"} | `Registered Nurse at our Park Avenue Care Home in Bromley.` (J19.location_conflict, offsets 3594–3651) | yes / no |
| Q172 | `req:J19.1` | requirement (essential, gate: statutory registration, row nmc-registration) | A valid UK NMC Pin number | `A valid UK NMC Pin number` (J19.requirement, offsets 5337–5362) | yes / no |
| Q173 | `option:C03` | credential | no formal qualification | `No formal qualification` (C03.qualification, offsets 110609–110632) | yes / no |
| Q174 | `option:C03` | assessment | quizzes only (60% to unlock later modules); no other assessment | `Apart from this, you do not need to sit for any other assessments.` (C03.assessment, offsets 133685–133751) | yes / no |
| Q175 | `option:C03` | stated_purpose | skills to work as a nursing assistant | `will teach you the skills and techniques needed to work as a Nursing Assistant.` (C03.stated_purpose, offsets 2840–2919) | yes / no |
| Q176 | `offering:C03` | fee_total | £19.00 | `<span class="current-price">&#163;19</span>` (C03.fee_total, offsets 109362–109405) | yes / no |
| Q177 | `offering:C03` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q178 | `offering:C03` | intake | unknown: not stated on the page | (no span) | yes / no |
| Q179 | `offering:C03` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q180 | `offering:C03` | duration | {"hours": 18, "self_paced": true} | `18 hours` (C03.duration, offsets 109983–109991) | yes / no |
| Q181 | `offering:C03` | schedule | unknown: not stated on the page | (no span) | yes / no |
| Q182 | `offering:C03` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q183 | `offering:C03` | extra_cost | £13.99 | `Certificate of completion - &pound;13.99` (C03.extra_cost, offsets 110944–110984) | yes / no |
| Q184 | `outcome:C03.1` | outcome for `nmc-registration` | topic_mention, no level (no rubric yet), unsupported | `No formal qualification` (C03.outcome_evidence, offsets 110609–110632) | yes / no |
| Q185 | `option:C08` | credential | Bachelor of Nursing (BNurs), eligibility to register with the NMC | `Become eligible to register with the Nursing and Midwifery Council (NMC) while also receiving a degree at the end of three years of study.` (C08.credential, offsets 55358–55496) | yes / no |
| Q186 | `option:C08` | recognising_body | Nursing and Midwifery Council (NMC) | `The course is approved by the Nursing and Midwifery Council (NMC), the UK regulator for nursing and midwifery professions.` (C08.recognising_body, offsets 86904–87026) | yes / no |
| Q187 | `option:C08` | assessment | written and multiple-choice exams, essays, case studies, online work; practice assessed by practice assessors | `Unit assessments vary and include written and multiple-choice exams, essays, case studies and online work.` (C08.assessment, offsets 67600–67706) | yes / no |
| Q188 | `option:C08` | fee_per_year_home | £10,050.00 per year | `£10,050 per annum` (C08.fee_per_year_home, offsets 109059–109076) | yes / no |
| Q189 | `option:C08` | practice_assessment | skills in practice assessed by practice assessors and supervisors | `Most units of learning also include the assessment of relevant skills in practice, which are carried out by practice assessors and practice supervisors.` (C08.practice_assessment, offsets 67718–67870) | yes / no |
| Q190 | `option:C08` | pass_rule | all theory and practice assessments must be passed | `To complete the course, you are required to pass all theory and practice assessments.` (C08.pass_rule, offsets 67882–67967) | yes / no |
| Q191 | `option:C08` | conditions | health screening and an Enhanced DBS check | `All offers of a place are subject to satisfactory health screening and an Enhanced Disclosure and Barring Service (DBS) check` (C08.conditions, offsets 115606–115731) | yes / no |
| Q192 | `offering:C08` | fee_total | unknown: a per-year fee is stated (C08.fee_per_year_home, from September 2027); no total over the three years is stated | (no span) | yes / no |
| Q193 | `offering:C08` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q194 | `offering:C08` | intake | 2027-09 | `Tuition fees for home students commencing their studies in September 2027 will be £10,050 per annum.` (C08.intake, offsets 108977–109077) | yes / no |
| Q195 | `offering:C08` | application_deadline | unknown: the UCAS deadline is not on this page | (no span) | yes / no |
| Q196 | `offering:C08` | duration | {"years": 3, "mnurs_years": 4} | `3 years/4 years for MNurs` (C08.duration, offsets 48124–48149) | yes / no |
| Q197 | `offering:C08` | schedule | unknown: not stated on the page | (no span) | yes / no |
| Q198 | `offering:C08` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q199 | `offering:C08` | support_grant | £5,000.00 per year | `will receive a payment of at least £5,000 a year which they will not need to pay back` (C08.support_grant, offsets 110239–110324) | yes / no |
| Q200 | `outcome:C08.1` | outcome for `nmc-registration` | assessed_work_sample, no level (no rubric yet), provisional | `Become eligible to register with the Nursing and Midwifery Council (NMC) while also receiving a degree at the end of three years of study.` (C08.outcome_evidence, offsets 55358–55496) | yes / no |

## P05: Bookkeeping assistant, Leeds (`bookkeeping-assistant-leeds`)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q201 | `job:J04` | salary | unknown (null) | `Salary: Based on Experience` (J04.salary, offsets 3589–3616) | yes / no |
| Q202 | `job:J04` | valid_through | 2026-11-26T23:55:00+00:00 | `2026-11-26T23:55:00.000Z` (J04.valid_through, offsets 5183–5207) | yes / no |
| Q203 | `job:J04` | advertiser | agency | `Verelogic Recruitment` (J04.advertiser, offsets 5065–5086) | yes / no |
| Q204 | `job:J04` | employer | unknown (null) | `Our client is seeking a full-time Bookkeeper to join their growing accountancy team based in Yeadon, Leeds.` (J04.employer, offsets 3664–3771) | yes / no |
| Q205 | `job:J04` | location | {"label": "Yeadon, Leeds", "locality": "Yeadon"} | `Location: Yeadon, Leeds` (J04.location, offsets 3545–3568) | yes / no |
| Q206 | `job:J04` | salary_shown | Competitive salary | `Competitive salary` (J04.salary_shown, offsets 31155–31173) | yes / no |
| Q207 | `req:J04.2` | requirement (essential, row reconciliation) | Completing bank reconciliations | `Completing bank reconciliations` (J04.requirement.2, offsets 4143–4174) | yes / no |
| Q208 | `job:J08` | salary | £30,000.00–£35,000.00 per year, advertised | `£30,000 - £35,000 per annum` (J08.salary, offsets 30939–30966) | yes / no |
| Q209 | `job:J08` | valid_through | 2026-12-03T23:59:59+00:00 | `2026-12-03T23:59:59.000Z` (J08.valid_through, offsets 5159–5183) | yes / no |
| Q210 | `job:J08` | advertiser | agency | `Synergem Recruitment` (J08.advertiser, offsets 5042–5062) | yes / no |
| Q211 | `job:J08` | employer | unknown (null) | `We're working with an established and growing business looking to recruit an experienced Accounts Assistant` (J08.employer, offsets 3557–3664) | yes / no |
| Q212 | `job:J08` | location | {"label": "Leeds, West Yorkshire", "locality": "Leeds"} | `Leeds, West Yorkshire` (J08.location, offsets 31280–31301) | yes / no |
| Q213 | `req:J08.2` | requirement (essential, row records) | Is comfortable working across purchase and sales ledger | `Is comfortable working across purchase and sales ledger` (J08.requirement.2, offsets 4420–4475) | yes / no |
| Q214 | `job:J16` | salary | £35,000.00–£38,000.00 per year, advertised | `£35,000 - £38,000 per annum, inc benefits` (J16.salary, offsets 32309–32350) | yes / no |
| Q215 | `job:J16` | valid_through | 2026-11-02T23:59:59+00:00 | `2026-11-02T23:59:59.000Z` (J16.valid_through, offsets 6113–6137) | yes / no |
| Q216 | `job:J16` | advertiser | unknown | `PRATAP PARTNERSHIP LTD` (J16.advertiser, offsets 5994–6016) | yes / no |
| Q217 | `job:J16` | employer | PRATAP PARTNERSHIP LTD | `PRATAP PARTNERSHIP LTD` (J16.employer, offsets 5994–6016) | yes / no |
| Q218 | `job:J16` | location | {"label": "Leeds City Centre", "locality": "Leeds"} | `Leeds City Centre` (J16.location, offsets 3723–3740) | yes / no |
| Q219 | `job:J17` | salary | £25,760.00–£27,476.00 per year, advertised | `£25,760 to £27,476 a year` (J17.salary, offsets 17980–18005) | yes / no |
| Q220 | `job:J17` | valid_through | 2026-11-02 | `The closing date is 02 November 2026` (J17.valid_through, offsets 13284–13320) | yes / no |
| Q221 | `job:J17` | advertiser | employer | `Leeds Community Healthcare NHS Trust` (J17.advertiser, offsets 12947–12983) | yes / no |
| Q222 | `job:J17` | employer | Leeds Community Healthcare NHS Trust | `Leeds Community Healthcare NHS Trust` (J17.employer, offsets 12947–12983) | yes / no |
| Q223 | `job:J17` | location | {"label": "White Rose Office Park, Building 3, Millshaw Park Lane, Leeds, LS11 0DL", "locality": "Leeds", "postal_code": "LS11 0DL"} | `LS11 0DL` (J17.location, offsets 19454–19462) | yes / no |
| Q224 | `job:J17` | contract_duration | {"months": 4} | `4 months` (J17.contract_duration, offsets 18298–18306) | yes / no |
| Q225 | `job:J17` | contract_end | 2027-03-31 | `This role is fixed term until 31st March 2027.` (J17.contract_end, offsets 15638–15684) | yes / no |
| Q226 | `job:J17` | early_close | may close early when the maximum number of applicants is reached | `Adverts will close early where the maximum number of applicants is reached.` (J17.early_close, offsets 15804–15879) | yes / no |
| Q227 | `req:J17.1` | requirement (essential, gate: work rights) | the right to work in the UK | `Employment is conditional on confirmation of the right to work in the UK` (J17.requirement, offsets 16957–17029) | yes / no |
| Q228 | `option:C02` | level | 1 | `, Level 1` (C02.level, offsets 153468–153477) | yes / no |
| Q229 | `option:C02` | assessment | unknown (null) | `Learning outcomes:` (C02.assessment, offsets 158248–158266) | yes / no |
| Q230 | `option:C02` | duration | {"weeks": 14} | `Taking the form of a 14-week online programme, this course will introduce the` (C02.duration, offsets 157315–157392) | yes / no |
| Q231 | `option:C02` | duration_conflict | {"weeks": 12} | `12 weeks` (C02.duration_conflict, offsets 160870–160878) | yes / no |
| Q232 | `offering:C02` | fee_total | £900.00 | `Fees: £900` (C02.fee_total, offsets 158048–158058) | yes / no |
| Q233 | `offering:C02` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q234 | `offering:C02` | intake | unknown: not stated on the page | (no span) | yes / no |
| Q235 | `offering:C02` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q236 | `offering:C02` | duration | unknown: the page states two durations (C02.duration, C02.duration_conflict): unresolved | (no span) | yes / no |
| Q237 | `offering:C02` | schedule | part time | `Part time` (C02.study_type, offsets 161196–161205) | yes / no |
| Q238 | `offering:C02` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q239 | `offering:C02` | fee_condition | may be free depending on circumstances (ask the college) | `Please note this course may be free depending on student circumstances,` (C02.fee_condition, offsets 157924–157995) | yes / no |
| Q240 | `outcome:C02.1` | outcome for `records` | topic_mention, no level (no rubric yet), unsupported | `Process customer and supplier transactions` (C02.outcome_evidence, offsets 158601–158643) | yes / no |
| Q241 | `outcome:C02.2` | outcome for `reconciliation` | topic_mention, no level (no rubric yet), unsupported | `Process receipts and payments` (C02.outcome_evidence.2, offsets 158651–158680) | yes / no |
| Q242 | `option:C05` | credential | eligibility for AAT associate bookkeeping membership (AATQB) | `associate bookkeeping membership and achieve professional AATQB status. You will` (C05.credential, offsets 160152–160232) | yes / no |
| Q243 | `option:C05` | level | 3 | `, Level 3` (C05.level, offsets 153207–153216) | yes / no |
| Q244 | `offering:C05` | fee_total | unknown (null) | `Please note this course may be free depending on student circumstances,` (C05.fee_total, offsets 161319–161390) | yes / no |
| Q245 | `offering:C05` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q246 | `offering:C05` | intake | 2027-09-13 | `13/09/2027` (C05.intake, offsets 165073–165083) | yes / no |
| Q247 | `offering:C05` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q248 | `offering:C05` | duration | {"years": 1} | `1 year` (C05.duration, offsets 164769–164775) | yes / no |
| Q249 | `offering:C05` | schedule | part-time online, morning and afternoon, the full academic year | `The course is ‘part-time online taught’ on a morning AND afternoon and will` (C05.schedule, offsets 160347–160422) | yes / no |
| Q250 | `offering:C05` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q251 | `outcome:C05.1` | outcome for `records` | topic_mention, no level (no rubric yet), unsupported | `Financial Accounting: Preparing Financial Statements: Covers the` (C05.outcome_evidence, offsets 161689–161753) | yes / no |
| Q252 | `option:C06` | level | 2 | `, Level 2` (C06.level, offsets 153190–153199) | yes / no |
| Q253 | `option:C06` | assessment | exams taken at the college | `Online taught, only exams to be taken in the college` (C06.assessment, offsets 157004–157056) | yes / no |
| Q254 | `offering:C06` | fee_total | £1,265.00 | `Fees: £1265` (C06.fee_total, offsets 158053–158064) | yes / no |
| Q255 | `offering:C06` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q256 | `offering:C06` | intake | ["2026-02", "2026-03"] | `Start dates in February and March 2026` (C06.intakes_stated, offsets 156400–156438) | yes / no |
| Q257 | `offering:C06` | application_deadline | unknown: not stated on the page | (no span) | yes / no |
| Q258 | `offering:C06` | duration | {"years": 1} | `1 year` (C06.duration, offsets 161868–161874) | yes / no |
| Q259 | `offering:C06` | schedule | part time | `Part time` (C06.study_type, offsets 162192–162201) | yes / no |
| Q260 | `offering:C06` | wage | unknown: not stated on the page | (no span) | yes / no |
| Q261 | `offering:C06` | fee_condition | may be free depending on circumstances (ask the college) | `Please note this course may be free depending on student circumstances,` (C06.fee_condition, offsets 157936–158007) | yes / no |
| Q262 | `outcome:C06.1` | outcome for `records` | exam, no level (no rubric yet), provisional | `Principles of Bookkeeping Controls:` (C06.outcome_evidence, offsets 158371–158406) | yes / no |
| Q263 | `outcome:C06.2` | outcome for `reconciliation` | exam, no level (no rubric yet), provisional | `Introduction to Bookkeeping:` (C06.outcome_evidence.2, offsets 158194–158222) | yes / no |
| Q264 | `option:C09` | credential | AAT Level 3 Diploma in Accounting (within the apprenticeship) | `It includes the AAT Level 3 Diploma in Accounting` (C09.credential, offsets 32412–32461) | yes / no |
| Q265 | `option:C09` | standard | Assistant accountant (level 3) | `Assistant accountant (level 3)` (C09.standard, offsets 24463–24493) | yes / no |
| Q266 | `offering:C09` | fee_total | unknown: the page states no fee or cost to the apprentice (that apprentices pay no training fee is a funding rule this page does not state): unknown, never 0 | (no span) | yes / no |
| Q267 | `offering:C09` | instalment | unknown: not stated on the page | (no span) | yes / no |
| Q268 | `offering:C09` | intake | 2027-01-04 | `Monday 4 January 2027` (C09.intake, offsets 25379–25400) | yes / no |
| Q269 | `offering:C09` | application_deadline | 2026-11-30 | `Closes on Monday 30 November 2026` (C09.application_deadline, offsets 19272–19305) | yes / no |
| Q270 | `offering:C09` | duration | {"months": 18} | `1 year 6 months` (C09.duration, offsets 25761–25776) | yes / no |
| Q271 | `offering:C09` | schedule | 35 | `35 hours a week` (C09.weekly_hours, offsets 24972–24987) | yes / no |
| Q272 | `offering:C09` | wage | £14,560.00–£14,560.00 per year, advertised | `&#xA3;14,560 a year` (C09.wage, offsets 23588–23607) | yes / no |
| Q273 | `outcome:C09.1` | outcome for `reconciliation` | practice, no level (no rubric yet), provisional | `Complete bank and account reconciliations and resolve discrepancies` (C09.outcome_evidence, offsets 27115–27182) | yes / no |
| Q274 | `outcome:C09.2` | outcome for `records` | practice, no level (no rubric yet), provisional | `Maintain purchase and sales ledger records` (C09.outcome_evidence.2, offsets 27063–27105) | yes / no |

## Funding (P01, P03, P05)

| # | Record | Field | Value | Span (claim, location) | Right as the page states it? |
|---|---|---|---|---|---|
| Q275 | `funding:F01` | instrument kind, award state | fee_waiver, not_assessed | (record) | yes / no |
| Q276 | `funding:F01` | eligible_costs | course fees only | `The government will pay the course fees.` (F01.eligible_costs, offsets 5331–5371) | yes / no |
| Q277 | `funding:F01` | published_on | 2021-04-01 | `1 April 2021` (F01.published_on, offsets 44102–44114) | yes / no |
| Q278 | `funding:F01` | rules_updated_on | 2025-07-29 | `29 July 2025` (F01.rules_updated_on, offsets 44238–44250) | yes / no |
| Q279 | `funding:F01` | timing | unknown: when and to whom it is paid is not stated on the page | (no span) | yes / no |
| Q280 | `funding:F01` | repayment | unknown: not a loan | (no span) | yes / no |
| Q281 | `funding:F01` | rule_age | {"minimum_age": 19} | `aged 19 or over` (F01.rule_age, offsets 4290–4305) | yes / no |
| Q282 | `funding:F01` | rule_earnings | {"below_annual_gross": {"currency": "GBP", "minor_units": 2575000}, "or_unemployed": true} | `earn below £25,750 or are unemployed` (F01.rule_earnings, offsets 7233–7269) | yes / no |
| Q283 | `funding:F01` | rule_local_variation | in some areas the earnings limit and prior-qualification rules differ: check with the local provider | `In some areas, there may be slightly different rules about the maximum amount you can earn and the qualifications you already have.` (F01.rule_local_variation, offsets 7318–7449) | yes / no |
| Q284 | `funding:F01` | eligible_courses_level_3 | a level 3 qualification in a listed subject (including accounting and finance, digital, health and social care) | `Study for a level 3 qualification in:` (F01.eligible_courses_level_3, offsets 5564–5601) | yes / no |
| Q285 | `funding:F01` | eligible_courses_level_2 | a level 2 qualification in construction, engineering or manufacturing | `in construction, engineering or manufacturing` (F01.eligible_courses_level_2, offsets 4712–4757) | yes / no |
| Q286 | `funding:F01` | rules_version_note | earnings threshold £25,750 under the adult skills fund funding and performance management rules 2025 to 2026 | `Updated the earnings threshold from £25,000 to £25,750 to reflect the adult skills fund: funding and performance management rules 2025 to 2026.` (F01.rules_version_note, offsets 45194–45337) | yes / no |
| Q287 | `funding:F01` | eligible_subject_digital | digital | `digital` (F01.eligible_subject_digital, offsets 5918–5925) | yes / no |
| Q288 | `funding:F01` | eligible_subject_accounting | accounting and finance | `accounting and finance` (F01.eligible_subject_accounting, offsets 5651–5673) | yes / no |
| Q289 | `funding:F01` | award_status | not awarded: eligibility is checked by the provider at admission | `If you’re accepted, you will not have to pay a course fee.` (F01.award_status, offsets 8665–8723) | yes / no |
| Q290 | `funding:F01` | universal_credit_interaction | many claimants can train full-time for up to 16 weeks and keep claiming | `Many Universal Credit claimants can take full-time training for up to 16 weeks and continue to claim benefit.` (F01.universal_credit_interaction, offsets 10004–10113) | yes / no |
| Q291 | `funding:F02` | instrument kind, award state | loan, not_assessed | (record) | yes / no |
| Q292 | `funding:F02` | eligible_costs | unknown: not stated on the page | (no span) | yes / no |
| Q293 | `funding:F02` | published_on | unknown: not stated on the page | (no span) | yes / no |
| Q294 | `funding:F02` | rules_updated_on | unknown: not stated on the page | (no span) | yes / no |
| Q295 | `funding:F02` | timing | unknown: when and to whom it is paid is not stated on the page | (no span) | yes / no |
| Q296 | `funding:F02` | repayment | Advanced Learner Loans, repaid when earning over a threshold | `are available to help you cover the costs of learning, which you pay back when you’re earning over a certain amount.` (F01.alternative_if_ineligible, offsets 10504–10620) | yes / no |
| Q297 | `funding:F02` | rule_age | {"minimum_age": 19, "on": "first day of the course"} | `You must be 19 or older on the first day of your course.` (F02.rule_age, offsets 4884–4940) | yes / no |
| Q298 | `funding:F02` | rule_course_level | {"levels": [3, 4, 5, 6]} | `Level 3, 4, 5 or 6 qualification` (F02.rule_course_level, offsets 5107–5139) | yes / no |
| Q299 | `funding:F02` | rule_provider | an approved college or training provider in England | `at an approved college or training provider in England` (F02.rule_provider, offsets 5208–5262) | yes / no |
| Q300 | `funding:F02` | rule_residency | living in the UK on the first day; a UK national, Irish citizen or settled; 3 years' residence before the course (with listed exceptions) | `have been living in the UK, British overseas territories, the Channel Islands or the Isle of Man for 3 years in a row before the first day of your course` (F02.rule_residency, offsets 6573–6726) | yes / no |
| Q301 | `funding:F02` | lle_interaction | {"levels": [4, 5, 6], "courses_starting_on_or_after": "2027-01-01", "use_instead": "Lifelong Learning Entitlement funding"} | `studying a level 4, 5 or 6 qualification on a course that starts on or after 1 January 2027 - apply for student finance through your` (F02.lle_interaction, offsets 5653–5785) | yes / no |
| Q302 | `funding:F02` | htq_interaction | level 4 or 5 Higher Technical Qualifications use undergraduate funding instead | `studying a level 4 or 5 qualification with Higher Technical Qualification approval - apply for` (F02.htq_interaction, offsets 5433–5527) | yes / no |
| Q303 | `funding:F03` | instrument kind, award state | programme, not_assessed | (record) | yes / no |
| Q304 | `funding:F03` | eligible_costs | unknown: not stated on the page | (no span) | yes / no |
| Q305 | `funding:F03` | published_on | unknown: not stated on the page | (no span) | yes / no |
| Q306 | `funding:F03` | rules_updated_on | unknown: not stated on the page | (no span) | yes / no |
| Q307 | `funding:F03` | timing | unknown: when and to whom it is paid is not stated on the page | (no span) | yes / no |
| Q308 | `funding:F03` | repayment | unknown: not a loan | (no span) | yes / no |
| Q309 | `funding:F03` | rule_age | {"minimum_age": 19} | `You need to be 19 or over to do a Skills Bootcamp.` (F03.rule_age, offsets 123142–123192) | yes / no |
| Q310 | `funding:F03` | rule_course_specific | some bootcamps add entry requirements, listed in the course details | `Some courses may have additional entry requirements, such as needing you to have a certain qualification or experience.` (F03.rule_course_specific, offsets 123442–123561) | yes / no |
| Q311 | `funding:F03` | duration_limit | {"weeks_max": 16} | `Skills Bootcamps take up to 16 weeks to complete.` (F03.duration_limit, offsets 122564–122613) | yes / no |
| Q312 | `funding:F03` | outcome_offer | a guaranteed job interview with an employer after finishing | `After you’ve finished your Skills Bootcamp, you’re guaranteed a job interview with an employer.` (F03.outcome_offer, offsets 126470–126565) | yes / no |
| Q313 | `funding:F03` | cost_to_learner | unknown (null) | `course fees` (F03.cost_to_learner, offsets 127384–127395) | yes / no |
| Q314 | `funding:F03` | digital_subjects | digital, including data engineering, software development and marketing | `, including data engineering, software development and marketing` (F03.digital_subjects, offsets 121542–121606) | yes / no |
