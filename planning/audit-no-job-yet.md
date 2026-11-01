# Audit: the path for someone who has never had a job

The product owner, 1 November 2026: "I don't want to over-rely on existing skills in the
process. Many users will be final year school students who have never had a job before."

This walks the whole path as a final-year school student in England: 17 or 18, never had a
job, maybe volunteering or a weekend activity, A-levels or a BTEC in progress, unsure what
they want.

**How it was done.** Read-only. No app run, no live call, no tests run. Code, data, task
cards, the specification, the personas, the evaluation cases and the latest review captures.
Citations are to HEAD `51ca593`. Task 6d slice C is mid-flight in the main tree with
uncommitted edits (`Directions.tsx`, `vocabulary.ts` after line 340, `exploration.py`,
`slate.py`, the evaluation cases): it may move some cited lines, and it is removing the
unexpected connection as a separate object. Anything marked *derived* comes from reading code
and the pinned data, not from a run.

---

## The walk, in brief

| Step | What the student meets | Evidence |
|---|---|---|
| Start | "What do you do now, or what did you do last?" over a field labelled "Your job title", placeholder "Start typing your job title", and a quiet "Skip for now". | `vocabulary.ts:868, 872-873, 887`; capture `docs/reviews/sprint-2/screenshots/you--390x844.png` |
| Types "student" | *Derived:* "Use my own words: “student”" first, then job titles that begin with "student": ONS's "Student nurse", "Student adviser", "Student ambassador"; ESCO's "student advisor" (an educational counsellor). ONS's own entry "Student" has no code and is dropped at import. | `taxonomy.py:193-204, 207-243` (prefix match, ordering); `soc.py:114-116`; ONS index row `e1qo` "Student", SOC `}}}}` |
| Keeps "student" | Careerwright keeps it as the role, then says "…so what this work asks for isn't known yet." | `Conversation.tsx:309-323`; `vocabulary.ts:912-913` |
| Types "sixth form student" | *Derived:* no title holds every word, so the partial list asks "Careerwright couldn't match that title in ESCO. Is it one of these?" over ESCO occupations holding most of the words (school teaching titles are the likely ones). | `taxonomy.py:238-243`; `vocabulary.ts:876` |
| Skips | Nothing is saved, so the person's light stays dark. | `FirstQuestion.test.tsx:397-406`; `world/model.ts:38-42, 54` |
| How to start | "I know my direction" / "Help me explore". Neutral. | `vocabulary.ts:272-275` |
| Opening (explore) | "What would you most like to be different about your working life?" | `vocabulary.ts:287`; spec line 233 |
| Demo questions | Asked in order: what you do now (again, if skipped; example "I'm a warehouse supervisor"), cities, hours for learning, "the most you would spend on this change", then "role in mind, or explore?". Never asks what they enjoy, can do or have done. | `fixture_interviewer.py:43-58, 126-133`; `vocabulary.ts:303-317` |
| Live interview | The instructions say nothing about people without a job. The conversation's "Show me suggestions" waits until the current role has any answer. | `interview.py:444-480`; `conversation.ts:112, 134-145` |
| Suggestions | Works from what they enjoy. With no work known: heading "Directions to consider", and the note "Careerwright doesn't know your current work yet…". The emphasis row still offers "Closer to what I do". | `Directions.tsx:739-744, 774-776`; `vocabulary.ts:534-540` |
| The world | Lit after any answer. No skills "usual in your role" and no first destinations without an ESCO role. The overlooked strength is refused until a target is chosen. | `exploration.py:1677-1683`; `strengths.py:157-179, 243-250` |
| Target, sketch | Works. "Compare these requirements with what you have done" fits anyone. | `vocabulary.ts:946` |
| Options, Routes (not built) | University fees count as the student's own spending; a 3-year degree runs past the 24-month model; the apprenticeship's fee is unknown; every funding scheme in the pack needs age 19+. | Finding 2 and 6 |

---

## 1. Top findings, ranked by harm to a school student

### Finding 1. The first question has no answer for "I haven't had a job", and skipping leaves the world dark

**What they'd experience.** The first screen asks for a job title. A student who types
"student" is offered jobs that serve students (a student nurse, a student adviser). One who
types "sixth form student" is likely asked whether they are a teacher. Keeping their own words
makes "student" their role, and the next line talks about "what this work asks for". The
honest route is "Skip for now", which saves nothing: their light never comes on, so the
plan's ten-second moment fails exactly for them. In the demo, the conversation then asks
"What do you do now…?" again, with "I'm a warehouse supervisor" as the example.

**Evidence.** `vocabulary.ts:868-887` (question, "Your job title", "Start typing your job
title", "Skip for now"); `FirstQuestion.tsx:337-341`; skip saves nothing
(`FirstQuestion.test.tsx:397-406`; `Conversation.tsx:262-266`); the light needs a saved
answer (`world/model.ts:38-42, 54`); "Student" dropped from the ONS index (`soc.py:114-116`;
index row `e1qo`); the role line (`vocabulary.ts:912-913`); the repeat in the demo
(`fixture_interviewer.py:43-50, 136-146`; `vocabulary.ts:306`). Capture:
`docs/reviews/sprint-2/screenshots/you--390x844.png`. The type-ahead lists are *derived*, not
run.

**Why it matters.** It is the first ten seconds. It tells a student "this is for people with
jobs" before anything else, the opposite of "My future is larger than I realised". The plan's
own baseline to beat is "Don't even know where to start" (`development-plan.md:170`).

### Finding 2. Routes would tell a school leaver that university is out of reach, and leave an apprenticeship unresolved

**What they'd experience** (once Options and Routes are built on today's rules):
- **University.** A loan is never counted as support, so the nursing degree's £10,050 a year
  counts as the student's own spending and cash. Against any realistic student limit, the
  degree reads "not feasible in this monthly model". In England most students pay tuition
  with a loan paid straight to the university (background, not checked here).
- **Length.** The model plans at most 24 months. The degree takes 3 years. The specification
  gives such a path "an explanatory sketch and an unsupported-model state".
- **Apprenticeship.** The pack's apprenticeship has its wage (£14,560 a year, 35 hours) but
  its fee is unknown, because the page doesn't state that apprentices pay no training fee. The
  route stays unresolved unless the student types £0 as their own figure.
- **Time.** Hours and commitments are one figure for the whole plan. "At school until July,
  free from September" can't be said. Work patterns all assume a current job, and the baseline
  has no "staying in education".

**Evidence.** Loans: `planning/catalogue.py:208, 282`; spec line 586. Degree fee and length:
`england-option-pack-0.2.0.json:446, 448, 633`. Horizon: `planning/months.py:16`; spec line
71. Apprenticeship: pack lines 464, 472, 634 ("that apprentices pay no training fee is a
funding rule this page does not state"). Time: `planning/inputs.py:9-11, 75-80, 95-99`;
`planning/catalogue.py:316-320`. I did not trace the checker's verdict for these cases.

**Why it matters.** The two main school-leaver routes are a degree and an apprenticeship.
Both are in the pack, and both would come out wrong or empty. That is the opposite of "a
credible route towards something they thought was beyond them".

### Finding 3. The conversation asks about a working life and "this change", and the demo never asks what they enjoy

**What they'd experience.** The explore opening asks what they'd change about their working
life. The spending question asks about "this change". The demo asks for a job, cities, hours
and money, never what they enjoy, can do or have done. Examples are adult job lines. In a live
interview the model has no guidance for someone without a job, and the conversation's way to
suggestions waits for a current-role answer the student may never give. The sure entry asks
"at what level?".

**Evidence.** `vocabulary.ts:286-287, 204, 217, 303-317`; spec line 233 (the opening is the
specification's own words); `fixture_interviewer.py:43-61, 126-133`; `interview.py:444-480`
(no line on people without work); `conversation.ts:112, 134-145`; `Directions.tsx:742-743`
("doesn't know your current work yet"); `vocabulary.ts:528-540` ("Close to what you do now",
"Closer to what I do").

**Why it matters.** Discovery for a student rests on what they enjoy and have done (school,
volunteering, clubs, caring). The demo, where human testing starts, never collects those, so
a student's slate comes only from the opening's free answer.

### Finding 4. There's nowhere to say "I'm at school" or which qualifications they're taking

**What they'd experience.** The saved answers have a current role but no work or study
status and no qualifications. "I've never had a job" can only be stored as Skipped, Unknown, or
a fake role. The facts that decide a school leaver's entry ("BBC including specific
subjects"; "GCSE maths and English at grade 4 or above") have no home, and the planning model
records entry as yes, no or not answered, with no "results due in August".

**Evidence.** `profile/document.py:162-198` (12 fields; none for status or qualifications);
answer states `vocabulary.ts:125-129`; spec line 156 ("Collect work status, current
role/level, experience, relevant qualifications and commitments"), line 221 ("Work/study
status … credentials") and line 224 ("prerequisite education"); entry requirements in the
pack, lines 451 and 472; `planning/inputs.py:183-185`.

**Why it matters.** This is a specification gap that hurts students most. Their
qualifications in progress are their main asset and the main gate on their routes.

### Finding 5. The world's first answer and the one model-proposed revelation rest on a job or a chosen target

**What they'd experience.** The first destinations and the skills "usual in your role" come
only from the role's ESCO occupation, so the student's light comes on alone. The overlooked
strength (their own words matched to a skill, such as "I run the school coding club") looks
only at chosen targets and the role's first destinations. A student who is still exploring
is refused ("no_destinations"), even after a full slate was found from what they enjoy.

**Evidence.** `exploration.py:1677-1683` (the first slate is the role's join alone);
`capability/strengths.py:157-179` (destinations), `:243-250` (refusal); plan
`development-plan.md:180, 201`; Task M card `l0-sprint-tasks.md:1776, 1781-1785`. The
unexpected connection also needs an ESCO role, but the product owner's "always a plain line"
and slice C make that moot.

**Why it matters.** Of the plan's three revelations, the overlooked strength is the one a
student can earn without a job. Today it is blocked while they explore.

### Finding 6. Options and Roles hold no school-leaver funding or sources

**What they'd experience.** All three funding schemes in the pack need the person to be 19 or
over (Free Courses for Jobs, Advanced Learner Loan, Skills Bootcamps), and the profile has no
age. So a 17-year-old meets three schemes they can't use and none of theirs: student finance,
the 16 to 19 Bursary Fund, free full-time education to 19, the apprenticeship no-fee rule.
The degree has no UCAS deadline ("not on this page"). Option research sends only a target
title and a city. Apprenticeship adverts are an M1 source; in L0, Roles reads Adzuna.

**Evidence.** Pack lines 500, 510, 521 (`rule_age`, minimum 19); 633 (UCAS deadline
unknown); spec lines 45, 416 (apprenticeship adverts in M1) and 592; Task 7e
`l0-sprint-tasks.md:1097`; Task 8 `:1293`; `evidence/sources.json` (no apprenticeship or UCAS
host; the default class permits a pasted page).

**Why it matters.** The planning model can only be as good as the options and funding it
holds. For school leavers it holds the wrong funding and too few routes.

### Finding 7. No school leaver in the test people, the checks or the next session

**What they'd experience.** Nothing protects their path from regressions. P01 to P05 are
adults with work history; P02, the closest, is "unsure, unemployed". None of the 55
evaluation cases speaks as a school student. Interview cases are adult job lines ("At my last
job", "payroll for ten years", "warehouse supervisor"). Session W2's package plans "two or
three named personas (one whose role is on no list)".

**Evidence.** `fixtures/m0/personas/P01.json:10` … `P05.json:10`;
`backend/tools/evaluation_cases.json` (INT-01 line 7, INT-04 line 55, INT-11 line 149);
`l0-sprint-tasks.md:913`. On the good side, 12 of the 20 discovery cases have no role (for
example DSC-04 line 442, DSC-20 line 660), so slate retrieval without a role is checked.

**Why it matters.** The live prompts have never seen a student's words, and session W2 will
judge the start without one.

### Finding 8. The specification says Careerwright is for adults

**What they'd experience.** Nothing yet, but it decides what is allowed. The specification's
primary customer is "an adult making a career choice", the private beta is for "adult
testers", and the press release says "designed for adults". Live mode needs the person's own
Meta API key. The calm support panel lists adult services only (999, NHS 111, Samaritans,
Shout), with no young people's service.

**Evidence.** Spec lines 24, 36, 111 and 27; `docs/adr/0001-l0-scope.md:60-62` (real people's
data needs the privacy assessment); `profile/safety.py:361-389`.

**Why it matters.** Many Year 13 students are 17. Young people's data, consent and support
need a decision before a real student uses the app. I did not check the legal rules or
Meta's age terms.

---

## 2. Smallest coherent change, and who owns it

Each change makes the existing path work without a job. None adds a separate student mode:
the same answers help career returners, carers and anyone between jobs.

| # | Smallest coherent change | Owner | Rough size |
|---|---|---|---|
| 1 | Beside "Skip for now", one answer: "I haven't had a job yet" (wording is the product owner's). It saves an answer, so the light comes on, and the start goes to how to start. The conversation never asks the job question again, and the next question is about what they enjoy. With Finding 4's field it saves that status. Without it, the interim is that "Skip for now" saves the role as Skipped (an answer) so the light comes on and the question isn't repeated. Add a browser test: the no-job answer lights the world within ten seconds. | New work before session W2: a short Task 6d follow-up after slice C, or a line on Task 6e's card | 3-4 h (interim); about 2 h more with Finding 4 |
| 2 | (a) Task 12b's checkpoint words work for someone not working: the baseline "staying in education", and "not working: 0 hours, £0" said plainly. (b) Task 14 says a route longer than the model in plain words, as the specification asks ("longer than Careerwright can plan yet"). (c) The apprenticeship fee comes from the new pack version (Finding 6), or the student states £0 as their own figure at the checkpoint (already in Task 12b's card). (d) With the product owner's yes: a tuition fee loan paid to the university is no cash out of the student's pocket and is shown as a loan to repay (checker and Task 13a's separate oracle both change). (e) With a yes: hours that change on a date ("free from September"). | 12b and 14 for (a) to (c); new work for (d) and (e), between 12b and 14 | (a)-(c) 2-4 h inside the cards; (d) 8-12 h; (e) 6-10 h |
| 3 | A word pass: the explore opening (a decision, because the specification sets it); "this change" becomes "your next step"; one non-job example reply ("I help run a youth football team"); the demo asks unsure people "What do you enjoy doing, at school, at work or in your own time?"; one line in the live instructions ("Someone may not have had a job yet: ask about school or college, volunteering, caring, clubs and hobbies; never treat no job as a gap"); the conversation's way to suggestions no longer waits for a current role; "Closer to what I do" hidden when no work is known; drop "yet" from "doesn't know your current work yet". Bump the interview prompt version and run the new evaluation cases once, capped. | New work before session W2 (with Finding 1) | 3-5 h and one capped live run |
| 4 | Two optional answers: "What you're doing now" (working, in education or training, looking for work, caring, other: the specification's work status) and "Qualifications, including ones you're taking" (each achieved or expected). Saved-answers schema version 4, a migration, the interview contract, demo patterns, What we know, the client. Then Task 10 reads them as entry facts (expected is unresolved, never met) and Task 12b's entry confirmation reads them ("if you get your grades"). | New work (needs the product owner's yes), then a line each on Tasks 10 and 12b | 8-12 h, then 2-3 h each |
| 5 | Task M: when the role names no ESCO occupation, the strength's horizon is the latest slate's suggestions, not only the role's first destinations; the first answer's ignition also answers a first saved "what you enjoy" (its first destinations from the skill search), so the world responds without a job. Task 10: no empty "usual in your role" panel without a role. | Task M; one line on Task 10 | 3-5 h inside M; under 1 h in 10 |
| 6 | A new reviewed option-pack version with school-leaver sources: the official page saying apprentices don't pay for training; Student Finance England's tuition fee and maintenance loan pages; the 16 to 19 Bursary Fund; a T Level or Level 3 course; the UCAS deadline. Task 12b shows each scheme's age rule beside it (the pack already holds it). Task 7e's research purpose names apprenticeships, degrees and their funding. Task 8 marks apprenticeship listings as such and takes a pasted apprenticeship advert. | New work like Tasks 7b and 7c (with a short review session); a line each on 7e, 8 and 12b | 6-10 h and a review session; 1-2 h on the cards |
| 7 | A synthetic school leaver, labelled synthetic and kept apart from the supplied pack (which stays untouched): 17, Year 13, A-levels in progress, no job, helps at a youth club, unsure, Leeds. 4 to 6 evaluation cases: an interview ("I'm in Year 13 doing biology, chemistry and psychology. I've never had a job but I help run a Brownies group": enjoyed and done tasks, no job title invented, no income invented); a discovery from school subjects and volunteering (grounded, nothing marked "close to what you do now"); a strength proposal from those words once a slate exists; the no-job first answer in the browser. Make her one of session W2's personas. | Task 6e (session W2's package), plus new evaluation cases | 2-3 h and one capped live run |
| 8 | Decisions first (section 4). Then: the specification's "who it's for" line (the controller's), Childline in the support panel (checked on its own site; support policy version and review), and the release report's privacy note. | Controller; a small support-policy change; Task 16 | 1-2 h, plus the privacy check |

New work in total, if every decision is yes: about 35 to 55 agent hours, and one short review
session for the pack.

---

## 3. What already works for them

- **Skip and own words.** "Skip for now" is always there. "Use my own words" is always first
  and kept. Nothing typed is refused. `FirstQuestion.tsx:5-13, 337-341`.
- **Discovery doesn't need a role.** It searches from what they enjoy, believe they can do and
  have done, through ESCO's essential skills (`discovery.py:47-54`; `exploration.py` module
  note). 12 of the 20 discovery cases have no role.
- **No false "different".** With no work known, no suggestion is called "a different kind of
  work", and the group is headed "Directions to consider" (`exploration.py:712, 943`;
  `Directions.tsx:774-776`).
- **"Try it before committing"** in every suggestion: talk to someone who does the work, try
  one of its tasks (`vocabulary.ts:782-785`). Ideal for someone who has never worked.
- **Skills judge what you can show, not job time.** The answers are context-free (done
  independently, done with help, understand but not tried, not learned, unsure:
  `capability/evidence.py:56-68`). "Time in a job adds nothing by itself"
  (`docs/adr/0012-capability-model.md:128`). Anchors read "No evidence yet of…", and a short
  work sample counts as proof (`capability-reference-0.2.0.json:56, 75`). A school project
  counts as much as a job.
- **Money and unknowns are honest.** £0 is allowed, unknown is never zero, and an unconfirmed
  baseline blocks an economic comparison instead of inventing one (`planning/inputs.py:367-395`;
  P02's expectations).
- **The pack holds two school-leaver routes with their entry rules:** the nursing degree (BBC
  at A-level; at least £5,000 a year that is not paid back) and an accounting apprenticeship
  (GCSE maths and English at grade 4; £14,560 a year; 35 hours). Pack lines 446-472.
- **No search by age.** Discovery may never search by age (`discovery.py:266-267`), with
  counterfactual cases INT-04 and INT-05.
- **Neutral start.** The purpose line and "Help me explore" fit anyone
  (`vocabulary.ts:272-275, 331-332`). The specification's FAQ already says to start from
  activities you enjoy (spec line 117).

---

## 4. Decisions for the product owner

1. **Who it's for.** The specification says Careerwright is for adults: should school
   students aged 17 and 18 be in scope? Yes means we change that line and check the rules for
   young people's data before any real student uses it.
2. **A first answer without a job.** Add "I haven't had a job yet" beside "Skip for now" at
   the first question? Yes means the answer is saved, the person's light comes on, and the
   conversation asks what they enjoy instead of their job.
3. **What you're doing now, and your qualifications.** Add two optional answers: what you're
   doing now (working, studying, looking, caring) and qualifications you have or are taking?
   Yes means Skills and Options can later check entry requirements like "BBC at A-level",
   never counting expected grades as met.
4. **The opening question.** Replace "What would you most like to be different about your
   working life?" with one that works without a job, such as "What would you like your working
   life to be like?" Yes means the specification's opening changes and the interviewer
   follows.
5. **A school-leaver test person.** Add a made-up school leaver (17, Year 13, no job, unsure)
   and 4 to 6 checks? Yes means she is used at session W2 and in every check run; the
   supplied five stay untouched.
6. **University fees paid by a student loan.** Should a tuition fee loan paid straight to the
   university count as a loan to repay later, not money from the student's own pocket? Yes
   means degree routes stop looking unaffordable to every school leaver; it changes the
   rule that loans are information only, about 8 to 12 hours of work.
7. **Degrees longer than two years.** Careerwright plans 24 months ahead and a degree takes
   three years: is it enough in this version to say plainly that the route is longer than
   Careerwright can plan yet? Yes means no planning change, only plain words in Routes.
8. **School-leaver options and funding.** Add a new reviewed version of the option list with
   apprenticeship, student finance, 16 to 19 bursary, T Level and UCAS deadline pages? Yes
   means a short review session like the last one, and apprenticeships and degrees can be
   checked properly.
9. **Childline.** Add Childline (for anyone under 19) to the calm support panel? Yes means one
   more service, checked on its own website and reviewed with the support policy.
10. **"Free from September".** Let a person say their free hours change on a date? Yes means
    about 6 to 10 hours of planning work; no means it is recorded as a known limit.

---

## 5. What I could not check

- **Anything live:** how the live interviewer and discovery handle a student's words; whether
  the live model records "never had a job" as Unknown, Skipped, a role, or nothing (which
  decides whether "Show me suggestions" ever appears in the conversation).
- **The type-ahead's actual lists** for "student", "sixth form student" and "Year 13": derived
  from `taxonomy.py`, the ONS index and ESCO's labels, not run.
- **The checker's verdicts** for a 3-year degree, the apprenticeship with £0 supplied, or a
  student with £0 cash: not traced.
- **The world** after a skipped start: no capture shows it, and its timing is unmeasured.
- **Background facts**, from general knowledge and not checked against sources here (no web
  access): tuition fee loans are paid to the university; apprentices don't pay for training;
  full-time education is free to 19; Childline serves under-19s; the UK's rules for
  children's data (the ICO's Children's code); Meta's age and billing terms for an API key.
- **Task 6d slice C** is mid-flight: it may move some cited lines, and it is removing the
  unexpected connection as a separate object.
- **Human judgements** (requires human): whether the words feel right to a 17-year-old, and
  whether the world feels like it answers them.
