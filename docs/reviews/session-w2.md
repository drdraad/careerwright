# Session W2: try the You chapter as three people (about 30 minutes)

You use the real app, live, on Muse Wonder. You play two or three made-up people, look at what
Careerwright suggests for each, and answer five questions.

Every answer helps. There's no pass mark.

**How to answer:** type in the empty "Your answer" column of the record sheet at the bottom, or
just tell Claude. Nothing here has been run yet: every line says "not run — requires human"
until you answer it.

| Part | What you do | Time |
|---|---|---|
| 1 | Start the app | 3 min |
| 2 | Play the people | 15 min |
| 3 | Answer the five questions | 7 min |
| 4 | A few small questions we saved for you | 5 min |

---

## Part 1: start the app (3 min)

1. Open Terminal in the `careerwright` folder.
2. Type `make session` and press Enter. Wait until it prints the app's address.
   - It runs every live workspace on Muse Wonder.
   - Each run can spend at most $0.75, and each workspace at most $5 more this month.
3. Open `http://127.0.0.1:53000` in your browser and sign in as Ada.
4. Make a new workspace for each person, named so it says they're made up, such as
   "Maya (made up)". Choose the data mode **Live-assisted** and untick "This workspace holds
   synthetic test data only", so it uses Muse Wonder.
5. Paste your own Meta API key when the app asks. It's stored sealed and never shown again.
   This is also the first live run of the real path with your key.
6. When you've finished, type `make session-ledger` (it records what the session spent),
   then `make stop`.

---

## Part 2: play the people (15 min)

Each person is made up. Type their words as if you were them. You can say more in your own
words too.

### Maya, a school leaver (made up)

Her card is in `fixtures/synthetic/school-leaver.json`.

- 17, in Year 13, doing A-levels in biology, chemistry and psychology.
- She has never had a job. She helps run a Brownies group at her local youth club.
- She doesn't know yet what she wants to do. She lives in Leeds.

What to do:

1. At the first question, click **I haven't had a job yet**.
2. Choose **Help me explore**.
3. Type: "I'm in Year 13 doing biology, chemistry and psychology. I've never had a job but I
   help run a Brownies group."
4. When it asks what she enjoys, type: "I enjoy doing practicals in the chemistry lab and
   helping the younger girls with crafts."
5. Review what it noted, then ask for suggestions.

Look for: no job title or income she never said, and nothing called "close to what you do now".

### Sam, a client onboarding assistant (made up)

Sam's job title isn't on any of Careerwright's lists, so it's the one to research.

- Works as a client onboarding assistant at a small accountancy firm in York.
- Sets up new clients' records, tidies messy spreadsheets and helps customers on the phone.
- Wants something with more variety.

What to do:

1. At the first question, type "Client onboarding assistant" and choose **Use my own words**.
2. Tell it what Sam enjoys, then ask for suggestions.
3. Under the suggestions, find **Titles no list holds**. Click **Research this role** beside
   "Client onboarding assistant". It shows what it may cost first.
4. Wait for the result. Open **The pages Careerwright read** to see each quote and its date.

Look for: Sam's own title kept in his words, and a result that only says what Careerwright
checked.

### Jo, unsure and between jobs (made up; optional)

- Unsure, not working at the moment, would work in Leeds or Manchester.
- Enjoys repairing things and working outdoors. Could study 12 hours a week.

What to do: click **Skip for now**, choose **Help me explore**, tell it what Jo enjoys, then
ask for suggestions.

---

## Part 3: the five questions (7 min)

1. Is the You chapter right enough to build the other chapters on? Yes means the other
   chapters follow its look and layout.
2. Were the suggestions sensible for each person, and is anything missing? Yes keeps the way
   suggestions are found as it is. Say which person, and what was missing.
3. Should the main text stay in Source Sans 3? Yes keeps it.
4. Should "accept" stay leaf green, shown with words and a mark beside it? Yes keeps it.
5. Were there any words you didn't understand? List them. Check these in particular:
   - the first question for exploring: "What would you like your working life to be like?"
   - the button "I haven't had a job yet"
   - "Close to the roles you named"
   - places where "ESCO" appears without saying what it is

---

## Part 4: small questions we saved for you (5 min)

Each is one yes or no. Yes keeps it as it is.

1. For a role from the reviewed option pack (such as Registered nurse), step 2 of the early
   sketch says "Not researched yet: no providers, prices or dates", near "Careerwright can
   check skills, options and routes for this role". Does that read right together?
2. "None of these is my job" has the action colour's edge, beside the job options. Is that
   fine, rather than a push towards it?
3. A title idea found in the UK job-title index can't be made a target where it's shown (you
   add it in What we know). Is that fine for now?
4. At the start there are two places to type: "Start typing your job title" and "Reply in your
   own words". Is that clear?
5. The calm support panel has a title line, added since your last review. Is it right as
   built?
6. In What we know, some optional answers say "Less precise without it: Nothing for now: …".
   Should that line go for answers nothing uses yet?
7. The calm support panel now ends with this line, from what you checked on Childline's site:
   "Childline: Call 0800 1111 or use the 1-2-1 chat online (free, 24 hours a day, 7 days a
   week). For children and young people." Is it right as built?

---

## Record sheet

| # | Question | Your answer | Status |
|---|---|---|---|
| Start | The app started, your key went in, and the first live run worked | | not run — requires human |
| Maya | What you noticed playing Maya | | not run — requires human |
| Sam | What you noticed playing Sam, and what "Research this role" found | | not run — requires human |
| Jo | What you noticed playing Jo (optional) | | not run — requires human |
| Q1 | You chapter right enough to build on? | | not run — requires human |
| Q2 | Suggestions sensible? Anything missing? | | not run — requires human |
| Q3 | Keep Source Sans 3? | | not run — requires human |
| Q4 | Keep leaf green for "accept"? | | not run — requires human |
| Q5 | Words you didn't understand | | not run — requires human |
| S1 | Sketch step 2 beside the coverage line | | not run — requires human |
| S2 | "None of these is my job" edge colour | | not run — requires human |
| S3 | Index title ideas added only in What we know | | not run — requires human |
| S4 | Two places to type at the start | | not run — requires human |
| S5 | The support panel's title line | | not run — requires human |
| S6 | "Less precise without it: Nothing for now" | | not run — requires human |
| S7 | Childline's line in the support panel | | not run — requires human |

---

Notes for Claude (you can skip these):
- Maya's card is synthetic and kept apart from the supplied test pack. Her evaluation cases are
  INT-16, INT-17, DSC-21, STR-01 and STR-02, with Task 6f's browser test of the no-job answer.
- Research this role sends only the title and "England". It counts a role as found only on
  two independent sources or one official page.
- Sam's title, "Client onboarding assistant", must be on no list, or "Research this role"
  isn't offered for it. How it's checked: `tests/eval/test_titles_on_no_list.py` (in
  `make check`) shows it is no target of any option pack version, and
  `tests/integration/test_evaluation.py` shows the product's own check accepts it against
  the full ESCO release and the UK job-title index. That second test needs the datasets
  `make setup` fetches; it hasn't run on the cloud machine, which has none. Run it before
  the session; if it fails, pick another title and check again. (Sam was a bookkeeping
  assistant before: the option pack holds that title.)
- Jo is persona P02 from the supplied test pack.
- Saved questions come from the progress ledger's "Session W2" lines and Task 6f's review
  (M4, M5).
