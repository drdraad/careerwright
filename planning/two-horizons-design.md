# "Next step" and "Aim higher": design note (3 November 2026)

Read-only design by a planning agent, dispatched by the controller after the product owner's
re-test ("a lot of the role suggestions are quite basic ... not very aspirational or
inspirational. I think we need to distinguish between immediate next job ... and ideal job").
The product owner said yes to building it after Task W2F and before 10B, 12bB and 14B.

## Why today's slate favours basic roles
- Sam's six suggestions sit at ISCO skill levels 1-3: Bookmaker 4212 (2), Club host 5169 (2),
  Restaurant host 5131 (2), Head chef 3434 (3), Laundromat attendant 9629 (1), Equine dental
  technician 3240 (3).
- One door into the catalogue: a search reaches work only through an ESCO essential-skill label
  holding every word of the search (exploration.py:559-584; taxonomy_store.py:253-298). "assist
  customers" is essential for 35 occupations, 26 in major group 5.
- Ties lean to simpler work: equal scores per skill (exploration.py:587-599), ties to the larger
  share of essential skills reached (slate.py:370-374, 390-400); ESCO lists fewer essential skills
  for elementary (mean 15.6) and clerical (16.8) work than for professionals (27.4) or managers
  (25.7); each further query adds 0.2 (slate.py:67, 355-359).
- The relevance floor is per query's own best hit, so any query's best clears it
  (exploration.py:589-593; slate.py:65; ADR 0007:170-173).
- Nothing knows level or path length by design (slate.py:13-15; ADR 0007:149-152; discovery.py:
  259-260 "Do not favour popular, prestigious or well-paid work"; spec line 283).
- Muse barely widens the pool: at most 3 title ideas (discovery.py:37, 262-264), joining only as
  ESCO labels (exploration.py:851, 876-886); qualifications never sent (discovery.py:47-54).
- 1,864 of ESCO's 3,039 occupations are in major groups 1-3: the catalogue is not the limit.
- "Directions to consider" is the less_familiar direction: with Sam's role in his own words there
  is no join and no familiar group (exploration.py:816-825, 891), so the balanced 2/2/2 quotas
  with a 0.4 bonus force two "less familiar" picks in (slate.py:73, 506, 571-572;
  Directions.tsx:824-825). Equine dental technician lists "assist customers", "communicate with
  customers" and "deal with challenging people".

## Common ground
- A pinned skill-level table by ISCO sub-major group (managers 4 except group 14 at 3;
  professionals 4; technicians 3; groups 4-8 at 2; elementary 1; armed forces 4/2/1), tested
  against ESCO's own group descriptions. A job group's level, never the person's, never prestige.
- The person's reference level from their role's ESCO occupation or agreeing ONS groups; else
  unknown, never a number (ISCO bands then: 1-2 Next step, 3-4 Aim higher).
- Next step drops the forced "less familiar" slot (quotas close 2, transferable 1) and the
  "Directions to consider" heading.
- No new service, workflow, run kind or migration; slates recomputed on read (ADR 0007:117-121).

## Approaches
- A. Deterministic ladder (code only): split today's pool by level; three each. Aim higher card:
  "Careerwright checked its job group in ISCO: most work there is at skill level 4 of 4, usually
  reached through a degree or equivalent training." No prompt change, no added model call.
  10-14 agent hours. Weakness: re-sorts the same pool (Sam's Aim higher: Head chef, Equine dental
  technician).
- B. Muse's horizon: the one discovery call also returns up to six "aim higher" title ideas, each
  quoting 1-3 answers (checked), qualifications included in what Muse reads; code confirms each
  by the existing rule (ESCO label, ONS index, or Research this role). Sam: Customer success
  manager (3339), Training and development officer (2424), Careers adviser (2423); Maya: Clinical
  scientist (2131), Genetic counsellor (3259), if proposed. About $0.019 per discovery on Wonder.
  14-18 agent hours. Strains "the slate is deterministic code"; the offline demo shows none.
- C. Hybrid (recommended): Muse widens the pool with checked ideas, code places every candidate
  by level; within Aim higher, confirmed ideas and joins rank first (policy, to be evaluated);
  an ONS title whose groups disagree on level goes in neither set. The model proposes, code checks
  and places, the person chooses. 20-26 agent hours in two slices: A first, then Muse's ideas.

## The world and the demo
- Near lights (Next step) and far lights (Aim higher): ADR 0014 decision 4 amendment (depth means
  which set, a computed fact, never how likely or how good); the key says so; the still world the
  same; ships with the suggestion rings, after the working view.
- Maya: with no job, ISCO bands decide; in B and C her A-levels reach Muse; an expected grade is
  never met. The demo's "roles she'd never have searched for" becomes true on screen.
- Sam: his "no pay cut for three years" is a planning limit, never a slate filter (only a
  confirmed salary floor filters; exploration.py:894; slate.py:534-535). Next step's common work is
  never called basic.
