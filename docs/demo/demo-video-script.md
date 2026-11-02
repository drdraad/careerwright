# Careerwright: demo video script

About 3 minutes. One happy path, told through Maya: 17, in Year 13, never had a job, unsure
what she wants. Maya is made up, so the video labels her that way.

The thread running through it: **Meta's Muse models do the listening, the searching and the
reading. Careerwright's own code checks every word and does every sum. You make every choice.**

---

## 0. Opening animation (0:00–0:10)

No voiceover. A low, warm synth pad that swells, then one soft chime on the title.

| Time | Picture | Sound |
|---|---|---|
| 0:00 | Black. A few faint stars drift. | Room tone, a breath of pad. |
| 0:02 | A single white point of light appears low in the centre: the person. It pulses once, like a heartbeat. | A low pulse. |
| 0:04 | Warm orange lights fade in along a distant horizon, one at a time. Some are filled discs, some are rings. | The pad rises. |
| 0:06 | A sea-glass trail grows from the white light towards one orange light, branching like a root or a circuit. Small gates (diamonds) sit on the trail. | A shimmer as the trail moves. |
| 0:08 | The camera pulls back. The trails settle into the title poster. | The chime. |
| 0:09 | **Title poster:** "Careerwright" in Source Sans 3, white on the deep night background. Below it, smaller: "Your future is larger than you think. Start moving towards it." | Pad holds, then fades under the voice. |

Palette, from the design tokens: night background; the person's light in white; destinations in
orange `#FF9433`; the chosen path in sea-glass `#45F7D4`. Keep it organic and slow, never
flashy. Make a still version for reduced motion: the poster fades in on its own.

---

## 1. The problem (0:10–0:25)

**On screen:** the title poster dissolves to Maya's desk: a laptop, A-level notes, a Brownies
rota on the wall.

**Voiceover:**
> Most careers sites start with a form: "What's your current job?"
> But Maya is 17. She's never had one.
> So what does she type?

---

## 2. Starting without a job (0:25–0:45)

**On screen:** the app opens on the You chapter. The world is dark except for a dim point of
light. The first question: "Do you have a role in mind, or would you like to explore?" Beside
"Skip for now" sits **"I haven't had a job yet"**. Maya clicks it.

Her light ignites, and the first trails reach out.

**Voiceover:**
> Careerwright starts with her, not her CV.
> One click, and the world answers.

**Caption:** "Maya is made up. Every screen is the real app."

---

## 3. A conversation, powered by Meta's Muse (0:45–1:15)

**On screen:** Maya chooses "Help me explore". The question appears: "What would you like your
working life to be like?" She types:

> "I'm in Year 13 doing biology, chemistry and psychology. I've never had a job but I help run
> a Brownies group."

A reply arrives. Beside it, a review card lists what Careerwright picked up: what she's doing
now (in education), her A-levels **marked "expected"**, and what she enjoys. Each item has a
Confirm button in leaf green. She confirms them.

**Voiceover:**
> Behind the conversation is Muse, Meta's model. It's good at listening, so Maya can talk the
> way she would to a person.
> But Muse doesn't get to decide anything. It only proposes.
> Maya confirms each fact herself, and her A-levels stay "expected" until she has her grades.

**Caption, small:** "Conversation by Meta's Muse Wonder. Every fact confirmed by you."

---

## 4. Suggestions she can trust (1:15–1:45)

**On screen:** the Suggestions view. A short list of roles, each shown as a ring on the
horizon. She opens one. Under "Why this could suit you", a sentence quotes her own words:
"I help run a Brownies group". A small note says the quotation was checked against what she
said.

She clicks **"Make this a target"**. The ring fills into a warm disc, and a trail grows towards
it.

**Voiceover:**
> Muse reads Maya's answers and suggests where they could lead.
> But the shortlist itself is built by Careerwright's own code, from official job lists.
> And when Muse explains a suggestion, every quote is checked word for word against what Maya
> actually said.
> No invented praise. No made-up facts.

---

## 5. A job that isn't on any list (1:45–2:05)

**On screen:** Maya types a job title she heard about that isn't on the official lists. Under
"Titles no list holds", she clicks **"Research this role"**. A note says the search sends only
the title and "England", and nothing about her. Pages come back, each shown with its website
and date.

**Voiceover:**
> Real jobs don't always fit the official lists.
> So Muse searches the web, sending only the job title.
> Careerwright then reads the pages and checks the exact title appears on two independent
> sites before calling it found.
> If it can't check, it says so. It never pretends.

> *Film note: this needs a live workspace with a Meta key. If the role isn't found on two
> sites, keep that take: "Not yet found in independent sources" is the honest answer, and it
> makes the point.*

---

## 6. Skills, options and money (2:05–2:35)

> *Film note: these screens are being built now and follow session W2. Film this part once
> they're ready. Every figure on screen must come from the app, not the script.*

**On screen, three quick cuts:**
1. **Skills:** what her target role asks for, what she can already show, and an entry
   requirement that reads "if you get your grades".
2. **Options:** a degree with its fee shown as a **loan paid straight to the university, repaid
   later**, not money from her pocket. Beside it, an apprenticeship and a T Level. A missing
   fact is named plainly, with a box for her to fill it in.
3. **Routes:** a chart of time against cost. She picks one route, and a monthly money table
   opens beneath it.

**Voiceover:**
> Here's the part no model touches.
> Readiness, money and routes are worked out by Careerwright's own code, month by month,
> against Maya's own limits.
> A tuition fee loan shows as a loan to repay, not her money. A missing fact is named, never
> guessed.

---

## 7. The close (2:35–2:55)

**On screen:** back to the world. Maya's light, her chosen destination glowing ahead, a
sea-glass trail between them with its first gate lit. The camera pulls back slowly. The
poster from the opening returns.

**Voiceover:**
> Meta's Muse to listen and search.
> Careerwright to check every word and every pound.
> Maya to decide.
> Her future's larger than she thought. And she's started moving towards it.

**End card:** "Careerwright" and the line "Your future is larger than you think. Start moving
towards it."

---

## Production notes

- **Where Meta's models are used, so the claims stay true:**
  - **Muse Wonder** runs the live conversation in this demo, started with `make session`.
  - **Muse Spark** is the app's everyday model: it suggests searches and title ideas, writes
    "Why this could suit you" from checked quotes, searches the web for role research, and
    quotes values from pages.
  - Code decides everything that matters: readiness, money, routes and rankings. Say "Meta's
    Muse", never "AI decides".
- **Two ways to film, and which scenes each covers:**
  - **Demo workspace (offline, no key, free):** covers scenes 2 to 4. Its conversation uses a
    pre-written fixture interviewer, so it doesn't show Muse. Use it for rehearsal, or caption
    it "demo mode".
  - **Live workspace (`make session` with your Meta key, capped at $5):** covers scenes 3 to 5
    with Muse for real.
- **Not built yet:** the screens for scene 6 (Skills, Options, Routes). Film them after they
  land.
- **Honesty, on screen and in the edit:**
  - Label Maya "made up".
  - Nothing may imply a job offer.
  - No numbers in the voiceover that the app doesn't show.
  - Keep "not yet found" and "unknown" results if they happen; they're part of the pitch.
- **Look and sound:** Source Sans 3 for every caption; use the app's colours only; calm, warm
  music; a friendly, unhurried voice with a UK accent; captions on throughout.
