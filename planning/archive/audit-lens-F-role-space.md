# Audit lens F: the role space beyond a standard list

Task A1, lens F. Read-only. Repository `l0-local-release`, HEAD 8e78060, 2026-10-31.
Question: how can Careerwright stop being limited to a prefilled list of roles (today ESCO),
so a person's ideal job can appear and be chosen, with research and language models
filling out the role space, without breaking the trust rules in `CLAUDE.md`?

The product owner's requirement (2026-10-31), verbatim: "we aren't limited to a prefilled
list of roles ... I want to avoid the frustration of your ideal job not appearing as an
option to select. This is where deep research and LLMs have a part to play to fill out the
"role space" more fully. I want it to feel like you have an omniscient career coach who
knows all possible jobs that could fit you."

Method: read the specification (sections 1, 3–8, 10, 11, 18, 20, 21), the plan (sections 1,
4, Sprints 2–3, SW.5), `l0-sprint-tasks.md` (R9, A1, W2 remainder, Tasks 5, 8, 10, 12),
ADRs 0001, 0003, 0006, 0007, 0009, 0010, 0011, 0012, 0014, the ledger's W2B lines, the
session 2 answers, the register's DIV-1, REC-1 and TAX-1 rows, the code named below, and the
product owner's `esco_research.txt`. Offline counts over the pinned ESCO and ONS files in
`var/datasets/` used small read-only scripts (Python `-I`, in the scratchpad); my title
folding approximates `careerwright.concept_key` (case, punctuation, a simple plural), so
counts are close, not exact.

---

## Top findings

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| F1 | **"Roles come only from ESCO" is an ADR ruling and a plan call, not a specification requirement.** The spec (M0, DIV-1) says a role library is "never the universe of recommendable careers", asks for "emerging roles absent from older taxonomies", keeps titles outside ESCO as provisional concepts, and lets a model's title count once "corroborated by an authoritative occupational/professional source or independent employer evidence". ADR 0007 narrowed that to "only if ESCO holds it as a label". The register marks the employer-evidence half as deferred to Task 7; Task 7 never built it. | spec 261, 263, 271; ADR 0007:124; register DIV1-04 ("verified (ESCO corroboration; employer evidence from T7)"); ADR 0009 has no corroboration decision; `grep corroborat backend/src` finds none for titles | high |
| F2 | **An authoritative UK title list is already pinned, imported and licensed, and unused for discovery.** The ONS SOC 2020 coding index (v14, 2026-08-27, OGL v3.0) is in `soc2020_index_entries` with a normalised-title index: 23,898 distinct titles, **20,334 of them no ESCO label**. It holds "Registered nurse" (P04), "Data quality analyst" (P01's target), "Prompt engineer", "UX researcher", "Customer success manager", "Content designer", "Heat pump installer", "Retrofit coordinator", "Cyber security analyst", "Doula". Each title carries ONS's own SOC 2020 unit group and ISCO-08 code. It is used today only to suggest SOC candidates for pay. | `catalogue/soc.py:1-40`; migration `r0027_reference_data.py:73-81`; my count over `var/datasets/ons-soc2020-volume2-coding-index-v14.xlsx`; spec TAX-1 (line ~342: "ONS ... supplies an ISCO-coded job-title index") | high (counts approximate) |
| F3 | **The roles the product models most deeply are the ones the You chapter cannot recognise.** The reviewed option pack's targets are "Data quality analyst", "IT support technician", "Registered nurse" and "Bookkeeping assistant"; three of the four are not ESCO titles, so their slates are empty ("nothing joins them, and the slate says so"). The pack already solved this with a human-reviewed crosswalk from each real title to its nearest ESCO occupation, which the product owner approved at session 2. | `england-option-pack-0.2.0.json` `targets`; `capability-reference-0.2.0.json` `targets[].note` ("ESCO holds no label 'data quality analyst'"); ADR 0007:740-741; ADR 0012:315 ("Yes to the four occupation crosswalks") | high |
| F4 | **The limit is in recognition and discovery, not further down.** Searching for jobs already takes any confirmed target title as text (source search, Adzuna). Readiness is `insufficient_coverage` for every role without pack rows, which is already true for 3,035 of 3,039 ESCO occupations. Options exist only for the pack's four targets. So a role from outside ESCO loses almost nothing downstream compared with an ESCO role outside the pack. | `evidence/search.py:279`; `evidence/adzuna.py:65` (`what`); ADR 0012:202 (`insufficient_coverage`: "an unknown target, ESCO seed rows only"); pack targets | high |
| F5 | **The model already proposes titles, and they are thrown away.** Each discovery returns up to 3 "surprising but plausible" titles quoting the person's answers. A title not held by ESCO is shown only as one line: "Titles Careerwright thought of but couldn't match to an occupation in ESCO, so not suggested: ...". That line is the PO's frustration, built into the product. | `profile/discovery.py:37, 125-129`; `profile/exploration.py:818-825`; `apps/web/src/components/Directions.tsx:608-611` | high |
| F6 | **Nothing in the web app yet calls the type-ahead, the first-answer command or provisional concepts.** The generated client has `matchTitles`, `chooseRole` and `registerProvisionalConcept`; no component uses them. The first answer's command needs an ESCO concept ID. So the first ten seconds can still be built role-open, at the cost of no rework. | `grep` over `apps/web/src` outside `generated/` finds no caller; `profile/exploration.py:1294` (`concept_id: ... An occupation from GET /v1/taxonomy/titles`); `l0-sprint-tasks.md` W2C part 2 lists the type-ahead as not built | high |

---

## 1. Where the role space is limited today

| Place | What limits it | Evidence | Source of the limit |
|---|---|---|---|
| First question type-ahead | Searches ESCO preferred and alternative labels only; no title outside ESCO can be picked; when no title holds every word it offers "closest" ESCO titles | `catalogue/taxonomy.py:188-218`; plan 178 ("matching job titles from the pinned ESCO release ... (the plan's call, v1.4)") | plan choice (v1.4) |
| First answer (`POST .../origin/role`) | Takes an ESCO `concept_id` only; the person's label is kept but must be an ESCO label of that occupation | `profile/exploration.py:1288-1300` | code choice (W2B) |
| The person's own titles (current role, targets) | Resolved by ESCO choice or ESCO label; "A title ESCO does not hold joins nothing" | `profile/titles.py:1-9, 33-72`; ADR 0007 decision 13 | ADR 0007 ruling |
| The slate | Deterministic code over ESCO: titles join by ≥3 shared ESCO essential skills; every other search reaches work only through one ESCO essential skill label | ADR 0007 decisions 5, 13; `CLAUDE.md:132-134` | ADR 0007 + `CLAUDE.md` |
| Model title ideas | Up to 3; a suggestion only if ESCO holds the title; else one line "not suggested" | `profile/discovery.py:37`; `profile/exploration.py:818-825`; ADR 0007:124 | ADR 0007 (stricter than spec DIV-1) |
| Provisional concepts | Exist (workspace-private, `concept_kind: "provisional"`), API only, no UI caller; a model's title is refused; no sources beyond "you confirmed it"; nothing downstream reads them | `profile/concepts.py:1-13, 49-103`; ADR 0006 decision 5 | ADR 0006 + unbuilt UI |
| Early sketch | A title ESCO doesn't hold gets no requirement list, only "Careerwright couldn't match it in ESCO" | `profile/sketch.py:43-47`; `apps/web/src/lib/vocabulary.ts:443-444` | code choice |
| Unexpected connection | Only between a role naming exactly one ESCO occupation and a slate suggestion | ADR 0007 decision 14 | ADR 0007 |
| Overlooked strength | Destinations are targets naming one ESCO occupation and the first slate; the skill must be an ESCO essential skill | ADR 0014 decision 3 | ADR 0014 |
| "Usual in your role" | ESCO essential skills, display only | plan 170; ADR 0014 decision 4 | plan call (v1.4) |
| Targets | Any title can be a target (profile text, hard constraint); a chosen ESCO occupation adds an `occupation_choice` source | ADR 0006 decision 6; ADR 0007 decision 6 | not limited (text), but unrecognised downstream |
| Capability matrices | Rows from pack postings (four pack targets only) plus ESCO seed rows (unknown, never readiness); target → pack by title or ESCO crosswalk | ADR 0012 decisions 3, 10 | ADR 0012; depth limited by the pack, not ESCO |
| Crosswalks | One ESCO occupation per pack target, human-reviewed | `capability-reference-0.2.0.json` | ADR 0012 (PO-approved at session 2) |
| Pay (ASHE / SOC) | Reached from an ESCO occupation's ISCO group → SOC candidates; modelled pay only via a reviewed mapping (none in L0) | ADR 0010 decision 5; `CLAUDE.md:163` | ADR 0010 + spec TAX-1 |
| AI evidence | ILO by ISCO-08 group; O*NET via the ESCO crosswalk; resilience unscored for every real role | ADR 0010 decisions 6, 7 | ADR 0010; unscored for all |
| Option pack | Four targets; live research of options (R9) not built | ADR 0011; `l0-sprint-tasks.md:144-152` | spec D1 + plan |
| Job search and map | Title-agnostic: any confirmed target title and city; Adzuna `what=` any text | `evidence/search.py:279, 290`; `evidence/adzuna.py:65` | not limited |
| Opportunity map (Task 8) | Not built; consumes pack postings | `l0-sprint-tasks.md:802-838` | plan |

---

## 2. What the authorities require

- **Specification (M0, DIV-1, spec 259-289):** full-taxonomy retrieval plus "current evidence,
  including local-language titles, specialist associations and emerging roles absent from
  older taxonomies"; ESCO full-text plus aliases is the *M0 retrieval mechanism*, not the
  universe; "Verified user-supplied titles absent from ESCO remain provisional internal
  concepts"; "LLM-generated titles are search hypotheses until corroborated by an
  authoritative occupational/professional source or independent employer evidence;
  duplicated adverts do not constitute independent support"; channel 5 is "user-proposed
  roles and 'surprising but plausible' LLM hypotheses, subjected to the same grounding". "A
  lack of live vacancies is a demand/availability signal, not proof that an occupation does
  not exist."
- **Specification (M0, REC-1, spec 251-253):** a `CareerSuggestion` holds "canonical concept
  **or provisional concept ID**" and supporting source IDs; "A confident user may skip this
  service and enter their own titles".
- **Specification, M1 parts:** research method (spec 326-336: resolve a title to one or more
  codes with a reviewable mapping, retrieve primary sources, extract supported claims);
  matrices (spec 507: "a missing template must trigger supported on-demand research, never
  make a career unrecommendable"); reference library (spec 530: "Unsupported roles remain
  explorable"). Muse Wonder is M1 (spec 27).
- **Specification bounds that still apply:** no autonomous crawling, spider or embeddings
  (spec 63, section 6); Meta search discovers URLs, Scrapling-HTTP fetches selected pages;
  research stays private to its workspace; live research records are `review_state:
  proposed` (spec 630; R9).
- **Plan:** S2.1 "Preserve provisional internal concepts for corroborated titles outside
  ESCO" (plan 386). Section 4 (v1.4, ADR 0014) chose ESCO for the type-ahead and the first
  trails ("the plan's call"), and "Revelations are earned" from deterministic sources and
  verified spans (plan 172). Nothing in the plan forbids non-ESCO roles.
- **ADRs:** ADR 0006 decision 5 (provisional concepts for the person's own titles; model
  titles refused); ADR 0007 decisions 4, 5, 13 ("the model proposes searches, never
  suggestions"; a model title only if ESCO holds it); ADR 0009 decision 12 (source search:
  one target title and one city, candidate URLs only, never claims); ADR 0010 (pay only
  through reviewed mappings); ADR 0012 decision 10 (ESCO seed by choice, label, then
  crosswalk); ADR 0014 decision 3.
- **Net:** the spec allows, and in DIV-1 asks for, roles outside ESCO, provided each is
  grounded (an authoritative occupational source or independent employer evidence) and the
  model never commits it. The ESCO-only rule is a stricter local ruling that can be amended
  by ADR, with `CLAUDE.md:132-134` updated to match.

---

## 3. The product owner's ESCO research, weighed against the design

Release check: the repository pins **ESCO v1.2.1** (`catalogue/esco.py:54-66`), the server's
`Last-Modified` was 2025-12-16 (`docs/dependencies.md:188`), and the newest occupation
`modifiedDate` in the pinned file is 2025-12-15. That matches the research's "v1.2.1,
published in December 2025", so its points apply to the release in use. I checked its
concrete example in the pinned file: the software developer's 24 essential skills still
include "perform scientific research" and "use technical drawing software". In the same
file, 54 skills are essential to more than 100 occupations ("manage staff" 261, "quality
standards" 248, "troubleshoot" 246).

| Research point | Current design | Agrees / conflicts | Recommendation |
|---|---|---|---|
| Keep the original title | The first answer keeps the person's picked label (`exploration.py:1295-1300`; ledger 680 "their words stay theirs"); but only an ESCO label can be picked | partly conflicts | Accept any title in the person's words (provisional concept), always |
| Keep seniority and industry separately | The profile has no seniority or industry field; the type-ahead drops status words when matching (`taxonomy.py:168-170`). Spec TargetRole has `seniority` (spec 1106-1109) and target hypotheses list seniority and industry (spec 225) | conflicts (build gap against the spec) | Add optional seniority and industry beside a title; matching ignores them, display and search keep them |
| Several plausible mappings, including an explicit poor fit | Ambiguous titles keep every occupation, none picked (ADR 0007 decision 13): agrees. No "none of these fits" outcome; capability crosswalks are one-to-one | partly conflicts | Offer the candidate occupations and "None of these is my job"; a role with none gets no ESCO seed and says so |
| Validate important requirements against actual jobs | ESCO rows are seeds, unknown, never in readiness; requirement rows come from postings with spans (ADR 0012 decision 3) | **agrees** | Keep |
| Essential/optional is too crude for capability | Rubrics with behavioural levels exist only for pack rows; ESCO rows have none | **agrees** | Keep |
| Implausible occupation–skill links | "Usual in your role" draws ESCO essential skills; the slate joins, the unexpected connection and the overlooked strength all rest on ESCO essential skills alone | **conflicts** | Word "usual" as "ESCO lists these for this kind of work", let the person mark a skill "not part of my job", and never let an ESCO essential skill alone be a revelation's only support (other lenses may own this) |
| Shared skills do not make a transition feasible | The connection is worded as a fact about two roles, not the person (ADR 0007 decision 14). But the slate's main retrieval is shared essential skills, and the world draws a trail between them (plan SW.5, plan 530) | partly conflicts | Keep the wording; make sure no trail between roles reads as a route |
| Separate evidence for pay, demand, qualifications, transitions | ASHE, adverts, AI evidence and gates are separate records (ADR 0010, 0012) | **agrees** | Keep |
| Update lag; not built for UK use | Only ESCO is used for titles | conflicts | Add the ONS UK index (F2), updated 2026-08-27 |

Net: the research supports **ESCO as a reference vocabulary under a richer role record**.
That is what the option pack already does for its four targets (F3), and what the design
below generalises.

---

## 4. Existing parts that can carry it

| Part | What it could do for the role space | What is missing |
|---|---|---|
| ONS SOC 2020 coding index (`catalogue/soc.py`, `soc2020_index_entries`, normalised-title index) | Recognise about 24,000 UK titles offline, at no cost, in demo too; give each ONS's SOC unit group and ISCO-08 code; count as an "authoritative occupational source" for DIV-1 corroboration | A title search over it; a resolution kind for "UK title (ONS)"; ranking against ESCO in the type-ahead; showing ambiguity (e.g. "Registered nurse" is coded to two SOC groups, 2235 and 2237); some titles are dated ("Bookkeeper-typist") |
| ISCO-08 bridge to ESCO | From an ONS title's ISCO group, list the ESCO occupations in that group for the person to choose (median 4 per group; max 91) | The choice step and "none fits". It is a set of candidates, not an answer: "Data quality analyst" is ISCO 2421 in ONS, while the reviewed crosswalk picked data quality specialist (ISCO 2519) |
| Discovery title ideas (`profile/discovery.py`, `ModelHypothesis.based_on`, checked by `check_discovery`) | The "coach" part: the model names real-world titles from the person's own answers; quotes already verified | Corroboration beyond ESCO labels; a place on the slate; more than 3 |
| Quotation verifier (`profile/slate_explanation.py:411 span_offsets`, `:456 accepted_quotation`) | Check a title or a duty sentence is a verbatim span of a fetched page or the person's answers | Nothing: reusable as is |
| Source search (`evidence/search.py`, `search_agent.py`) | Meta web search for pages describing a title; deterministic URL and manifest checks; "grounded" flag | A role-research prompt (title plus "England" only, keeping SEC-05); quality is unqualified ("The live search proposed no candidate in two tries", ADR 0009:592); demo never searches (database CHECK) |
| Guarded fetcher and restricted acquisition worker (ADR 0009 decisions 1-4) | Fetch the candidate pages safely, with robots, pacing, redaction and rights classes; unlisted hosts keep hash and excerpts, enough for spans | An acquisition purpose "role evidence" (today it fetches postings per target) |
| Page extraction (`page_extraction`, `evidence/extraction.py:581`) | Model quotes, code approves: duties, entry requirements and pay as verified spans | A role-description schema (today's is a job posting); cap of 5 per acquisition |
| Adzuna adapter (`evidence/adzuna.py`) | Free-tier search on any title: distinct employers using a title count as "independent employer evidence"; syndicated copies already fold into one job (ADR 0009 decision 6) | Live-vacancy credentials only; snippets only; not wired to title ideas |
| Source manifest (`evidence/sources.json`) | `nationalcareers.service.gov.uk` is permitted and keepable (OGL): its job profiles are an authoritative careers source for UK roles | Nothing for a first slice |
| ASHE and ILO by code (ADR 0010) | An ONS-coded title can show its unit group's ASHE figures by region and its ISCO group's exposure, each labelled as the group's | A product owner decision (see section 6, D4); modelled pay and the salary floor unchanged |
| Option pack plus capability reference | The pattern for depth: a real-world title, postings with spans, a reviewed crosswalk to the nearest ESCO occupation | Generalising it to researched roles (later, with Tasks 10 and 12) |
| Capability states (ADR 0012 decision 7) | `insufficient_coverage` already says honestly that nothing covers a target | Nothing |
| Sketch resolutions (`profile/sketch.py:43-47`) | `provisional` and `not_found` exist | A "UK title (ONS)" and a "researched" state with their words |

---

## 5. Designs compared

All costs are per person in USD, from `identity/model_registry.py` prices (Spark production
$1.25 / $4.25 per million input / output tokens; Wonder $4.00 / $20.00; search $0.0025 per
query) times the token counts measured in `docs/evidence/live-usage.md`. Measured: a
production web-search call, 9,434 in / 482 out / 1 search = $0.0151 (row 7); test-model
source searches of 4,800–9,053 in, 384–909 out, 1–2 searches (rows 27–30); a discovery call,
530 in / 568–761 out (rows 20, 24, 25). The page-extraction figure (about 3,500 in / 600 out
for a real 8 KB page) is my estimate: only a synthetic page was measured (row 31: 700 / 460).
Worst cases are the reservations each task takes at its bounds.

| | D. UK title index first (deterministic) | A. Researched roles (model proposes, sources corroborate) | B. ESCO spine plus real-world variants | C. One deep-research run per person |
|---|---|---|---|---|
| Constraint it optimises | Zero cost, offline, fastest to true | Openness: any real role can appear | Minimal change to the tuned slate | Maximum "omniscient" breadth in one go |
| What the person sees | Their title is recognised (ESCO or ONS) or kept in their words; ONS-listed title ideas appear as suggestions | Plus: "Research this role" for any title; a researched role card with where it was found, quoted | ESCO suggestions, each with "adverts also call it ..." variants to choose as their title | A role map of 10–15 kinds of work from sources and their words, as one revelation |
| Honesty enforced by | Exact title match in a pinned, hashed ONS file; no claim beyond "ONS lists this title in group X" | `span_offsets` on fetched visible text; ≥2 independent hosts or employers, or 1 authoritative class; syndicated copies fold; records `proposed` (R9) | Variant strings are verbatim advert or ONS titles | Same checks as A, over many more claims; more model judgement in what is searched |
| Model cost, Spark | $0 extra (title ideas ride on the existing discovery call, about $0.004) | Title check per role about $0.013–0.015 (worst $0.045); optional duty quotes on 3 pages +about $0.02 (worst +$0.14). 3 roles: about $0.04–0.11 | $0 (Adzuna free tier) | About $0.09 for one 5-call run plus about $0.06 for page quotes: about $0.15 |
| Model cost, Wonder | $0 extra (discovery about $0.016) | Per role about $0.03–0.05 (worst $0.14); quotes +about $0.08 (worst +$0.49). 3 roles: about $0.10–0.38 | $0 | About $0.27 plus $0.21: about $0.5; one attempt at its bounds (about $0.32) exceeds the default $0.15 run limit (ADR 0006 decision 9) |
| Works in demo / without a key | Yes | No (demo never searches) | No (live-vacancy only) | No |
| Later chapters for a role outside ESCO | See the table below | Same, plus advertised pay and duties as quoted claims | Unchanged: the role stays ESCO-backed | Same as A |
| Rough effort (agent days, incl. review) | 3–5 | 6–10 (after D) | 3–5 | 10–15, plus qualifying more than 2 search calls (only 1–2 qualified, row 29) and Wonder |
| Main risk | Feels like "a bigger list", not a coach | Search quality unqualified; per-role spend; new run purpose | Doesn't reach roles ESCO has no neighbour for (P05's "Bookkeeping assistant" is in neither list) | Cost, latency, a large opaque run; close to the "general agent" the plan excludes |

### What the later chapters can compute for a role outside ESCO (designs D and A)

| Chapter | Can compute | Must show as unknown or not yet |
|---|---|---|
| Skills | With a chosen closest ESCO occupation: its essential skills as "ESCO lists these" (display only); the person's answers as evidence | Requirements, levels and readiness: `insufficient_coverage` (as for every ESCO role outside the pack); with "none fits": no rows at all |
| Pay | ONS-coded title: ASHE for its own SOC unit group(s) by region, labelled the group's (as unreviewed ESCO occupations already show per candidate group, ADR 0010 decision 5). Design A: advertised pay read from verified spans | Modelled pay and the salary floor: unchanged, still need a reviewed mapping; city pay never |
| AI evidence | ISCO group exposure, labelled the group's | Resilience: unscored (as for every real role in L0) |
| Roles (jobs, map) | Source search and Adzuna on the title as text (already) | "No listings" is a demand signal, not "this job doesn't exist" (DIV1-09) |
| Options, Routes, Plan | The sketch's generic steps, unresolved | Options, costs, dates, routes: "not researched yet" (as for every role outside the pack) |

### D. UK title index first

- Type-ahead over ESCO labels and ONS index titles, ESCO first on ties; an ONS title shows
  "UK job title (ONS)". "Use my own words: '...'" is always offered; nothing is refused.
- Picking an ONS title keeps the person's words and records ONS's SOC and ISCO codes as its
  source. The world asks one question: "Which of these is closest?" (the ESCO occupations in
  that ISCO group) or "None of these is my job".
- A model title idea the ONS index lists is corroborated (an authoritative occupational
  source, DIV-1) and shown in its own short list beside the slate, "Title ideas found in the
  UK job-title index", with the answers it came from. It is kept apart from the tuned ESCO
  slate, so none of W2B's matching rules change.
- Code: a title search over `soc2020_index_entries.normalised`; a resolution kind; a
  provisional concept with an ONS source; the ESCO candidate list by ISCO group.

### A. Researched roles

- A `role_research` purpose on the existing source search: input is one title and
  "England" (SEC-05 kept: never the person's answers). Prompt: pages that describe this
  role, such as National Careers Service profiles, professional bodies and employer adverts.
- The acquisition worker fetches up to 5 candidate pages. Code checks the title is a
  verbatim span of each page's visible text (`span_offsets`); no model is needed for that.
- **Corroborated** when the title is verified on pages from ≥2 independent hosts or
  employers (copies fold, ADR 0009 decision 6), or on 1 page of an authoritative class
  (`govuk`, `public-sector`, `professional-body`). Otherwise it stays a "title idea, not yet
  found in sources", visible, never hidden, never a suggestion.
- Optional, on opening the card: a role-description extraction quotes duties and entry
  requirements as spans (the `page_extraction` pattern). Records are workspace-private,
  `review_state: proposed`, dated (spec 630, R9).
- The person's own title is always choosable without research. A model's idea is choosable
  only once corroborated (DIV-1).

### B. ESCO spine plus real-world variants

For each ESCO suggestion, list the ONS index titles in its ISCO group and Adzuna advert
titles from distinct employers as "also called". The person may choose a variant as their
title. It is cheap and keeps the slate, but it only reaches roles ESCO already has a
neighbour for. It inherits the slate's empty results for P01, P04 and P05 (ADR 0007:740-741)
and the shared-skill problems in section 3.

### C. One deep-research run per person

One bounded Wonder run with several searches maps the role space from the person's work
answers and sources. It is the closest literal match to "omniscient", but:
- the person's words would reach a web-searching model (SEC-05 changes);
- more than 2 tool calls is unqualified;
- its worst case breaks the default run limit and the "three attempts fit" rule
  (ADR 0006 decision 9; ADR 0009 decision 12);
- it is one large, slow, opaque step.

Defer it to M1 (spec 27: Wonder is M1).

---

## 6. Recommendation

**Do D now, then A. Do not build B. Leave C for M1.** D removes the dead end ("couldn't
match that title") for most real UK titles at no cost, offline and in demo. It also gives
DIV-1 the corroborating source the spec names. A then covers what no list holds, which is
the PO's "deep research and LLMs" part, on demand and per title, at about 1–5 US cents a
title on Spark. Both keep every trust rule:
- the model proposes;
- deterministic code corroborates against a pinned file or verified spans;
- the person chooses;
- unknown stays shadow;
- no claim of fit, pay, readiness or vacancies beyond the evidence.

Both reuse the option pack's proven pattern: a real title, evidence with spans, and a
human-chosen link to the nearest ESCO occupation (F3), with "none fits" added, as the
research asks.

### The smallest first slice: "your title, recognised"

Scope:
- The type-ahead over ESCO and the ONS index.
- "Use my own words" (a provisional concept).
- The closest ESCO occupations by ISCO group, with "None of these is my job".
- A title's resolution and words through the sketch and slate.
- The discovery's title ideas corroborated by the ONS index, shown in their own list.
- No new model call, no change to W2B's slate rules.
- It replaces W2C part 2's planned "Careerwright couldn't match that title in ESCO. Is it
  one of these?" item, which is not built yet (F6).

Acceptance test, in plain words:
1. In the demo workspace, with no key and no network, type "Registered nurse", "Data
   quality analyst", "Prompt engineer" and "Doula" at the first question. Each appears as a
   title to pick, marked as a UK job title from ONS.
2. Picking one keeps your exact words. The world answers within a second. It offers the
   ESCO occupations in the same ONS group and "None of these is my job".
3. Type "Bookkeeping assistant", which neither list holds. "Use my own words" is offered
   and kept, and the world still answers. It says what isn't known yet and asks no one to
   pick a different job.
4. When a discovery's title idea is in the ONS index, it shows as a suggestion with the
   answers it came from and "found in the UK job-title index". An idea in no list is shown
   as not yet found, never as a suggestion.
5. No screen states skills, pay, readiness or job openings for these titles beyond what
   their sources hold.

Second slice (A, "Research this role"):
- Acceptance: on the test model with a synthetic title, one run. Pages from two different
  hosts that both contain the title make it corroborated, with both quotes and dates one
  step away. One page, or two copies of one advert, leaves it "not yet found in
  independent sources".
- A page telling the model to do something changes nothing.
- Ledgered under R5, worst case at most $0.045 (Spark) per run.

### Documents and invariants that would change (described, not applied)

- **Specification (v1.4, product owner's approval):**
  - DIV-1 (M0): name the pinned ONS SOC 2020 coding index, already a TAX-1 input, as an
    authoritative occupational source for corroborating titles.
  - DIV-1: spell out "independent" (distinct hosts or employers; syndicated copies fold)
    and define a researched role as a provisional concept with its SourceClaims.
  - BND-1's discovery row ("full English ESCO catalogue", spec 44) adds the ONS index.
  - No invariant is relaxed.
- **Plan (v1.5):**
  - Section 4, the first ten seconds (plan 178): titles from ESCO and ONS, and the person's
    own words always accepted.
  - "Revelations are earned" (plan 172): add "a role you never named, found in sources",
    from deterministic corroboration.
  - S2.1 and S2.4 notes.
  - SW.5 and W2C part 2 reshaped as above.
  - A new card for role research before Task 8 (the Roles chapter's cards need it).
- **ADR 0006 decision 5:** provisional concepts carry sources (ONS entry, verified pages);
  a model's title becomes one only once corroborated.
- **ADR 0007 decisions 4, 5 and 13:**
  - "A model title becomes a candidate only if ESCO holds it" becomes "... if ESCO holds
    it, ONS's coding index lists it, or verified independent sources name it".
  - The slate stays deterministic code; corroborated ideas sit in their own list.
- **ADR 0009 decision 12:** a second search purpose, role research, whose input is one
  title and "England" (SEC-05 unchanged); a role-evidence acquisition; a role-description
  extraction schema.
- **ADR 0010:** an ONS-coded title uses ONS's own codes for ASHE candidate figures and ILO
  group exposure, labelled as the group's. Modelled pay and the floor are unchanged.
- **ADR 0012 decision 10:** the ESCO seed for a provisional or researched role is the
  person's chosen closest occupation, or none ("none fits" means no seed, so
  `insufficient_coverage`). Optional seniority and industry fields go in the profile (spec
  225, 1109; the PO's research).
- **ADR 0014 decision 3:** the researched-role revelation as a source.
- **New ADR 0015, "The role space":** the layers, the corroboration rule, the record, the
  per-role spend caps and the model choice.
- **`CLAUDE.md:132-134`:** "In discovery the model proposes searches only; the slate is
  deterministic code over ESCO" becomes "In discovery the model proposes searches and title
  ideas. A title idea becomes a suggestion only when deterministic code corroborates it (an
  ESCO label, the ONS coding index, or the title verified as a span on independent permitted
  pages). The slate is deterministic code."
- **Register:**
  - Correct DIV1-04's status: employer evidence was never built.
  - Update DIV1-03, DIV1-10 and REC1-06.
  - Add rows for the new behaviour.

### Decisions that are the product owner's (one sentence each)

1. Should Careerwright recognise any UK job title that ONS lists (about 24,000), not only
   ESCO's? Yes adds them to the first question and to the title ideas, at no cost.
2. Should a person always be able to keep their own job title, even one no list holds? Yes
   means the world answers "not researched yet" instead of asking them to pick another job.
3. Should a title idea count as real when ONS lists it, or when two independent web pages
   name it? Yes makes those the two ways a new role can appear.
4. Should an ONS-listed title show the official pay figures for its whole ONS group, clearly
   labelled as the group's? Yes shows group pay; no keeps pay unknown for these titles.
5. Should Careerwright research a title no list holds, with one web search and the pages it
   finds, at about 1–5 US cents a title? Yes builds the second slice.
6. Should a role keep an optional seniority and industry beside its title, as your ESCO
   research advises? Yes adds two optional fields that matching ignores.

### Plan placement

- Slice D belongs inside W2C part 2, which already owns the type-ahead and the first
  answer's ignition. It has no backend dependency on later tasks.
- Slice A is mostly backend (run purpose, acquisition, corroboration). It can run while
  sessions are awaited, like 7c and 13a. Its card belongs before Task 8.
- A full role-research run on Wonder belongs with A1 question 4's decision. On Wonder,
  three attempts at the extraction bound (about $0.16 each) do not fit the default $0.15
  run limit, so a provider outage would read as "over budget" unless the limit for that
  kind is raised.

---

## 7. What I could not check

- No live calls (rules). The role-research search quality is unknown. The existing source
  search's candidate quality is itself unqualified (ADR 0009:592).
- Wonder costs are registry prices times Spark's measured token counts. Wonder has never
  been called (ADR 0003: not selected).
- Real-page extraction tokens are estimated. Only a synthetic page was measured (row 31).
- My ESCO and ONS title counts fold titles with an approximation of `concept_key`, run over
  the pinned files. They were not run against the database or the SQL function.
- I did not run the app, tests or `make check` (the shared rules say not to).
- The PO's research links and the ESCO publication date were not checked on the web. The
  date is inferred from the pinned file (`Last-Modified` 2025-12-16, newest `modifiedDate`
  2025-12-15).
- Whether search reaches National Careers Service profiles, and the robots rules of likely
  role pages, are untested.
- Rights for any new source class need human review (session 1's policy covers the
  existing classes).
- Intent, for the product owner: whether ONS-listed titles alone feel like "the role space
  filled out", or whether model-researched roles are required in L0. Decisions 1 and 5
  separate the two.
