# ADR 0014: The living world, Careerwright's experience direction

- Status: **Accepted 2026-10-30; amended 2026-10-31.** Proposed on 2026-10-30, and accepted
  the same day, when the product owner approved plan v1.4 ("commit"). Session W1
  (2026-10-30, `docs/reviews/session-w1-answers.md`) made the spike's choices, recorded in
  decisions 2, 6 and 8 by Task W2. The amendment of 2026-10-31 (the last section) follows the
  product owner's approval of the audit: it keeps decisions 1–8 and changes decision 9.
- Date: 2026-10-30
- Supersedes, for L0: the "calm observatory" art direction (spec section 14), the visual scope
  and renderer limits of plan v1.3 (sections 1, 4 and 5) and the visual direction in
  `docs/design/README.md`.
- Requirements: VIS-1, VIS-2; spec sections 3, 7, 13, 14 and 15; ADR 0005 (the web app),
  ADR 0007 (the slate, explanations and the support panel)

## Context

At review session 2 the product owner scored the first screens 2, 4, 4, 3, 3, 4 and 2 out of
5 ("Feels incoherent", "Don't even know where to start") and could not follow the route
wording ("Sounds like psychobabble"). On 2026-10-30 they set a new direction. In their words,
the interface should be "revolutionary, not the current bland corporate borefest"; it should
"verge on computer game rather than typical tool, conveying a sense of travelling through a
brave new world, and progression towards your destiny", "feel organic and cybernetic",
"thrum with power and possibility" and "leave users astonished and breathless and excite them
with revealed insight". They added: "After the original brief I gave, I would fire whoever
put this prototype in front of me, but I guess my ambition got lost in the planning
process." Their reference image is "Careerwright's luminous path forward".

## Decisions

1. **The experience contract is plan section 4 (v1.4).** Careerwright is one persistent world
   in which the six chapters are places, not pages. Three rules govern the interaction model:
   progress visibly transforms the world, evidence unlocks understanding, and decisions show
   their consequences before they are confirmed. It overrides the specification's art
   direction for L0; the specification's domain rules are unchanged.
2. **Two rendering layers.** A WebGL2 world layer (atmosphere, glow, particles, depth, travel)
   sits behind an exact DOM and SVG layer (everything a person reads or operates, with D3 for
   layout). The canvas holds nothing unique. This lifts, for this one layer, plan v1.3's "no
   other renderer" and the specification's "No alternative GPU renderer is selected". Sprint
   W's spike chooses the library against section 4's frame budgets; it is pinned at least 14
   days old and recorded in `docs/dependencies.md` and here.
   **Chosen: three.js 0.186.1** (MIT, published 2026-09-24), the spike's recommendation, not
   contested at session W1. The spike drew the same workload with three.js, PixiJS 8.22.0 and
   OGL 1.0.11 at the same frame cost (the shaders do the work); three.js runs raw GLSL 3
   shaders as written (`RawShaderMaterial`), has a real camera for travel, is by far the most
   used and steadily maintained, and needs no `unsafe-eval` under the app's content security
   policy (PixiJS did). The app draws one canvas (`apps/web/src/lib/world/gl.ts`); its types
   are `@types/three` 0.186.0 (dev only).
   **Direction: Horizon, made livelier** (the product owner's choice at session W1): Horizon's
   calm, lined-up layout, with animation as alive as Growth and Circuit and quiet solid trails
   in place of the dashed ones. "Not known yet" is a solid slate trail, never dashed.
3. **Revelations come from deterministic sources** (the slate, readiness and gaps, the route
   checker, reviewed options) and from verified spans. The one exception, by the product
   owner's answer of 2026-10-30, is an overlooked strength: the model may propose one as a
   quotation of the person's own words against an essential skill of one of their
   destinations; code verifies the span and the skill, and the person confirms it before it
   shows. It is a new bounded run kind (ADR 0006), live only, within the person's spend
   limit; the demo shows a scripted, labelled example. The model never decides a revelation,
   and a kind of revelation with no such source is not shown.
   **In the app (Task W2 slice W2B):** the run kind `strength_proposal`
   (`careerwright.capability.strength`, prompt `overlooked-strength-1`; one `RunTask` composed
   in `worker.py`, run by the one model-run workflow as its own run, so the DBOS step
   sequence and `careerwright-l0-1` are unchanged). The person's client asks for it
   (`POST .../interview/turns/{id}/strength`, expected profile version and Idempotency-Key)
   once a turn's decision saved something they enjoy, can do or have done: at most one per
   turn, never on a turn the support screen answered (refused before any run, nothing
   stored), only while those answers are current, with the person's key and within their
   spend limit (the activity checks again). The model reads only the answers that turn's
   decision added (fix round 1: never every answer, so a strength declined on one turn is
   not offered again from the same words on a later one, and nothing about the decline is
   stored; a turn that added none it could quote is refused `no_quotable_answer`; never a
   title, a name, a place or money) and each destination's essential skills (ESCO), and
   returns at
   most one destination, skill and quotation, and no prose; finding none is an answer. Its
   destinations are the person's targets that name one ESCO occupation and the first
   slate's (ADR 0007 decision 14), each with the essential skills not yet claimed. Code
   checks the destination, that the skill is listed as essential to it, and the quotation as
   a span of an answer (ADR 0007 decision 12's verifier); one repair, then
   `invalid_model_output`. Confirmed (`POST .../strength/decision`, the capability version,
   Idempotency-Key), it is recorded as the person's own claim (ADR 0012's `used` answer, no
   level, the quotation as its example): self-reported, never evidence, so it counts for
   nothing towards readiness. Declined, nothing about the skill is recorded. A demo
   workspace uses `careerwright-fixture-strength-1`, a script (fix round 1): a fixed table
   of the demo journey's known answers, each with the ESCO skill it shows
   (`SCRIPTED_STRENGTHS`: "reconciling accounting entries", accounting entries; "fixing
   bikes", perform repairs on bicycles; "finding inconsistencies", perform data cleansing;
   "working outdoors", work in outdoor conditions), proposed only when a destination lists
   that skill as essential, quoted whole, through the same check, labelled "Demo example
   (synthetic)"; anything else finds none. No word is matched.
   Every rule above is provisional (R6) until the product owner confirms it at session W2.
4. **The world never shows more than the evidence.** Everything that varies has a computed
   meaning; position is layout only; unknown is shadow, never zero; a condition is a gate in
   plain words; nothing implies a job offer. Skills a role usually needs show as "usual in
   your role, not confirmed yet", for display only: wherever something is computed they stay
   unresolved (ADR 0012). Distress stills the world and shows the calm support panel.
5. **Colour has one meaning each.** Orange is destinations only; the sea-glass teal is
   selection, the chosen path and the primary action only; blue and violet are atmosphere,
   graded the same along every trail. Industry moves from colour to glyph and label,
   replacing spec VIS-1's industry colours.
   **Decisions on a proposed change (Task W2, the You chapter):** session 2's C3 asked for
   accept and undo as "colour coded buttons", and no meaning hue was free for either, so two
   tokens join: leaf green (`--decision-accept`, `#A6E25A`) accepts a change or confirms a
   limit, on a faint leaf tint once chosen (`--surface-decision-chosen`; at first it filled
   solid, a second bright fill beside the one primary, so the W2C review changed it);
   orchid (`--decision-undo`, `#FFAAFF`) undoes the last save. Each
   follows its words and glyph, means nothing else, and is never the primary action; CIE76 ΔE
   from every other hue is at least 56 (leaf) and 44 (orchid, nearest the journey's violet),
   measured by `docs/design/tools/contrast.mjs`. Provisional (R6), for session W2.
6. **Type.** A bold geometric sans display face and a readable sans body face, licensed and
   self-hosted; Newsreader retires. The spike chooses the faces.
   **Chosen: Outfit** for display (the product owner at session W1: "Keep Outfit"), the OFL
   variable font from `google/fonts`, pinned and unmodified (`docs/design/fonts/README.md`).
   **Body: Source Sans 3, provisional, to confirm with the product owner at session W2**
   (R6). This decision delegated the faces to the spike, and the spike set its words in
   Atkinson Hyperlegible Next, which the product owner saw; session W1 chose only the heading
   lettering. Task W2 keeps Source Sans 3 until session W2 says otherwise: it is already
   licensed, self-hosted and measured, and its default figures are tabular, which money and
   months need.
7. **Stillness is a first-class version.** Reduced motion, calm mode and a browser without
   WebGL2 draw the same states and words without motion. A visible control pauses ambient
   motion.
   **In the app (Task W2):** the still world is also drawn while the calm support panel shows
   (Pause keeps showing the person's own choice, and the strip says "Still while support is
   shown"), and for the rest of a visit once the moving world fails (its WebGL context lost,
   or its renderer unable to start). Calm mode is a setting in the account menu; Pause motion
   and Sound stay in the strip. **Never overwhelming** (the product owner, shown the busiest
   scene: "too busy … overwhelming"): one idea at a time, and nothing moves without meaning. The
   atmosphere keeps the breathing horizon, the aurora and light flowing along known trails; the
   shimmer that travelled the horizon and the trails' sway are gone, and the motes are cut from
   2,400 to 360. Every trail is drawn at least at its measured strength (3:1 as drawn, over the
   ground and the horizon's glow, in the references and in both of the app's worlds), with one
   recorded exception: while the calm support panel shows, the world is a dimmed, still
   backdrop and its trails may fall below 3:1, because every name and state stays in the list
   beside it and the person is not reading the world then (the controller's ruling in Task W2's
   second round of fixes). Nothing else is exempt.
   **Frame evidence:** `docs/evidence/world-frames.json` stays the record of the run on commit
   `65aed2f` (2,400 motes, before these changes). The measurement tool now records the commit,
   marks the scene synthetic, pairs each frame's main-thread and WebGL GPU time by frame number
   and counts frames over 16.7 ms; it was not run again, because its headed runs open a window
   on the product owner's screen. Task W2's acceptance slice measures again, with the product
   owner warned first.
8. **Sound is not in L0** unless the product owner asks for it at session W1.
   **The product owner asked for it** at session W1: "YEs, all three, but I want them subtle
   and evocative, not cheesy!" So L0 has three short cues, synthesised in the browser (no
   audio files, no requests): a low swell when the person's light comes on, a soft two-note
   chime when a connection lights up and a small glass tick when a skill is picked
   (`apps/web/src/lib/world/sound.ts`). Sound is off until the person turns it on with a
   visible control, every visit.
9. **Sequencing.** Sprint W (spike, session W1, references, the world in the app with the You
   chapter, session W2) runs before any more chapter interface. Session W2 is a gate: every
   rubric category, including the three v1.4 questions, at least 4.

## Consequences

- The estimate grows by 13–16 engineering days and about two hours of the product owner's
  time (plan section 6).
- The Sprint 0 compositions and the current shell are retired, not polished. Their fixture
  checks stay until Sprint W's references replace them. (Done in Task W2: `docs/design` now
  holds the world's references, and `check-data` checks the fixture values they use.)
- The slate must join destinations by shared skills, not shared words in a title (session
  2's "data analyst" finding), because a revelation is only as good as its source. That is an
  amendment to ADR 0007, made in Sprint W.
- One new web dependency, the WebGL library (three.js 0.186.1), and its types for development.
- Risks: frame rate on the target Mac, motion sensitivity, and a world that implies more
  certainty than the evidence. The budgets, the still version and decision 4 answer them
  (plan section 12).

## Amendment, 2026-10-31 (the product owner's approval of the audit)

The product owner, 2026-10-31: "The visuals are important, but they must be subservient to
having a practical, useful product." The audit found that session W2's gate (every rubric
category at least 4 before any other chapter) kept the whole decision path waiting for the
world's spectacle in its first chapter, and that on a phone the world pushed the first
decision out of view. They approved it on 2026-10-31. The truth rules of decisions 1–8 are
unchanged; what changes:

- **Decision 9, sequencing.** Sprint W closes at the world shell, the You chapter and the
  deterministic sources (Task W2E). Session W2 is a short first look: about 30 minutes, live,
  about five questions, and no score threshold. Each later chapter is built in the world to
  Sprint W's references, its working view (words, choices and numbers) first. The chapters'
  moments come in a new Sprint M (Task M), after the decision path works, in the order the
  product owner chooses at the end-to-end session. The threshold, every rubric category at
  least 4, applies at release (Task 16).
- **Practical first** (plan section 4; `CLAUDE.md`). Where the world and the decision path
  compete, the path comes first. On a phone the decision comes first, and the world takes no
  more room than what it shows.
- **Decision 3.** Its rules stay provisional until the product owner confirms them at
  session W2 or, for the strength's interface, in Sprint M. The strength's proposal and
  confirm step, its holding back on a support turn and its destinations on the horizon ship
  together in Task M.
- **Decision 4.** From the product owner's ESCO research: skills a role usually needs are
  described as what ESCO lists for that kind of work; the person can mark one "not part of
  my job"; no revelation rests on ESCO's essential skills alone (how the unexpected
  connection meets it is to be settled by Task 6d). A role the person never named, found in
  sources, is a revelation with a deterministic source (ADR 0015).
- **Decisions 5 and 6.** Leaf green for "accept" and Source Sans 3 for body text stay
  provisional; they are two of session W2's five questions.
- **Decision 7.** Its frame evidence now reads: Task M and Task 16 measure again, with the
  product owner warned first, because the measurement opens a window on their screen. Its
  strip wording is corrected by Task W2E, which moves the motion and sound switches into
  the account menu below desktop width.
- **References.** Once a chapter is built, the app's own Storybook stories become its
  reference, and its place in the hand-drawn design compositions is retired (task file
  ruling R13).
- **The spike.** `spikes/world` is deleted after session W2 (Task 10), the audit's ruling;
  it stays in git history.

Consequences: plan v1.5 (sections 1, 4, 5 and 6, and the Sprint W and new Sprint M cards);
Global Constraint 11 and rulings R13 and R14 in the task file; Tasks W2E and M.
