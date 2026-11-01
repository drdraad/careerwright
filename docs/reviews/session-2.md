# Session 2: your review (about 2½ hours)

You look at what the app made and say whether it is right. Nothing here is answered yet: only
you can answer. Stop whenever you like; anything you skip stays "unreviewed", and nothing
breaks.

**How to answer:** type in the empty right-hand column of each table, or tell Claude the
number and your answer (for example "Q12 yes", "D5 no: count it as level 2").

| Part | What you do | Time |
|---|---|---|
| 1 | Read one route screen and explain it in your own words | 30 min |
| 2 | Score how the first screens look, on desktop and phone | 25 min |
| 3 | Check facts taken from real course and job pages (Q1–Q219) | 55 min |
| 4 | Check what the money checker concluded for P01 (T1–T36) | 10 min |
| 5 | Check the skill levels and rubrics (R1–R58) | 20 min |
| 6 | Say yes or no to 15 rules (D3–D17) | 10 min |

---

## Part 1: explain a route screen (30 min)

Everything on this screen is invented for a test. The screen is being tested, not you.

1. Open `docs/design/screenshots/route-comparison--default--1440x900.png`.
2. Look for 5 minutes. Don't read anything else first.
3. Answer the 3 questions below about **route B**, in your own words.
4. Only then open the answer key at the bottom of this file and mark each answer.

| # | Question | Your answer | Right, partly or wrong? |
|---|---|---|---|
| 1 | What would route B cost you, and what is that cost made of? | | |
| 2 | What does "conditional readiness" mean here? | | |
| 3 | What is uncertain in what you see? | | |
| 4 | Did anything mislead you in a way that could make someone act against their own interest? What? | | |

---

## Part 2: score the first screens (25 min)

Open the screenshots in `docs/reviews/sprint-2/screenshots/`. Each comes in a desktop
version (`1440x900`) and a phone version (`390x844`).

1. **Start screen** (`you--1440x900.png`, `you--390x844.png`): look for 10 seconds. What is the
   page for, and what would you do first?
2. **Suggestions** (`you--slate--1440x900.png`, `you--slate--390x844.png`): pick one
   suggestion. Can you tell why it was suggested?
3. **Choosing:** how would you make that suggestion your target? Could you find the button?

| # | Question | Your answer |
|---|---|---|
| 1 | What the start page is for, and your first step | |
| 2 | Why that suggestion was made | |
| 3 | Found how to choose it? Where was it hidden, if anywhere? | |

**Scores:** 1 = bad, 5 = great. For anything below 4, write what is wrong.

| | Desktop | Phone | What is wrong |
|---|---|---|---|
| Clear what matters most | | | |
| Text easy to read | | | |
| Spacing feels right | | | |
| Looks like one product | | | |
| Clear about what is uncertain | | | |
| Works well at this size | | | |
| Easy to keep going from step to step | | | |

**Quick checks** (yes or no). The app at `http://127.0.0.1:53000` shows the ones the
screenshots can't.

| # | Check | Look at | Yes / no |
|---|---|---|---|
| C1 | The start screen makes sense | `you--1440x900.png` | |
| C2 | A failed reply is clear, and you can try again | `you--reply-failed--*` | |
| C3 | Suggested changes to your profile are easy to accept or undo | `you--reply-to-review--*`, or the app | |
| C4 | The suggestions list is easy to scan | `you--slate--*` | |
| C5 | The support panel is calm and helpful | `you--support-note--*` | |
| C6 | Asking before using your own API key is clear | `you--key-consent--*` | |
| C7 | Everything works on the phone | the `390x844` screenshots | |

---

## Part 3: check facts from real pages (55 min)

Open `docs/reviews/session-2-option-pack-questions.md`. Each question shows a fact beside the
exact words it came from. Answer **yes** if the words say that, **no** if not.

- First Q1–Q67 (P01's courses and jobs, about 17 min).
- Then Q68–Q219 (other people's courses and the funding pages, about 38 min).
- Q220–Q344 are optional. Skip them if you're tired: a later task can take them.

---

## Part 4: check the money checker's result for P01 (10 min)

Open `docs/reviews/session-2-checker-questions.md` (T1–T36). It shows what the checker read
about P01, what it read from each course page, and what it concluded. Answer yes or no to each.

The checker said that no course works for P01 yet. C04 costs £2,995, which is above P01's
£1,500 limit. The other options are missing dates, costs or timetables.

---

## Part 5: check the skill levels (20 min)

Open `docs/reviews/session-2-capability-questions.md` (R1–R58). These are an agent's proposals:
the skills each job needs, how each skill is graded, and what level each course would give
you. Answer yes or no to each. Only your yeses are published.

---

## Part 6: yes or no to 15 rules (10 min)

**Yes** keeps the rule. **No** means change it: say what you'd do instead. (D1 and D2 are
already answered: yes.)

| # | Rule | Yes / no |
|---|---|---|
| D3 | A job requirement counts as "must have" or "nice to have" as the job ads say. If ads disagree, it counts as must-have until you decide. Requirements that appear only in the ESCO database, and in no ad, don't count yet. | |
| D4 | A legal requirement, such as nursing registration, is met only when you say you have it **and** you've checked it with the official body. The app can't check registers itself. | |
| D5 | "I did it with help" counts as level 1 (beginner) at most. | |
| D6 | If a real assessment puts you lower than you rated yourself, the app uses the assessment's level and flags the difference. | |
| D7 | A skill level counts only if it comes from an assessment, or from you with an example and when you last did it. A level with no example counts for nothing. | |
| D8 | A test result counts once you confirm the result and who assessed you. This version has no outside reviewer. | |
| D9 | Having the right to work, on its own, never makes you "ready" for a job. At least one skill or licence must also be checked. | |
| D10 | The app asks about must-haves first, then disputed requirements, then nice-to-haves. It starts with 12 questions and stops once 80% of the must-haves are answered. | |
| D11 | The app finds a target job's course data by the same job title, or by the one official occupation that fits. If two fit, it doesn't guess. | |
| D12 | A course fee with no payment date is treated as due in the first month. Extras, such as a £13.99 certificate, are treated the same way. | |
| D13 | A course start given only as a month ("September") is treated as the 1st of that month. | |
| D14 | If you set a monthly shortfall limit, it counts course payments, minus grants received, plus any pay you lose by studying. | |
| D15 | Payments on debts you already have count towards your monthly spending limit. So if they alone are above the limit, every route fails. (No = leave existing debts out of the limit.) | |
| D16 | Becoming ready in exactly the last month of the planning window counts as within it. | |
| D17 | In the "delay" test, every funding award and job offer arrives a set number of months later. If a fee waiver arrives late, you pay the fees due before it. Course dates don't move. | |

---

## When you're done

Tell Claude "session 2 done", and which parts you finished.

---

## Answer key for Part 1 (read only after answering)

1. **Cost:** £600, paid as £150 a month for 4 months, with no pay lost. The lowest your cash
   gets is £4,850, still above the £500 safety cushion.
2. **Conditional readiness:** you're ready to apply for jobs **only if** you pass the course's
   assessed report. It is not a job, and not a guarantee.
3. **Uncertain:** whether you pass the assessment, the provider and start date (still to
   check), the payment dates, and that every figure is invented for the test.
4. **Dangerous misreadings to look for:**
   - reading the cost as cash in hand;
   - reading "ready" as a job offer;
   - missing that a payment limit or the cash cushion could fail;
   - taking invented figures as real.

---

<small>For the record: Part 1 is gate H-13, Part 2 is H-01 for Sprint 2, Parts 3–5 are H-07
(with TEST1-14 in Part 4), and Part 6 holds the provisional R6 decisions from ADRs 0011–0013.
Every part is "not run - requires human" until you answer it. ADR 0011's decisions 10 and 12
are not here: decision 10 was replaced by ADR 0012's rubrics, and decision 12 belongs to the
rights review before any push.</small>
