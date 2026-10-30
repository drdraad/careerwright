# ADR 0014: The living world, Careerwright's experience direction

- Status: Proposed, 2026-10-30. Accepted when the product owner approves plan v1.4. Sprint W
  adds the spike's choices (decisions 2 and 6) when session W1 has made them.
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
3. **Revelations come from deterministic sources** (the slate, readiness and gaps, the route
   checker, reviewed options) and from verified spans. The one exception, by the product
   owner's answer of 2026-10-30, is an overlooked strength: the model may propose one as a
   quotation of the person's own words against an essential skill of one of their
   destinations; code verifies the span and the skill, and the person confirms it before it
   shows. It is a new bounded run kind (ADR 0006), live only, within the person's spend
   limit; the demo shows a scripted, labelled example. The model never decides a revelation,
   and a kind of revelation with no such source is not shown.
4. **The world never shows more than the evidence.** Everything that varies has a computed
   meaning; position is layout only; unknown is shadow, never zero; a condition is a gate in
   plain words; nothing implies a job offer. Skills a role usually needs show as "usual in
   your role, not confirmed yet", for display only: wherever something is computed they stay
   unresolved (ADR 0012). Distress stills the world and shows the calm support panel.
5. **Colour has one meaning each.** Orange is destinations only; the sea-glass teal is
   selection, the chosen path and the primary action only; blue and violet are atmosphere,
   graded the same along every trail. Industry moves from colour to glyph and label,
   replacing spec VIS-1's industry colours.
6. **Type.** A bold geometric sans display face and a readable sans body face, licensed and
   self-hosted; Newsreader retires. The spike chooses the faces.
7. **Stillness is a first-class version.** Reduced motion, calm mode and a browser without
   WebGL2 draw the same states and words without motion. A visible control pauses ambient
   motion.
8. **Sound is not in L0** unless the product owner asks for it at session W1.
9. **Sequencing.** Sprint W (spike, session W1, references, the world in the app with the You
   chapter, session W2) runs before any more chapter interface. Session W2 is a gate: every
   rubric category, including the three v1.4 questions, at least 4.

## Consequences

- The estimate grows by 13–16 engineering days and about two hours of the product owner's
  time (plan section 6).
- The Sprint 0 compositions and the current shell are retired, not polished. Their fixture
  checks stay until Sprint W's references replace them.
- The slate must join destinations by shared skills, not shared words in a title (session
  2's "data analyst" finding), because a revelation is only as good as its source. That is an
  amendment to ADR 0007, made in Sprint W.
- One new web dependency, the WebGL library.
- Risks: frame rate on the target Mac, motion sensitivity, and a world that implies more
  certainty than the evidence. The budgets, the still version and decision 4 answer them
  (plan section 12).
