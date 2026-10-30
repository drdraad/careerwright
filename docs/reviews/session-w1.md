# Session W1: choose how the world looks (about 1 hour)

You try three looks for Careerwright's world in Google Chrome. Then you say which one you would
choose, or which mix, in your own words.

Everything you see is made up: a small invented list of jobs and skills. It is a throwaway
preview, not the app. Nothing you do can break anything.

**How to answer:** type in the empty right-hand column at the bottom, or just tell Claude.

| Part | What you do | Time |
|---|---|---|
| 1 | Start it | 2 min |
| 2 | Try each look | 2 min each, then play as long as you like |
| 3 | Answer six questions | 10 min |

---

## Part 1: start it (2 min)

1. Open Terminal in the `careerpathoptimizer` folder.
2. Type `make spike-world` and press Enter.
3. Google Chrome opens on a page with three looks: Growth, Horizon and Circuit.
   It opens Chrome even if you normally use Safari, because everything was checked in Chrome.
   If it doesn't open, open Google Chrome yourself and go to `http://127.0.0.1:53300`.
4. When you're done, press Ctrl-C in Terminal to stop it.

---

## Part 2: try each look (2 min each)

The three looks ask the same question and find the same thing. Only the world changes. They
all use the same lettering, so you're comparing worlds, not lettering.

- **Growth:** a living network of roots and nerves, grown from you.
- **Horizon:** a journey across a dark plain, towards lights on the horizon.
- **Circuit:** a living circuit: exact, glowing, powered by you.

In each one, do this:

1. Type a job you've done, like "chef". Watch your light answer as you type. Pick it from the list.
2. Watch for ten seconds. Don't click.
   Your light comes on, and a few seconds later something new lights up.
3. Read the card on the right. Click **Why?**
4. Point at a few of the orange lights (or press Tab to reach them).
   Each one shows the skills it shares with your job.
5. Click two skills you've used. Watch what changes.
6. Click the bright button, **Keep … in view**. Then click **Undo**.
7. Turn on **Calm mode**. It's the same world, standing still. Turn it off again.

Then play as long as you like:

- Click **Start again** and try another job: care worker, electrician, bus driver, data analyst.
- Turn on **Sound**, then start again. You'll hear a low swell when your light comes on, a rising
  chime when the new connection lights up, and a small tick when you pick a skill. Sound is off
  unless you turn it on.
- To try other lettering, open **Spike tools** (bottom right) and pick a heading typeface.
- Switch looks with the names at the top. Your answer isn't kept when you switch.

If you'd like to compare them side by side, there are pictures of each look in
`docs/reviews/session-w1/`: the question, the discovery, and the same moment standing still.

---

## Part 3: your answers (10 min)

| # | Question | Your answer |
|---|---|---|
| 1 | Which look would you choose, or which mix? Say it in your own words. | |
| 2 | In the first ten seconds of each look, what did you feel? | |
| 3 | Did anything confuse you, or seem to promise more than it should (for example, look like a job offer)? | |
| 4 | Do you want sound? There are three sounds: the swell when your light comes on, the chime when the connection lights up, and the tick when you pick a skill. (yes, no, only some of them, or later) | |
| 5 | The heading lettering: all three looks use the first one in `docs/reviews/session-w1/4-typefaces.png`. Keep it, or would you rather one of the others? | |
| 6 | Anything else you want changed before we build it for real? | |

After you choose, we build your choice into the app, starting with the first screen. You review
that at the next session.

---

<sub>What the builder checked, so you don't have to (these are not design scores; only you
score): in all three looks the words are the same with motion on and off, and stay on screen
when you turn Calm mode on and off; the preview makes no connection beyond your own computer;
and it runs smoothly on this Mac, with no dropped frames at its busiest. Details are in
`spikes/world/README.md`.</sub>
