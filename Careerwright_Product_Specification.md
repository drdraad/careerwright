# Careerwright

## Career path optimiser product specification

**Version 1.3 | 28 October 2026 | Research checked 26 October 2026 | Product and architecture specification**

**Your career. Your next chapter.**

This specification defines a career decision product that turns a person's circumstances, capabilities and ambitions into explainable, affordable sequences of learning and work. It covers the customer experience, evidence standards, optimisation model, visual system, software architecture and acceptance criteria. It specifies a proposed private-beta build boundary and later launch requirements. It excludes a day-by-day development plan, staffing estimates and a promised launch date.

**Gate convention:** requirements marked **M0** belong to the proposed private beta; **M1** requirements are additional launch gates. Unlabelled subsections inherit their chapter gate; explicit paragraph labels override that default. M1 includes M0. Historical decision records and source notes are explanatory, not implementation alternatives. “Must” denotes a requirement at its stated gate. Numeric service targets, cache periods and interview thresholds are proposed engineering or product defaults, not measured results. Market examples and path figures are illustrative unless explicitly sourced. Sources are numbered in the reference register; product prescriptions are our design judgments rather than claims that research has validated this particular application.

# 1 Product thesis and principal decisions

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

Careerwright should answer three connected questions: **What work could suit my life? What would it actually take to get there? Which achievable route makes the best use of my time and money?** Its distinctive asset is an evidence-backed transition model connecting people, skills, credentials, training, funding and work. Chat, search and graphics are interfaces to that model.

The experience has three signature surfaces: a calm conversation that uncovers both familiar and unexpected career possibilities; a living map of opportunities; and linked trade-off and journey views that make alternative routes tangible. The selected route becomes a practical, printable plan that can be revised as circumstances change.

| Decision | Specification |
|---|---|
| Name | **Careerwright**, pronounced “Ness-ah”: “I used Careerwright to plan my next move.” Descriptor: “Your personal career planner”. Warm, without pretending to be human. Provisional: check global brand/linguistic clearance and possible confusion with Nesta. [53] |
| Primary customer | An adult making a career choice, transition or progression decision. Support people who already know their target and people who do not. “Researcher” in the brief is interpreted as the person exploring their career, not a restriction to academic researchers. |
| Scope | Up to three preferred cities and three active target roles per planning workspace; zero to three user-supplied exemplar postings per role. System-discovered postings have a separate, much larger limit. Multiple saved workspaces are possible. |
| Geography | A general, global product with a shared career model and independently qualified country/region/language adapters. No country defines the domain model. Coverage is declared per capability; local rules, funding, qualifications and currencies are never inferred from an English-language template. |
| AI | User-supplied Meta Model API key; Muse Spark 1.3 for routine tasks and Muse Wonder for difficult synthesis. M0 uses a single pinned approved Spark model; Wonder and image generation are M1. All application-controlled LLM reasoning remains Meta-only, with versioned model qualification. [1-4] |
| Web acquisition | M0: pinned ESCO/ASHE imports, bounded Adzuna searches and **Scrapling HTTP** for selected permitted pages. Meta search discovers URLs. Additional feeds/acquisition capabilities are M1; no extra scraper vendor is selected. [9,34-38] |
| Optimisation | **M0:** deterministic Python depth-first enumeration of a bounded catalogue; one monthly decision grid; full archive of feasible schedules encountered. Complete means exhaustive for that model. Budget-truncated results remain approximate. No second solver in the committed stack. |
| AI Resilience Score | Retains the requested 0-10 scale, with higher meaning more resilient. Lead with an evidence-supported range; filter on its lower bound by default. This ordinal assessment is not a replacement probability. “AI Safety Score” is the former working label. |
| Architecture | React/TypeScript with SVG and D3; Python/FastAPI/Pydantic AI; DBOS; PostgreSQL. Scrapling HTTP fetch/parse only in M0. Fixed execution choices; no automatic workflow-engine or renderer substitution. [28,57,58] |
| Product integrity | No promises of employment, fabricated funding, inferred psychiatric labels, hidden sponsorship influence or silent substitution of models/data. “Unknown” remains distinguishable from “not eligible”, “not skilled” and “no opportunities”. |

## Build boundary and precedence [M0, BND-1]

**Working assumption, not confirmation:** the proposed ten-day milestone is an invitation-only private beta for a handful of adult testers. No answer confirming private beta versus public launch was supplied. M0 is therefore a reviewable proposed scope, not authorisation to recruit testers, process their information or publish. Ten days is a target supplied by the review, not an evidence-backed delivery estimate. If the milestone is public launch, the M0 label does not waive launch requirements; scope and resources must be reconsidered.

The product remains global. M0 implements **England, English and GBP**, up to three English cities and three active targets, with the country-neutral identifiers and unsupported-region states already specified. Other countries remain discoverable in the future product, but M0 must state its supported slice before collecting detailed information. Residence and eligibility are never inferred from a chosen English city. Remote opportunities are limited to explicitly compatible England-based work. No cross-border cash-flow or tax inference is implemented in M0.

A complete M0 session goes from sure/unsure entry, through a grounded shortlist, a provisional skills matrix, evidence questions and real option review, to bounded route comparison and a printable plan. A route can be conditional or unavailable; it cannot quietly replace missing evidence with invented data. M0 is not merely a landing page or a canned happy-path demo.

| Capability | M0: private-beta requirement | M1: additional launch requirement |
|---|---|---|
| Geography and discovery | England/en-GB/GBP; full English ESCO catalogue; personality-informed multi-query retrieval and diverse slates | Qualified native adapters/languages and three contrasting jurisdictions under GLO-1 |
| Source integration | Pinned ESCO and ASHE imports; live bounded Adzuna search; user-pasted full exemplars; selected-page Scrapling HTTP fetches | Broader authorised feeds including Skills England and apprenticeship APIs; rendered/PDF acquisition where qualified |
| Data identity | Internal concept ID + ESCO URI; ISCO-08 grouping; versioned, reviewed UK-SOC and O*NET mappings | Additional native taxonomies and audited crosswalks |
| Source permissions | Small checked-in source manifest: permission basis, attribution, retention, access policy, version | Managed rights/capability registry and broader source operations |
| Skills and outcomes | Provisional ESCO/exemplar matrix; explicit course-outcome records and essential/gate review | Employer-diverse full-text corpus, specialist review and maintained reference families |
| AI resilience | Range filter and unknown states; reviewed static assessments where evidence permits, with experimental badge | Routine monitoring, inter-rater qualification, supported seniority/local modifiers |
| Research and caching | User-key research; keyless fetch process; private workspace cache in PostgreSQL; a reviewed, dated option pack as an immutable public evidence pack, with live research `proposed` until reviewed (section 11) | Shared cross-tenant derived cache with separate service funding and isolation |
| Planning | Up to 24 reviewed action concepts, at most two explicit starts per action, six selected actions and 24 months; at most one conditional bridge-role transition | Longer/finer planning, multiple job transitions and adaptive scenario policies |
| Finance | Common-horizon economic cost; direct/payment caps; conservative liquidity check; existing debt as fixed commitments; confirmed grants only in unconditional figures | Qualified optimisation of new borrowing instruments and complex benefit/tax interactions |
| Solver | One Python DFS, independent checker, deterministic order, complete encountered archive, F1-F3, explicit search limits | Larger-instance qualification; any replacement algorithm requires a later specification decision, not a hidden fallback |
| Workflow and persistence | DBOS, PostgreSQL, transactional outbox; restart/cancellation/revocation tests | Broader operational and upgrade qualification; no alternative engine preselected |
| UI | List/table, cost-time points, sliders, static focused Gantt, simple SVG city/company dendrite; keyboard and unknown/error states | Motion, halo, semantic zoom, mini-map and richer comparison views |
| Images and export | Fixed licensed icons; browser print CSS, JSON and ICS downloads | Meta-generated step illustrations, dedicated tagged accessible PDF export |
| Secrets and access | Invitation checks, object ownership, TLS, authenticated key encryption with runtime key outside DB, redaction and spend caps | Tenant envelope encryption/KMS, richer account and access management |
| Privacy and operations | Pre-test privacy assessment/DPIA where required, deletion, source permissions, basic backup/restore, error logs and dependency locks | Published SLO/RPO/RTO qualification, signed builds/SBOM, OpenTelemetry, Terraform |
| Acceptance | Five synthetic persona fixtures, worked trace, critical invariant tests, real-source extraction corpus and one deployed end-to-end smoke test | Larger representative benchmarks, named-device performance qualification and cross-region outcome studies |

**Non-deferrable M0 invariants:** unknown is not zero/ineligible; failure is not an empty success; a truncated search is not infeasibility; no invented course/score/funding; LLM proposals do not directly commit facts or plans; no personal data crosses workspaces; no secrets in prompts/logs/exports; no external enrolment/application/resignation or messaging without user action; no unqualified readiness or affordability claim.

The boundary excludes autonomous crawling, embeddings, a commercial shared research service, new-loan optimisation, international eligibility automation, image generation, advanced animation and service-level promises. It does not exclude the simple dendrite or the three requested Pareto layers. Preserve full-product requirements under M1 rather than pretending they have been delivered.

### Concrete M0 dependency inventory

Three main data integrations are **not** three total integrations. Track these separately: (1) ESCO download/import, (2) ASHE download/import, (3) Adzuna API, (4) selected-page HTTP retrieval, (5) Meta model/search API, (6) Firebase Authentication, (7) DBOS/PostgreSQL, and (8) GCP deployment/storage/secrets. Static ISCO/crosswalk and AI-evidence packs are additional versioned data inputs, not invisible free dependencies. Funding pages are selected-page evidence, not three automated eligibility engines.

No automated geocoder is required in M0: use a checked, finite English-city list with identifiers and coordinates. Commute statements are user-supplied constraints requiring confirmation, not computed travel-time claims. Cache/source policies and the current funding-rule date still apply to imported snapshots.

At a hard bound, do not silently keep the first 24 actions or first two intakes. Ask the user to pin/exclude or choose retained variants; persist the removed-candidate count and the scope restriction. A regulated pathway beyond 24 months receives an explanatory sketch and an unsupported-model state, not a claim that the career is impossible.

The chapter gates below are normative. M0 acceptance is defined in section 20. The final build order and day-by-day schedule remain a separate exercise.

## The essential correction to the original idea [M0]

The optimiser can find efficient ways to satisfy a target's modelled requirements. It cannot guarantee that a person learns a skill, passes an assessment, receives funding or gets hired. Courses, offers and employment outcomes therefore have distinct states. A course can create a learning opportunity; demonstrated capability requires evidence. A future job is a conditional transition; a current vacancy is a time-limited opportunity.

Time and cost are optimised **after** preserving minimum job quality, target suitability, wellbeing-related workload preferences, essential credentials and affordability. Otherwise the mathematically cheapest path might be an irrelevant course followed by a poorly paid job the user would hate.

# 2 Working backwards press release and FAQ

**Chapter gate: M1.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Draft launch press release [M1]

*The following is a proposed future launch narrative, not an announcement of an existing product. Quotations are proposed copy, not testimonials or measured outcomes.*

### Careerwright turns career uncertainty into a plan you can see and afford

**Explore work that fits your life, compare real routes into it, and leave with a clear next step.**

Careerwright today introduces a new way to plan a career: a personal map connecting the work you want with the skills, training, funding and experience that can help you reach it.

Choosing a direction and finding vacancies leaves a difficult practical question: working out what you already know, what you still need, which opportunities are real and how to make the change without exhausting your savings or your time.

Careerwright brings those decisions together. You can start with a clear ambition or simply describe what you want to change. A guided conversation helps you explore your interests, experience and practical constraints at your own pace. Careerwright suggests a varied set of researched directions, including less familiar roles whose tasks fit your interests and working preferences. You choose up to three careers and three places where you would be happy to work, potentially across countries.

Your opportunities emerge as a living map, grouped by company and coloured by industry. Inspect pay, demand evidence and requirements where available, and filter by AI resilience. Every assessment shows its sources, date and uncertainty.

After helping you recognise your existing skills, Careerwright researches the missing pieces: courses, qualifications, apprenticeships, funding and stepping-stone roles. It compares ways to combine them while respecting your budget, monthly cash limits, available hours and commitments.

Careerwright shows both what you must pay and how a transition could change your earnings. Instead of declaring one route “best”, it shows the trade-offs. A faster path may cost more. A slower route may let you keep earning. Another may build experience through paid work. Move the time and cost controls to reveal the routes that fit, then select a path to examine each step.

“A career decision should leave you with more agency,” says the proposed founder statement. “We want people to understand their options, see what is uncertain and choose a next step they can actually take.”

Careerwright makes uncertainty visible. A job opening today is not a promise of employment next year. An advertised course is not proof that it will close a skills gap. Funding is checked against eligibility and its conditions are shown. Where the evidence is weak, the plan says what needs to be verified before committing money or making a major change.

Once you choose a route, Careerwright gives you a printable plan: the sequence, schedule, costs, application links, evidence milestones and first actions. You can return as you learn, receive an offer or change your mind. Completed work stays part of your progress, even when the destination changes.

Careerwright is designed for adults exploring work in supported regions. It uses a customer's own Meta API key, with clear usage controls. Regional coverage and any separate product charges are shown before research begins. The service does not promise a job or sell preferential placement in its recommendations.

**Careerwright. Your career. Your next chapter.**

## Customer FAQ [M1]

**What if I do not know what career I want?** Start with activities you enjoy, experiences you want to avoid and constraints that matter. Explore a few plausible directions and, where useful, try a small real-world experiment before committing to a target.

**What if I know exactly what I want?** Enter one to three titles, optionally add postings, confirm the role level and geography, and proceed directly to opportunities and skills.

**Will it tell me that I am unsuitable?** It identifies evidence, requirements and trade-offs. Interest or personality information never creates an automatic career exclusion. You can inspect and correct every consequential profile statement.

**Why are some paths grey?** Under the displayed cost definition and scenario, another route to the same target takes no longer and costs no more, with at least one advantage. The card names that route and shows the difference; it also says when the comparison changes in an adverse scenario. They may still suit an unmodelled preference. You can inspect the comparison and change your requirements.

**Does it guarantee the cheapest or fastest route?** It reports the best routes found within its data and search boundaries. A mathematical proof, when available, applies only to the specified model, candidate catalogue and assumptions.

**Can I use it without sharing sensitive personal history?** Yes. Preference and availability statements are sufficient. Health diagnoses, employer-confidential material and detailed life stories are optional and unnecessary for a basic plan.

## Internal FAQ [M1]

**Why would someone use this instead of a general chatbot?** Persistent structured evidence, regional acquisition, explicit cash-flow constraints, reproducible optimisation, inspectable alternatives and a plan that survives updates. The language model does not invent the route catalogue or compute the final budget.

**What is the hard part?** Reliable mappings between training, demonstrated skills and employment transitions; rights to useful source data; and uncertainty about future opportunities. Attractive graph rendering is necessary but cannot compensate for these gaps.

**What must remain commercially independent?** Opportunity retrieval, skill requirements, course quality assessment and route ranking. Any referral relationship must be disclosed and excluded from optimisation weights. A user-paid product or separately disclosed institutional licence is preferable to a ranking model dependent on training commissions.

# 3 End to end customer experience

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

The application uses six persistent chapters: **You, Roles, Skills, Options, Routes, Plan**. These are navigable states, not a compulsory linear wizard. Each displays useful output early, accepts partial information and shows which downstream results depend on missing facts.

| Chapter | Customer action | Durable result | Completion condition |
|---|---|---|---|
| You | Say “I know my direction” or “Help me explore”; import a CV or start fresh | Confirmed constraints and a diverse discovery shortlist, then one to three selected targets | Minimum practical inputs known; selected targets confirmed as hypotheses |
| Roles | Inspect role cards and the company/job map; save favourites | Target specification and exemplar set | At least one defined role; an evidence-backed reference role is allowed if no suitable live posting exists |
| Skills | Review the skills matrix; answer short evidence-based prompts | Capability evidence and uncertainty map | Essential requirements addressed or explicitly unresolved; interview can be paused |
| Options | Review researched courses, work routes and funding; pin or exclude options | Dated option catalogue and budget assumptions | Sufficient feasible candidates, or a clear evidence/availability shortfall |
| Routes | Adjust ranges; inspect efficient and dominated paths | Reproducible plan alternatives | User selects a route or saves comparison without commitment |
| Plan | Confirm assumptions, print/export, record a next action | Versioned action plan | User understands costs, conditions and the first action |

The unfinished bullet “Once the tangible training and job options are available” is resolved as an explicit **option-review checkpoint** before optimisation. The user must be able to correct costs, exclude a provider, pin an option and distinguish an interesting opportunity from a committed obligation.

## Minimum inputs and preferences [M0]

- A preferred name is optional. Collect work status, current role/level, experience, relevant qualifications and commitments. **M0:** paste CV/exemplar text or enter details directly. **M1:** optional file upload with isolated document parsing. Extracted facts always require confirmation.
- Capture zero to three cities during exploration; require at least one work area before local search, except a remote-only user can specify a permitted employment country and timezone without choosing a city. A remote option does not consume a city slot. Never silently add a fourth city.
- Resolve cities to stable geographic IDs, country, administrative region and timezone. Store commute modes and maximum journey time; radius is an approximation, not a journey-time calculation. A geocoder/map supplier is an explicit region-adapter dependency.
- Ask about on-site, hybrid and remote preferences, relocation willingness/date, right-to-work status, sponsorship need, language and required accommodations as practical requirements. Do not collect protected characteristics to infer suitability.
- Ask minimum salary, contract types, hours, travel, industries to include/exclude, desired autonomy/meaning/security, and willingness to take an intermediate pay cut. Separate non-negotiable limits from preferences.
- Collect available study hours and calendar windows; direct transition-spend cap; monthly payment cap; available initial funds and an optional minimum cash reserve. For cash-flow modelling collect take-home income and committed outgoings as ranges if preferred. Distinguish a payment cap from a monthly deficit that savings can cover.
- Ask tolerance for borrowing and debt limits separately. Do not interpret “low monthly cost” as permission to recommend expensive credit.
- Permit “unknown”, “skip”, and “prefer not to say”. Explain exactly which result becomes less precise. Do not default unknown salary to zero or missing skills to absence.

## Global product contract [M1, GLO-1]

The product is general and global by design. All supported regions use the same person/occupation/skill/action/plan domain model. Country adapters supply evidence and rules; they do not create separate products. Up to three chosen cities may span countries. Residence, work location, tax jurisdiction, study location, language and immigration status are distinct fields. Remote work retains an employment jurisdiction.

| Concern | Global requirement |
|---|---|
| Occupational identity | Stable internal concepts plus versioned, many-to-many links to ISCO, ESCO and national taxonomies. Preserve local titles, scripts, synonyms, provenance and unresolved mappings. A taxonomy code is not proof of licensing or equivalence. |
| Locale | Separate UI language from source language and work language. Support Unicode, right-to-left layout, local names, dates, calendars, units and accessible translations. Preserve original evidence beside translated summaries. |
| Qualifications | Country-specific recognition, regulated professions, assessment routes, vocational pathways and equivalent experience. Never treat qualification levels from different systems as interchangeable numbers. |
| Money | Native currency/units per fact; one declared comparison currency, dated FX assumptions and sensitivity for cross-border plans. Local taxes/benefits use verified adapters or explicit user-provided net amounts. Purchasing-power comparisons never substitute for actual cash obligations. |
| Work and learning | Formal employment, trades, care, public service, creative work, apprenticeships, informal experience and non-degree entry routes. Portfolio work/self-employment can be explored; unverified business revenue is not modelled as a guaranteed salary. |
| Access and privacy | Evaluate language quality, model availability, data rights, residency, retention and lawful data flows per jurisdiction. No unsupported country is redirected silently to another country's rules or a different LLM. |
| Uneven evidence | Declare coverage separately for occupation discovery, jobs, salaries, credentials, training, funding and optimisation. A country can support discovery while lacking enough verified funding data for an affordability-qualified plan. |

Use capability states **verified local support, partial/inherited evidence, user-assisted research, unavailable**. These states describe evidence and functionality, not an individual's potential. Do not say “no careers” because a local job board lacks coverage. Search public local-language sources and accept user evidence where permitted; retain an explicit research gap when those routes fail.

**M1:** Additional adapters should reuse authoritative resources. ISCO provides an international classification framework; ESCO supplies multilingual concepts for European labour markets; O*NET is a US occupational resource. Canada's NOC/OaSIS, Australia's OSCA, India's NCO, Brazil's CBO and South Africa's OFO are examples of regional anchors, not a claim that complete integrations are already available. Pin the relevant versions and validate each crosswalk. [21,22,43-49]

**M1:** Product qualification must include at least three contrasting jurisdictions, with different languages, qualification/funding systems and data richness; include a non-English setting, an emerging-market setting and low-bandwidth mobile use. These are validation requirements, not a geographic rollout plan. No universal data-coverage promise follows from a global architecture.

## Early value and progressive refinement [M0]

Aim to show a **labelled route sketch within five minutes** after a target and four practical inputs: current work/experience, weekly availability, budget and work area. It may contain generic requirement steps and unresolved costs. It is not a verified feasible route or a Pareto solution. When no suitable template exists, show a task/requirement sketch and a research status instead of fabricated providers, prices or dates.

Unsure users first receive a small, varied set of career hypotheses. Each later chapter visibly improves the existing sketch: evidence narrows skill gaps, real options replace abstract steps, and verified constraints enable a solve. There is no requirement to finish five chapters before seeing useful output. Existing privacy, budget and confirmation rules still apply.

## Navigation and continuity [M0]

The desktop shell has a narrow chapter rail, a central work surface and a contextual evidence drawer. A compact strip shows active targets, cities, the current budget and saved status. Mobile uses a chapter menu, stacked cards and a bottom evidence sheet; graphs open as focused views. Every long process can continue in the background and resume after closing the tab.

An editable “What we know” panel accompanies chat. New facts appear as proposed changes; factual confirmations and inference have distinct styling. Undo and revision history are always available. A changed constraint shows affected results before invalidating them. Users may explore a what-if workspace without overwriting the chosen plan.

## State and empty-state requirements [M0]

Provide explicit states for draft, running, partial, complete, cancelled, blocked by missing information, insufficient coverage, stale, provider unavailable and failed. A search with no hits says “No matching listings found in the sources checked”, with source coverage and filters. A failed scrape never becomes “no jobs”. A solver timeout never becomes “no feasible route”.

When there are no feasible candidates, explain the smallest verified conflicting set of requirements where a proof is available. Otherwise say which observed bottlenecks prevented a route from being found. Offer inspectable relaxations such as another intake, lower weekly load over a longer period or a broader commute; never apply them silently.

# 4 Career exploration and the structured interview

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Research basis and limits [M0]

The 2025 adult career-development scoping review covers 20 studies and highlights heterogeneous interventions and outcome measures. It supports combining reflection, tailored feedback, work information and support, while leaving important uncertainty about generalisation and long-term outcomes. [14]

A 2026 meta-analysis of online career counselling combines 14 studies with 1,721 participants and reports improvements in career-related psychological outcomes, but includes mixed designs and substantial heterogeneity. It does not establish the efficacy of an autonomous LLM coach or prove higher employment rates. We reviewed its abstract, not an inaccessible full text. [15]

Use social cognitive career theory to distinguish interests, confidence, expectations, supports and barriers; narrative prompts to understand meaningful experiences; and small experiments to test assumptions. These are design applications of established approaches, not validated diagnostic instruments. **M1:** Use the O*NET RIASEC Interest Profiler only under its applicable licence and preserve approved items/scoring when presenting a validated assessment. A paraphrased free-form conversation must not be labelled a validated RIASEC test. [14,16]

## Structured profile behind natural conversation [M0]

The schema combines five layers; the user never needs to complete a wall of fields.

| Layer | Fields | How obtained |
|---|---|---|
| Current situation | Work/study status, history, responsibilities, credentials, constraints, reason for change | CV proposals and direct questions |
| Interests and values | Enjoyed tasks, disliked tasks, preferred environment, autonomy, stability, income, social contribution, learning | Concrete examples and trade-off prompts |
| Work style and personality | User-described collaboration, structure, novelty and social preferences; optional licensed trait assessment [M1] | Explicit consent; no diagnosis or inference from writing style |
| Feasibility | Locations, work rights, financial constraints, availability, mobility, prerequisite education, supports | Short practical questions, often completed inline |
| Target hypotheses | Canonical occupation and synonyms, seniority, industry, work arrangement, essential outcomes, rationale, concerns, evidence, user confirmation | Research-backed proposals followed by user choice |

Personality is descriptive and optional. Do not use MBTI-style categorical assignment or infer aptitude, intelligence or mental illness from chat. A preference such as “quiet concentration” can inform working-environment fit; it must not exclude management or public-facing roles categorically. Interests, capability and confidence remain separate fields.

Every field has a value, epistemic status, source reference, observation date, verification state and provenance. “No preference” differs from “not yet asked”. A model's confidence score is not a psychometrically validated probability.

## Adaptive conversational policy [M0]

1. Start with one low-pressure question: “What would you most like to be different about your working life?” Accept a long narrative or a few words.
2. Extract multiple relevant facts from each reply. Produce a typed patch, validate it and show a concise reflection. Do not ask again for information already supplied.
3. Ask the next question that most changes the decision. Practical constraints and blocked requirements precede low-impact preferences. Let the user answer through chat, a short choice or a direct field edit.
4. For high uncertainty, explore two or three task-level directions before naming careers. For a sure user, confirm title ambiguity/seniority and skip personality exploration.
5. Offer optional two-minute, five-minute and deeper modes. Session length is a user preference, not a diagnostic classification.
6. Summarise a diverse set of tentative hypotheses with reasons, concerns and one disconfirming question. Show an initial six suggestions in manageable groups; permit further exploration. Only the user-selected active targets are capped at three.
7. Ask the user to confirm or reject the summary. Completion means enough information for the next decision, not filling every field.

Useful prompts include: “Tell me about a task you finished feeling satisfied”; “What was draining even when you were good at it?”; “If the pay were similar, which of these working days would you choose?”; and “What would make this option impossible for you right now?”

## Personality-informed career suggestions [M0, REC-1]

Use the user's optional personality/work-style profile as one source of hypotheses, alongside vocational interests, values, enjoyed tasks, experience, practical constraints and desired working conditions. Separate “I enjoy this”, “I believe I can do this” and “I have evidence I can do this”. An interest-fit meta-analysis finds a modest association with overall job satisfaction; it does not justify deterministic personality-to-title matching. [54]

A Meta LLM turns confirmed profile evidence into task and work-environment queries, retrieves grounded occupation candidates and explains plausible connections. For example, “You enjoy diagnosing physical problems and seeing a tangible result” should trigger research across relevant technical, maintenance, laboratory and craft contexts, subject to the person's other preferences. It should not produce a fixed personality-type lookup. Any named example must pass the same grounding process as other candidates.

**M1:** an optional validated trait or interest instrument may enrich the profile only in an appropriately licensed and validated language/version. Free-form personality descriptions remain user-editable preferences, not a clinical or psychometric diagnosis. Do not infer sensitive traits from wording, names, accent or a CV photo. Do not derive a supposedly precise occupational personality profile from stereotypes in LLM memory.

The structured `CareerSuggestion` contains a local title, canonical concept or provisional concept ID, taxonomy mappings, supporting source IDs, linked profile evidence, workday/tasks, plausible fit, potential mismatch, entry gates, evidence gaps and a low-cost way to test the hypothesis. It also identifies its discovery channel and occupation family. It never contains an invented “92% personality match”. Confirmed suggestions become `TargetRole` records only after user selection.

Show “Why this could suit you”, “What might not suit you” and “Try it before committing”. Allow **broaden**, **more practical**, **less familiar**, **exclude this kind of work**, **change my profile** and **show why this wasn't included**. A rejected title does not automatically reject its entire industry. A confident user may skip this service and enter their own titles.

A model-written “Why this could suit you” is permitted, in at most one bounded model call per slate, when it quotes only the person's confirmed answers and the grounded occupation record, each quotation verified server-side, and is validated like a search proposal: one bounded repair, then an observable invalid-output failure. It adds no readiness or affordability claim. Deterministic provenance (the confirmed answers and the occupation record that grounded the suggestion) remains underneath and is what exports cite.

LLM job-recommendation studies have found demographic bias in earlier models; those results motivate current-model tests, not a claim that the deployed model has the same measured bias. Evaluate suggestions after removing or counterfactually varying irrelevant demographic cues, while keeping legitimate work-rights and accommodation requirements fixed. [55]

## Diverse discovery beyond common careers [M0, DIV-1]

A library of common role templates is a cache accelerator, never the universe of recommendable careers. Retrieval must query the full qualified occupation indexes and current evidence, including local-language titles, specialist associations and emerging roles absent from older taxonomies. In M0, PostgreSQL English full-text search plus alias lookup over the full pinned ESCO catalogue supplies candidates; issue multiple task/interest/skill queries and rerank the combined pool. No embedding service, live Career Causeways integration or extra taxonomy API is required. Verified user-supplied titles absent from ESCO remain provisional internal concepts, not fabricated ESCO records.

LLM-generated titles are search hypotheses until corroborated by an authoritative occupational/professional source or independent employer evidence; duplicated adverts do not constitute independent support.

Build a bounded working pool, initially 60-120 distinct occupation concepts where evidence permits, from several channels:

1. Task, interest and work-environment retrieval across broad occupation taxonomies, independent of vacancy frequency.
2. Adjacent roles suggested by transferable skills and reviewed transition datasets.
3. Cross-industry roles that share meaningful tasks but have different titles or workplaces.
4. Less-exposed-to-the-user, specialist, vocational, regional and emerging occupations from credible sources.
5. User-proposed roles and “surprising but plausible” LLM hypotheses, subjected to the same grounding and feasibility checks.

Sample across occupational families and sectors before reranking; oversample under-retrieved catalogue areas. Deduplicate aliases and near-identical roles before counting diversity. “Data analyst”, “analytics analyst” and a translated synonym are not three discoveries. Keep rare-but-evidenced occupations distinct from unsupported titles. A lack of live vacancies is a demand/availability signal, not proof that an occupation does not exist.

Rank a slate for both relevance and **additional information the user gains**. A practical first slate has two close-to-current, two transferable-skill and two less-familiar but plausible directions, when qualified candidates exist. These are overlapping discovery channels, not hard psychological categories. Apply a relevance floor and respect confirmed constraints; do not fill a diversity slot with an implausible or ineligible career. When evidence is insufficient, return fewer suggestions and state why.

For a qualified pool $R$, a proposed slate objective is:

$$\max_{S\subseteq R,\ |S|\le k}\left[\sum_{r\in S}q(r,u)+\lambda\sum_{c\in\mathcal C}w_c\,\mathbf1\{S\text{ covers }c\}-\mu\sum_{\{r,r'\}\subset S}\operatorname{sim}(r,r')\right].$$

Here $q$ is an evaluated relevance score, $\mathcal C$ comprises meaningful task/family/sector/work-environment categories, and similarity penalises near duplicates. Weights are product policy subject to evaluation, not estimates of personal fulfilment. A constrained greedy reranker is acceptable without claiming optimality. Start with a soft limit of two suggestions from one occupation family in a six-item slate; relax it visibly when the user requests depth in a narrow field.

Novelty is relative to the user's familiarity, not just low population frequency. Do not reward rarity for its own sake, equate common work with bad work, or optimise for prestige. Salary, popularity and sparse AI-resilience evidence must not silently remove plausible long-tail careers. Explicit hard user filters still take precedence, with counts explaining their effect.

Measure evidence-grounded relevance, alias duplication, family/task coverage, exposure concentration, long-tail catalogue coverage, useful unfamiliar discoveries and language/region disparities. Compare against a relevance-only and a common-careers baseline on the same eligible pool. A movie-recommendation study found that LLM popularity bias need not be worse than conventional recommenders; therefore measure the actual system instead of asserting that prompting alone causes or cures bias. [56]

**M1:** Career Causeways can seed adjacent-role retrieval, but its archived 2020-2021 research data cannot establish current worldwide transition feasibility or AI resilience. Revalidate mappings, entry gates and local demand, and combine it with other channels so adjacency does not trap users in their past occupation. [53]

## Uncertainty and emotional comfort [M0]

Let the user explicitly choose “keep this practical”, “help me explore gently” or “challenge my assumptions”. Normalise uncertainty without diagnosing it. Use one question at a time, neutral language and a visible pause/resume control. Do not infer a durable “anxiety score” from messages, voice or hesitation.

If the user expresses overwhelm, acknowledge it briefly and offer a smaller next step. If they describe a health condition, ask which accommodation or constraint would help rather than requesting medical history. Clinical screening is outside scope. Maintain a separately reviewed safety flow for explicit acute distress, including current local support resources; never fabricate emergency details.

Support decision reversibility: an informational interview, a short task simulation, a job shadowing opportunity or a sample class can precede a costly commitment. These are legitimate plan actions with time and cost, and may reduce uncertainty without directly awarding a skill.

## Schema governance and conversational integrity [M0]

Pydantic AI provides typed output modes and validation, but JSON conformity does not establish factual truth. Native structured output should be used where the tested Meta endpoint supports it, followed by server-side validation. A narrowly defined tool-output mode is permitted only as an explicitly tested capability configuration. Do not silently switch to prose parsing. [3,4]

Stream natural conversation for responsiveness, but commit changes only after complete validation. Unknown fields remain nullable. The assistant may propose a target or budget, but only explicit user confirmation establishes a hard constraint. Versioned patches use optimistic concurrency and reference the supporting message IDs. Bounded repair attempts end in an observable validation failure with the previous profile preserved.

# 5 Regional labour market intelligence

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Role card [M0]

Clicking any target opens a high-level card showing: the canonical role and synonyms; what the working day involves; seniority and industry; actual geographic coverage; salary distributions; short-term hiring signal; medium/long-term outlook; essential qualifications; common entry routes; the **AI Resilience Score**, task-level technology exposure and assessment horizon; evidence quality; sample sizes; observation period; and last refresh.

Use labels **Growing, Broadly stable, Contracting, Mixed evidence, Insufficient evidence**. Never force a binary conclusion when current advertisements and longer-term projections disagree. Explain the disagreement in a sentence. A decline in occupational headcount can coexist with replacement vacancies. AI task exposure is not a probability of job elimination. [17-20]

## Evidence hierarchy [M0]

| Claim | Preferred evidence | Required qualification |
|---|---|---|
| Official pay benchmark | ONS ASHE for the UK; BLS wage data/OOH for the US; appropriate national statistics elsewhere | Occupation code, geography, period, sample reliability and pay definition |
| Advertised salary | Deduplicated employer/authorised board listings | Sample count and missing-pay fraction; distinguish base, bonus, total compensation and hourly/annual rates |
| Long-term outlook | Government projections and sector/occupation studies | Forecast vintage, geographic scope, scenario and replacement versus expansion demand |
| Current hiring | Stable-source vacancy panel over time | Source coverage and entry/exit changes; current stock is not new-posting flow |
| Requirements | Regulators, occupational taxonomies, professional bodies and recent role-specific postings | Legal requirements distinguished from common employer preferences |
| Technology change | Task-level research with an explicit methodology | Exposure, adoption and realised employment effects reported separately |

For UK pay, the 2026 ONS release includes region-by-occupation tables and reliability information. Do not relabel a regional or broad-SOC estimate as a precise city-level figure. Skills England's 2026 sector work is relevant but does not cover every occupation equally. ESCO and O*NET help normalise concepts; neither automatically establishes current local demand. [17,18,21,22]

## Research method [M1]

Resolve title to one or more occupational codes with a reviewable mapping. Query each target/region/seniority combination using synonyms and exclusions. Retrieve primary sources, extract supported claims and record contradictions. Aim for an official anchor and at least one independent current source where available. Multiple websites repeating one report count as one source.

For salary, retain the original currency, period, hours and source before normalisation. Annualise only when working hours are known or explicitly assumed. Never combine contractor day rates with employee salaries without a separate conversion assumption. Quote gross values as gross; net-income modelling uses user-entered amounts or separately versioned jurisdiction-specific calculations.

For trends, use comparable source panels and seasonally comparable periods. Define indicators such as unique new postings over a rolling 90-day interval against a prior comparable period; show methodological breaks. Where licensed historical data are absent, display “trend history not available” and build a prospective series. Repeated scraping of today's jobs cannot reconstruct past labour demand.

Small cells use a wider published geography with an explicit label, or a statistically validated partial-pooling estimate labelled as modelled. A proposed minimum of 30 deduplicated salary observations is a display safeguard, not a guarantee of representativeness. Suppress or qualify estimates where coverage and precision are inadequate even above that number.

All numeric cards link to source records. Refreshing a synthesis does not make an old underlying statistic newly observed.

## M0 taxonomy and evidence packs [M0, TAX-1]

Use **ISCO-08 as the grouping pivot**, not as the unique ID for every distinct occupation. Preserve internal concept IDs and ESCO URIs so specialist occupations in the same ISCO group remain distinct. ESCO specifies one ISCO-08 code per ESCO occupation; that does not make other taxonomies one-to-one. [60]

Maintain distinct namespaces for **UK SOC 2020**, **US SOC versions** and **O*NET-SOC**. ONS explicitly describes split mappings and supplies an ISCO-coded job-title index. Select an appropriate UK occupation code using title/tasks and retain unresolved alternatives. Do not assign a precise ASHE salary to every ESCO descendant of one ISCO group. Do not average medians or percentiles across a many-to-many mapping as if that were a valid population estimate. [61]

For Anthropic records, pin the actual O*NET-SOC version in that release and a compatible ESCO/O*NET mapping or an explicit validated version bridge. The published ESCO/O*NET crosswalk and BLS SOC-version/ISCO crosswalks are useful starting material, not lossless interchangeable joins. Mapping ambiguity is carried into the result; insufficient matches stay unscored. [62,63]

The M0 import manifest records dataset release, URL, licence/attribution, hash, native code version, import date and transformation version. Frozen ESCO/ASHE imports are refreshed manually for the beta; live job results retain their own freshness limits. Show trend as unavailable unless comparable historical observations actually exist. One snapshot cannot measure a trend.

## AI Resilience Score [M0, AIR-1]

The user-facing label is **AI Resilience Score**, with “formerly AI Safety Score” in the specification's change record. Retain the requested 0-10 scale, higher meaning more resilient, and the five-year outlook. It assesses pressure on demand for human work, including reduced staffing and entry-level hiring; it is not a probability that a person will lose a job. General employment growth and personal skill readiness remain separate.

**Lead with a range**, for example “5-8 / 10 · mixed to comparatively resilient · five-year outlook”, then show a reference score only if evidence supports one. That example is synthetic. The range is sensitivity to scenarios and mapping uncertainty, not a statistical confidence interval. Zero is not certainty of elimination; ten is not a guarantee of safety.

### Concrete M0 score recipe

1. Import a pinned ILO exposure release and pinned Anthropic observed-use data into separate native-code tables, together with the reviewed mapping pack. They are additional static data inputs beyond ESCO/ASHE, not an extra live API integration. Preserve source measures and missingness; observed use is not replacement. [20,41,60-63,67]
2. Retrieve the mapped evidence, contradictions and task context. A Meta LLM proposes an assessment record and cites supporting spans; it does not publish the score. Two named sources are not automatically independent corroboration of the same claim, nor a calibration of a five-year resilience measure.
3. An accountable reviewer records an allowed range under the versioned ordinal rubric below, or null. The decision record includes scope, assumptions, method version and reasons. M0 publishes **range only**, experimental, with inherited geography; it adds no unsupported seniority or local modifiers. The application performs the matching, publication-state checks and lower-bound filtering deterministically.
4. A record is publishable only when its mapping and supporting assessment have passed that review. No automatic conversion such as `10 - exposure`, multiplying two indices, or treating absence of Claude usage as protection. Where the evidence supports exposure only, show that fact and keep resilience unscored.
5. Pin the reviewed pack for each run and mark its date. Check for known material corrections before enabling a beta session, and invalidate affected records immediately. Scheduled monitoring and inter-rater qualification are M1; basic review, provenance, contradictions and the ability to withdraw a misleading record are M0.

This recipe intentionally does not invent a numeric scoring formula from two incompatible datasets. The beta can expose unscored roles and the functioning range filter; it cannot claim comprehensive score coverage. Static fixture scores used in tests are conspicuously synthetic and never become real role assessments.

### Evidence and methodology

Start with published occupational/task exposure research, mapped to canonical occupations with mapping quality preserved. Distinguish capability, observed adoption, whole-workflow substitution, human accountability and labour-demand evidence. ILO exposure, Anthropic observed use and Stanford employment patterns measure different things; their native quantities must remain distinguishable. None directly supplies a calibrated five-year replacement probability. [20,41,42]

Use occupation plus seniority as the default assessment unit. Industry or geography modifies it only when relevant evidence supports the distinction; otherwise inherit the wider scope explicitly. Do not generate a costly, fictitiously precise occupation-by-city-by-industry grid. Bespoke task inventories are reserved for materially different job bundles, disputed mappings and consequential high-demand assessments. Sparse-data occupations can remain unscored without being excluded from career discovery.

Remove the earlier 45/25/30 weighted ordinal formula. Replacing it with “exposure × realisation” would also need defensible quantities and calibration; it is not a validated shortcut. Use a published, versioned **ordinal rubric** with anchored judgments and an auditable decision table. Ratings are not averaged, subtracted to measure effect size, or treated as probabilities.

| Ordinal band | Interpretation | Required assessment emphasis |
|---|---|---|
| 0-2 | Very high substitution pressure | Broad role-level substitution is technically and operationally plausible, with strong supporting evidence |
| 3-4 | Elevated substitution pressure | Important human work is substitutable; deployment or remaining responsibilities still constrain whole-role reduction |
| 5-6 | Mixed or contested outlook | Material augmentation/substitution pressures and durable human responsibilities coexist or evidence conflicts |
| 7-8 | Comparatively resilient | Important contextual, physical, relational or accountable work remains difficult to replace within the horizon |
| 9-10 | Highest assessed resilience | Strong, independently supported barriers across the essential work bundle under all assessed scenarios |

These are product rubric anchors requiring expert qualification, not established empirical thresholds. An individual integer within a band requires a documented anchor; otherwise publish the band/range only. A missing observation of AI use cannot justify a high score. Physical automation coverage must be stated; an LLM-use dataset alone cannot establish resistance to robotics.

Publish only with a reliable occupation mapping, explicit technological/geographic scope, supporting evidence for the assigned band, contradictory evidence recorded and at least two independent evidence families. The LLM extracts claims and proposes mappings; reviewed rubric rules determine permitted bands. Preserve reviewer/rule version, scenarios and the reason for widening the range. If no defensible range exists, return a null assessment. Mark this feature experimental until inter-rater consistency, cross-region transfer and comprehension tests pass; outcome monitoring must not overclaim causal validation.

### Interaction and maintenance

The default filter is **Minimum AI Resilience: Any / 0-10**, applied to the **lower end of the displayed range**. **M0:** range-only lower-bound filtering. **M1:** an explicitly selected reference-score mode is possible only when a reviewed record supports such a point. Include unscored roles is on by default for exploration. Show the active basis and excluded/unscored counts; unknown never becomes zero or ten. The card explains tasks, main pressures/protections, source scope, range, dates and why a junior role may differ from a senior one.

Industry retains the categorical colour encoding. Use a numbered range badge and text for AI resilience. A company cluster shows its visible role distribution, not an average “company safety” claim. The graph, salary lens, list and exports use this one contract.

Discovery filtering does not silently constrain optimisation. **Use this limit in my plan** creates an explicit constraint with separate target/intermediate-role scope. Strict constraints exclude unscored, invalidated or out-of-horizon assessments; an accepted exception is conditional and does not count as satisfying the limit. Preserve the chosen plan's assessment version. If a pathway ends beyond the horizon, require reassessment rather than extrapolating.

**M1:** Monitor source releases/material changes at least monthly; re-assess promptly on relevant capability, deployment, regulatory or mapping evidence. Conduct a full methodology/record review at least annually. Do not recompute every number every 30 days or expire it solely at 90 days. Record source observation date, last material-evidence check, last full review and next review due separately. Known material contradictions invalidate the score pending review; a missed annual review makes it overdue and unsuitable for an unqualified strict planning decision. Stable evidence may remain useful and visibly dated in exploration.

A chosen plan and its printout include the assessment snapshot and any unresolved review flag. Cache and testing sections reference AIR-1 rather than defining different score semantics.

# 6 Web acquisition and the scraper decision

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Recommended acquisition stack [M0]

Use direct public or licensed APIs and employer feeds whenever permitted. As an M1 integration example, Greenhouse documents unauthenticated GET access to its public Job Board API; this does not itself grant unrestricted republication or create a global search index. Maintain a separate source discovery registry and rights assessment. [23]

The scraper recommendation is **Scrapling as the preferred primary retrieval and parsing framework**, conditional on the workload acceptance benchmark below. Its Python library, browser support, crawler and agent-facing MCP fit this application; the repository uses a BSD-3-Clause licence. It does not require an LLM for ordinary parsing. [34]

Scrapling is the only committed scraper. M0 calls its HTTP fetch/parse capability on bounded, policy-permitted URLs supplied by the user or discovered through Meta search. No recursive link traversal, spider, browser rendering or additional scraper vendor is implemented. A page requiring unsupported rendering/access returns an explicit limitation and the established option to paste permitted text. M1 may add qualified acquisition capabilities through a later scoped change; there is no runtime vendor switch.

## Reuse regional evidence before scraping [M1]

| Source class or adapter | Use | Boundary |
|---|---|---|
| National statistical agencies and regulators | Pay/outlook anchors, credentials and regulated entry gates | Country/occupation scope and release vintage remain explicit |
| National occupational/skills datasets | Reference tasks, duties, skills and aliases | See GLO-1; local standards are not universal competency levels |
| Adzuna, in supported and licensed markets | Job discovery and salary/vacancy endpoints | Preserve `salary_is_predicted`; predicted pay is not employer-advertised pay. API descriptions may be snippets, insufficient for a full skills matrix. [51] |
| Skills England occupational maps API | England-specific duties, KSB relationships and progression inputs | Access/rate limits and the stated logo/attribution conditions apply. Do not assume KSB statements supply proficiency anchors. [50] |
| Find an Apprenticeship Display Advert API | Relevant apprenticeship advertisements | Use the current supported version and verified subscription/access terms; scope is not worldwide. [52] |
| Career Causeways and reviewed local transition resources | Candidate transition priors and transferability hypotheses | Archived research must be remapped and checked against current regional evidence. [53] |
| Official employer ATS feeds and permitted pages | Detailed, current role requirements | Reconcile with aggregators, deduplicate and recheck closure |
| Training, professional-body and funding sources | Syllabus, recognition, offerings and eligibility | Source-specific facts and freshness; programme approval is not personal eligibility |

A provider's presence in this table does not establish an active contract, unlimited reuse rights or complete coverage. Source discovery must actively look for equivalent authoritative local-language services in each adapter. The UK examples are named adapters, not a country preference. Use a source-capability registry to record supported markets/languages, fields, historical depth, attribution, rights, rate limits, cost and observed failure modes.

For pay, track employer-stated, provider-predicted, locally modelled and unknown values separately. If a prediction flag is absent or ambiguous, do not treat a numeric value as confirmed advertised salary. Salary-history endpoints do not establish a representative panel of all employers; preserve source coverage changes.

## Qualification and cost [M1]

Qualify feeds and Scrapling on a stratified, rights-permitted benchmark spanning employer ATS pages, boards, training/funding providers, PDFs and rendered pages in the supported jurisdictions. A starting corpus of 500 URLs is an engineering target; include minority languages and rare-role sources rather than filling it with easy English pages. Measure critical-field precision/recall, closed-status detection, p50/p95 latency, drift failures and total cost.

$$ C_{record}=\frac{C_{retrieval}+C_{model}+C_{compute}+C_{proxy}+C_{operations}}{N_{correct,\ fresh,\ deduplicated}}. $$

Use at least 95% critical-field precision as an initial qualification gate, with consequential price/status errors individually investigated. Do not combine recall and extraction failure into a misleading cheap-record metric. A known unsupported source returns a coverage limitation. A later vendor comparison uses the same source classes and output contract; it is justified by actual failures or economics, not the existence of another scraper. Meta preference breaks only otherwise close choices. [5-9,34-38]

Meta search supports discovery, while structured source acquisition and refresh remain application responsibilities. This review did not establish a Meta-branded scraper that replaces Scrapling's role. [9]

## Scrapling specific engineering contract [M0]

Use the Python library directly from bounded acquisition activities; expose narrow internal tools to Pydantic AI. MCP is useful for research-agent access and adapter exploration, but the broad stock MCP server must not be exposed to public users or carry production profile secrets. The scraper remains a fetch/parse component, not the owner of career decisions. [35]

**M0:** HTTP retrieval only. **M1:** add browser rendering for qualified sources that require it. Persist source-specific selector definitions, schema versions and approved recovery metadata. Treat adaptive relocation as a candidate match: check the field label, currency/units, surrounding context, plausible bounds, cardinality and source span. Critical-field disagreement blocks publication and surfaces an extraction error. Do not let a plausible-looking adjacent number become the salary. Adaptive state is isolated by source/template version and cannot be trained by unrelated tenants. [36]

Scrapling's published benchmark uses synthetic HTML and parser timing; its code uses CPU process time. These measurements do not establish browser success rates, network latency, completeness or lower production cost than Firecrawl/Crawl4AI. Include DOM-change regression fixtures and false-match rates in our benchmark. [37]

**M0:** no crawler or independent crawl scheduler. DBOS owns bounded fetch retries. Keep a small checked-in source manifest rather than a registry product: permitted domains/purpose, robots/access decisions, rate limit, retained fields and attribution. Policy-denied requests create explicit SourceAttempt records. Arbitrary user URLs pass SSRF and redirect checks; a user supplying a URL does not override source permissions. **M1:** any crawler must preserve these boundaries and have one retry owner. [38]

A self-hosted framework has no hosted per-page vendor charge under its open-source licence, but compute, storage, traffic, permitted proxies and engineering still cost money. Pin a tested release and dependencies rather than GitHub main; review release maturity and upstream breaking changes. No full production benchmark has been run for this specification.

## Retrieval pipeline and security boundary [M0]

Discovery produces candidate URLs, not trusted claims. Each URL passes scheme, host, DNS and redirect validation before retrieval. Block private, loopback, link-local and cloud-metadata addresses; recheck after redirects and DNS resolution. Bound response size, depth, time and content types. M0 accepts pasted text and supported HTML only; document uploads/parsing are M1 and require isolated processes with no network access.

Fetch using the fixed M0 feed or Scrapling HTTP adapter appropriate to the source. Parse JSON-LD JobPosting, official JSON and stable selectors first. Use model extraction only for remaining ambiguity. Store allowed evidence snippets and content fingerprints with source/field pointers; retain full snapshots only where permitted. Quarantine malformed, conflicting or suspicious records for review.

External pages are untrusted data. Embedded instructions cannot modify the interview, access keys, request private files or expand tool permissions. Acquisition workers receive no user profile or model key. The model extracts through a narrow schema; deterministic code approves the resulting record. No page-supplied code executes in the application origin.

Respect contractual access rules, robots policies, rate limits and copyright/database restrictions. Do not bypass sign-in, paywalls or access controls. A public page is not evidence of an unlimited right to collect and redistribute it. Use licensed partnerships when required and provide manual URL/text import where automated access is unavailable. Avoid claiming universal LinkedIn/Indeed coverage unless supported by permitted integrations.

# 7 Job discovery and the living opportunity map

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Search, canonicalisation and matching [M0]

Run bounded searches across target synonyms, seniority, industry and work areas. Fetch incrementally with cancellation and clear cost limits. Maintain canonical employer IDs, employer domain aliases, occupation IDs, posting source IDs and original URLs. Distinguish staffing agencies from the hiring employer; an undisclosed employer remains undisclosed.

Deduplicate syndicated postings using source IDs, canonical application URL, employer, title, location and normalised description fingerprints. Preserve all provenance links. Keep multiple city appearances as views of one job when appropriate. A multi-location job may appear in more than one city cluster but counts once in totals. Do not collapse materially different levels, contracts or locations.

Hard eligibility and preference checks precede ranking. Score task/skill relevance, target-level match, explicit preferences, salary fit and practical accessibility with inspectable contributions. Missing salary is not the lowest salary; display it separately and allow a strict “salary confirmed” filter. Unknown work-rights compatibility is “needs checking”.

Do not label a relevance score “probability of getting hired”. Before skills assessment, use the label “matches your preferences”. After assessment, separately expose evidence-backed requirement coverage and unresolved conditions. Users can favourite, exclude, report errors and compare listings. No auto-application occurs.

## Dendrite graph semantics [M0, VIS-1]

Each of up to three work areas is a stable region anchor. Company nodes cluster within it; branches terminate in individual jobs. Industry determines node/branch colour; role family and work mode use shape, icon and labels. Remote roles form a distinct area whose labels show employment jurisdiction and timezone constraints. Graph distance is a layout device, not geographic distance or hiring probability. This grouping is a meaningful hierarchy, but the graph is not the only comparison surface.

**M0:** a static SVG hierarchy with city anchors, company groups, job nodes, industry labels/colours, basic expand/select, source counts, favourites and the same filters as the list. Include numeric salary and AI-range filters. No semantic zoom, mini-map, halo or animated layout is required at this gate. Commute feasibility is user-confirmed; it is not computed from graph distance.

**M1:** Use a constrained organic layout: stable city/company anchors, collision avoidance, softly curved branches and gradual expansion. Preserve node positions across filtering, pagination and refresh wherever possible. New nodes unfold from their parent; avoid constant force motion or a spinning three-dimensional cloud. Companies spanning industries receive an explicit primary classification and secondary tags rather than misleading colour mixing.

**M1:** the best five eligible, sufficiently evidenced preference matches may emit a slow, pausable halo. Before skills assessment the accompanying marker says “Matches your preferences”; after assessment use “Strong requirement coverage” only when evidence warrants it. The same wording is available without animation. Pulse intensity does not imply statistical certainty. Hover/focus reveals title, location, pay status and match reasons. Click pins an accessible side card; double activation expands a company. Search, keyboard traversal, breadcrumbs, fit-to-selection, a mini-map and undo protect orientation.

Filters include target role, city/remote, industry, employer, salary, **minimum AI Resilience Score**, seniority, contract, working hours, sponsorship, commute, posting age, skill readiness, source quality and favourite status. AI filtering defaults to the lower range bound, with an explicitly selected reference-point mode and inclusion of unscored roles governed by AIR-1. Unavailable values remain selectable as “not specified”. Display result count, deduplication count and coverage status outside the canvas.

Add a linked **Pay and location** lens: area rows, advertised salary ranges on a common declared pay basis, explicit predicted-pay styling and a separate unknown-pay lane. Keep currencies/contract bases separate unless a labelled conversion is selected. Hover/focus highlights all jobs from the same company. Salary, location and AI filters stay synchronised with the graph and list.

The default view surfaces a few dozen relevant nodes, not thousands at once. Semantic zoom reveals detail; aggregate large branches by company or role. Offer a list/table toggle with identical filtering, ranking, selection and comparison. Mobile defaults to the list with an optional graph overview.

## User examples versus discovered corpus [M0]

**M0:** the user can supply zero to three permitted HTML URLs or pasted full-text examples per active target. **M1:** add PDF/file attachments. Mark these as strong statements of interest, not representative samples of the whole occupation. The automated corpus is broader and must not inherit the three-posting cap. Expired exemplars can remain as historical requirement examples, labelled accordingly, but never appear as live vacancies.

# 8 Systematic skills matrices

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## M0 provisional matrix [M0, MAP-1]

Import ESCO essential/optional skill relationships, enrich with up to three user-supplied full-text exemplars per target, and use deduplicated Adzuna titles/snippets only as a weak local-language signal. Show **Provisional - no specialist review**, source versions, actual full-text/snippet counts and the date. An ESCO essential relationship is a seed, not a statutory rule or a proficiency level. Missing terms in a snippet are not evidence of absence; keyword prevalence is labelled snippet prevalence and cannot establish requirement frequency. No full-description employer sample is claimed. [60]

Propose task-specific required levels and distinguish essential, preferred, disputed and unknown. The user can edit planning preferences at the checkpoint. Preserve original source claims, actor, reason and old/new matrix version. Changing essential rows changes the target definition and invalidates previous ranks; it is not evidence that the same target became cheaper.

**Protected gates cannot be toggled away.** Legal right to practise, credential recognition and confirmed admission/eligibility requirements remain separately typed gates. A user can challenge the source or define a different target, but the system cannot declare a regulated role attainable merely by demoting its registration row. Unverified gates remain unresolved. Employer-specific non-statutory requirements can be relaxed only with an explicit warning that the revised plan may not satisfy that posting.

**M1:** The protocol below adds the full-posting sample and specialist publication process. M0 matrices must not inherit that process's reviewed status.

## Reproducible research protocol [M1]

Seed matrices from the most applicable official occupational standards and skill datasets under GLO-1, then use current postings to identify local/seniority drift. An England KSB standard is useful for an English occupation, not a substitute for a Brazilian, Indian or South African entry pathway. Standards may omit proficiency anchors and emerging tasks. Preserve expert review for consequential gaps and disputed mappings. Common-role templates accelerate research; a missing template must trigger supported on-demand research, never make a career unrecommendable. [21,22,45-50]

1. Resolve target occupation, level, industry and jurisdiction. Ask if a title maps to incompatible occupations.
2. Start with a versioned reference template anchored to the applicable native taxonomy/standards, with ESCO/O*NET used where relevant, and regulatory requirements. Record crosswalk uncertainty rather than treating similar labels as identical. [21,22]
3. Gather a recent, deduplicated employer-diverse sample. A proposed target is 30 to 100 relevant postings per role/region, spanning at least ten employers where available; sparse markets carry lower evidence coverage rather than invented data.
4. Extract responsibilities and requirements with source spans. Label explicit essential, explicit preferred, inferred responsibility and legal/credential requirement separately. Advertising frequency does not establish that a skill is essential.
5. Normalise synonyms; preserve tool-specific versus conceptual skills. Cap each employer's influence to prevent one large advertiser determining the role template.
6. Reconcile template, local data and chosen exemplars. Preserve disagreements: a specific vacancy may require a credential uncommon in the broader role.
7. Assign task-specific proficiency anchors and evidence methods. A domain specialist must approve published reference templates and regulated-role requirements. A model-generated novel template remains provisional.
8. Publish a versioned matrix with dates, sources, sample coverage, reviewer status and change history. A material revision invalidates affected gap analyses and plans without silently rewriting them.

## Matrix contract [M0]

Each row contains a canonical skill or credential ID; observable task; required proficiency; requirement type; importance; prevalence with denominator; prerequisites; acceptable proof; source spans; uncertainty; jurisdiction; and a role-specific rubric. Credentials, supervised experience and right-to-practise gates are distinct from learnable skills.

Use ordered proficiency levels with explicit behaviour: **0 no evidence of performance; 1 performs with guidance; 2 independently handles routine tasks; 3 handles complex/non-routine tasks; 4 designs or leads and can justify trade-offs**. “Unknown” is separate from level 0. These are proposed rubric levels, not equal-interval measurements. Do not add ordinal scores or turn six months in a job automatically into one level.

Example for data analysis: “Independently join two tables, explain how missing keys change row counts and check the result” is more useful than “SQL: intermediate”. Evidence for stakeholder communication might be a structured account of resolving a disagreement, with a document or work sample optional.

## Reference library [M1]

Maintain reusable families for administration, customer support, sales, bookkeeping/accounting, marketing, project coordination, product roles, software development, testing, IT support, data analysis, data engineering, design, logistics, skilled trades and health/care support. Families contain levels and sector variants; they are not single universal matrices.

Each template has an owner, semantic version, validation status, applicable regions, source licence, last review, next review and a deprecation route. Avoid claiming regulated qualification pathways are complete without jurisdiction-specific review. Unsupported roles remain explorable but cannot receive a falsely definitive regulated-career plan.

# 9 Honest and pragmatic capability assessment

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

The goal is accurate evidence, not extracting a confession. Self-report can reflect uncertainty, memory, inflated confidence or unjustified self-doubt. There is no credible conversational lie detector. Do not score honesty from response speed, vocabulary, facial expression, accent or sentiment.

Use behaviourally anchored prompts and consistent evaluation rubrics, borrowing structured-interview principles while recognising that an adaptive coaching conversation is not a validated selection interview. The OPM material supports asking about concrete past behaviour and using defined rating standards; it does not validate this app's automated assessor. [32]

## Interview pattern [M0]

- Explain that gaps help tailor the plan, are private and do not reduce a person's worth. Let the user see the rubric before answering.
- Ask for the most recent relevant example, what the person personally did, what help/tools they used, and what outcome they checked. Accept transferable evidence from paid work, study, volunteering and caring responsibilities.
- Distinguish “I have done it independently”, “I did it with help”, “I understand it but have not tried”, “I have not learned this” and “I am unsure”. Use the same neutral tone for each.
- Ask “Which part would you need help with?” and invite correction. Do not lead users toward the level that would make a preferred route look feasible.
- Offer optional short work samples or artifact review for consequential uncertainty. Tell the user what will be evaluated; allow an accessible alternative and do not require employer-confidential work.
- Record recency, complexity, independence, permitted tool use and context. AI-assisted work is legitimate when consistent with the target's real tasks, but must not be misrepresented as unaided competence.
- Show the proposed capability conclusion, evidence and uncertainty for confirmation. Conflicting evidence triggers a clarification, not an accusation.

## Adaptive question budget [M0]

Construct one combined skill graph across the active roles and reuse shared answers. Ask about hard gates first. Then prioritise skill questions using a decision-impact heuristic:

$$ Priority(s)=\frac{Importance(s)\,Uncertainty(s)\,RouteImpact(s)}{EstimatedBurden(s)}. $$

The factors are operational priorities, not psychometric quantities or a formally estimated value of information. Where simulation can identify whether an answer changes the feasible routes, use that sensitivity directly.

Start with approximately 8 to 12 high-value prompts across all roles; propose further questions only when a consequential uncertainty remains. Stop when all gates are known or marked unresolved and roughly 80% of weighted high-priority requirements have usable evidence, or when the user chooses to stop. These defaults require usability validation. The interface reports coverage and unresolved assumptions, not “80% employable”.

Store separate self-assessed level, demonstrated level and evidence confidence. An unsupported claim remains self-reported, not false. A deliberately conservative plan can be compared with a plan conditional on passing a diagnostic assessment. New evidence can shorten the path; the system should recognise this as progress.

# 10 Gap analysis and discovery of real options

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Abstract requirements before products [M0]

Compare each target's requirements against current evidence. Classify gaps as **learn, demonstrate, credential, experience, eligibility, information or preference conflict**. Do not prescribe a course for an evidence gap that a small assessment could close, or for a work-rights issue that education cannot solve.

Produce a plain-language abstract plan: “Demonstrate independent SQL analysis”; “Obtain the required licence”; “Gain supervised responsibility for X”; “Verify whether the employer accepts equivalent experience”. List prerequisite relationships and distinguish mandatory gates from desirable improvements. Include an immediate-application route when present evidence already supports it; people do not need to satisfy every preferred criterion to apply.

## Concrete option types [M0]

Search for university/college programmes, accredited qualifications, short courses, apprenticeships, funded bootcamps, supervised practice, employer-supported study, internal rotations, volunteering, project work, mentorship, assessment-only routes and intermediate jobs. Add “remain in the current job while studying” and “apply now while building evidence” explicitly, where permitted by constraints.

Training discovery must check actual syllabus/outcomes against the skill gap. A title match is insufficient. Capture provider/accreditor, recognition, location, remote eligibility, delivery mode, prerequisites, application deadline, next confirmed intake, duration, weekly timetable, attendance requirements, assessment, credential, tuition, extras, refund rules and evidence of quality. A provider's employment-outcome marketing is a separate unverified claim unless methodology and denominators are available.

Intermediate-job templates describe tasks, entry requirements, plausible transferable experience, expected supervision and regional availability. Live postings instantiate present opportunities. If the job is needed in the future, the plan specifies a role class and a search/review gate, not a named vacancy presumed to remain open.

One apprenticeship can provide wages, training and a credential within a linked composite activity. Do not double-count its time, costs or learning. Likewise, two overlapping courses cannot both award the same mastered competency twice.

## Funding and finance discovery [M0]

**M0:** discover grants, employer support and loan information from permitted pages; do not implement three automatic funding-eligibility engines. Seed official discovery for Free courses for jobs, Advanced Learner Loans and Skills Bootcamps, then verify the actual course/provider/start-date conditions. The source-test minimum of three funding pages is not an exhaustive ruleset. In particular, 2027 LLE interactions vary with course and provider; a blanket date-only replacement rule is unsafe. [24,25,65,66]

Numeric M0 routes use confirmed non-repayable support or explicitly conditional award scenarios. They do not choose new borrowing products. Existing debt is a fixed obligation in the ledger; loan options remain information to verify. M1 adds qualified finance-instrument optimisation. Never infer that an unconfirmed grant or advertised apprenticeship will pay the user's bills.



Find grants, scholarships, employer sponsorship, publicly funded training, apprenticeship funding, bursaries and loans. Model them as different instruments. Record the authoritative scheme, jurisdiction, effective dates, deadlines, residency and age rules, income/qualification conditions, eligible providers, caps, funding availability, disbursement timing, award status, stacking/exclusivity restrictions, repayment terms and any obligation to stay with an employer.

Examples for an England adapter include Free Courses for Jobs, Advanced Learner Loans and apprenticeship routes. Their public pages demonstrate why country and programme eligibility matter: other UK nations have different arrangements, and loans are not grants. No scheme amount or income threshold should be hard-coded from this document into a future production system. [24-26]

Eligibility has four statuses: **confirmed, potentially eligible, ineligible, insufficient information**. Potential funding does not reduce the guaranteed-cost scenario. A funded scenario can be shown alongside the unfunded case, with a blocking verification action. Never assume an eligible person will win a competitive award or that two schemes can be stacked.

Offer grants and employer-supported options before debt. Show total charges, interest assumptions, repayment profile and outstanding liability. Do not apply for finance, assess creditworthiness or make regulated credit recommendations as part of this product. Any later financing marketplace requires a separate jurisdiction-specific regulatory assessment.

## Course-to-requirement outcome contract [M0, OUT-1]

The **Capability assessment module** owns outcome semantics/rubrics; the Opportunity catalogue stores the records, and the review checkpoint owns acceptance of modelling assumptions. The LLM proposes matches between syllabus/assessment evidence and the target matrix. This is among the most error-prone inputs in the system: unsupported outcomes directly falsify readiness time and cost.

Each `PlanAction.outcomes` record has `skill_id`, nullable `level_on_completion`, `evidence_kind`, categorical `confidence`, `source_span`, `rubric_version`, `claim_state`, `review_state` and reviewer/edit provenance. Confidence is `unsupported`, `provisional` or `corroborated`, not an LLM-generated probability. A span includes source ID/hash, offsets or a stable selector, retrieval date and the exact supporting extract within permitted retention limits.

Extract at row level: match the observable task, distinguish mentions/teaching from practice and assessed demonstration, and check whether the assessment supports the proposed behaviour anchor. A syllabus saying “introduction to SQL” does not establish independent level-2 performance. Use null when the level or assessment is unsupported. The user can correct a mapping, but a user override is recorded as an assumption and never masquerades as a provider claim or expert validation.

At review, show **this option is expected to address these rows**, assessment evidence, uncertain outcomes and omitted gaps. An accepted provisional mapping can support a clearly conditional route scenario; it cannot support an unqualified guaranteed-readiness claim. Missing critical outcome levels leave a partial sketch or exclude the action from a numeric readiness solve. Actual skill evidence changes only after an assessed completion event and evidence review, not on enrolment or course completion alone.

Credentials and supervised experience use separate outcome types with issuing body, jurisdiction and verification requirements. Never manufacture a licence or substitute accumulated course levels for a statutory gate. Work-based actions also need task/evidence mappings; wages alone do not produce experience credit.

## Readiness and the apply-now case [M0, RDY-1]

For a fixed target/matrix version, readiness requires every essential skill row at its required evidenced level **and** all credential, experience and eligibility gates satisfied. Unknown does not pass. A future planned outcome counts only in a conditional scenario after its completion gate; the current profile remains unchanged.

$$R_g(z)=\left[\bigwedge_{i\in E_g}\operatorname{evidencedLevel}_i(z)\ge r_i\right]\land\left[\bigwedge_{j\in G_g}\operatorname{satisfied}_j(z)\right].$$

If this is already true at the checkpoint, lead with **“You meet the modelled requirements - review current postings and apply.”** Show evidence recency, provisional matrix status and any employer-specific checks. Do not force training or render a degenerate frontier as the main result. Optional development remains a separate goal. “Apply now” is not a hiring guarantee.

## Option review checkpoint [M0]

Before optimisation, present a concise catalogue grouped by the gap each option addresses. Let the user pin, exclude or correct an option; prioritise keeping employment, avoiding borrowing or reducing weekly load; and request another provider. A pinned option is a planning preference, not an enrolment.

Display all mandatory constraints, unresolved critical fields and funding assumptions. Missing tuition, entry requirements or timetable can make an option provisional. Keep it available for exploration, but exclude it from an unqualified “affordable and feasible” recommendation until checked. If research is incomplete, produce a partial plan with labelled holes rather than replacing real options with invented courses.

# 11 Cache, freshness and evidence lifecycle

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

**M0:** keep derived research and cache entries inside their workspace, in PostgreSQL, with user-key billing and ownership checks. Keyless fetchers return permitted text to the user-scoped extraction workflow. Only immutable public taxonomy/statistics/evidence packs, including the option pack below, are common read-only inputs; user research is not reused for other testers. Refresh on access/manual action and enforce TTL/status checks. **M1:** introduce separately funded shared public-data caching and scheduled refresh.

**M0 option pack:** a reviewed, versioned, dated option pack covering the qualification personas' targets is an immutable public evidence pack and a permitted common read-only input. Its records use the section 18 shapes (LearningOption and Offering, FundingInstrument, SkillRequirement rows and `PlanAction.outcomes`), each with its SourceClaims, rights status, `review_state` and dates. Every surface that uses the pack shows its date and each record's review state; a pack record never fills a live field and is never shown as current; synthetic data stays labelled synthetic. Live research writes to the same catalogue contract, inside its own workspace, with `review_state: proposed`; a proposed record is explorable but excluded from an unqualified recommendation until reviewed, as at the option review checkpoint (section 10). The pack is not a shared cross-tenant cache, which remains M1.

Cache shared public facts separately from personal assessments and rankings at M1. Keys include canonical entity, actual data geography, occupational level, language, provider, source version, policy/eligibility context and extraction schema version. A shared funding-scheme cache contains rules, never a conclusion about a particular user's eligibility.

**M1 service refresh policy:** M0 enforces applicable maximum-age and invalidation rules on access, without a scheduled refresh service.

| Data | Proposed refresh interval | Maximum unverified age for normal use | Additional invalidation |
|---|---|---|---|
| Job search results | 2-6 hours for active searches | 24 hours before “currently available” treatment | Provider event, explicit closure, deadline |
| Individual live job | 6-24 hours by source | 24 hours; then label awaiting recheck | Check again before application/deep link |
| Course syllabus and provider profile | 30 days | 90 days, visibly dated | Content hash change or provider notice |
| Course fee, next intake, seats, deadline | 24-72 hours while being considered | 7 days; shorter near closing | Recheck on path selection and before enrolment |
| Funding rules | 7 days | 30 days only with a stale warning | Effective-date change; recheck before reliance |
| Funding availability/deadline | 24 hours | 48 hours while active | Scheme closure or exhausted allocation |
| Official salary/projection dataset | On publisher release; weekly release check | Valid for its stated vintage, never relabelled current-year | Superseding release or correction |
| Local advertised-pay/hiring aggregates | 7 days | 30 days with visible period | Source coverage change or taxonomy revision |
| AI resilience assessment | Event-driven; monthly evidence monitoring; annual full review | Use AIR-1 validity/overdue rules | Material evidence, taxonomy, regulation or methodology change |
| Role template | 90-day review | 180 days for unchanged non-regulated content | Regulatory change or material requirements drift |
| Generated illustrations [M1] | 180 days or indefinitely if style still valid | No factual freshness claim | Style/model/rights revision |

These are starting policies, not universal truths. Provider restrictions can shorten retention; expiry dates override TTL. Study descriptions therefore have a much longer cache lifetime than jobs, while study prices and intakes receive their own short-lived records.

Use stale-while-revalidate only where the stale label is visible and consequence permits. Last attempt, last successful fetch, source publication date, valid-from and valid-until are separate timestamps. A failed refresh never extends freshness. Deduplicate concurrent refresh requests; back off on errors; monitor high-impact record changes.

Each computed object stores its dependency versions. A changed course price marks dependent alternatives stale; a closed job changes its opportunity status; a revised skill requirement flags affected routes. The chosen plan remains an immutable version until the user reviews a proposed update. At M1, shared-cache refresh is paid for by product service credentials, never an arbitrary user's key.

# 12 Mathematical optimisation specification

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## The object being optimised [M0]

A route is a **time-indexed, resource-constrained plan**, potentially containing parallel activities and conditional employment transitions. It is not simply a shortest path through job titles. A person can work and study concurrently, but only within their real timetable, prerequisites, cash flow and workload limits.

Define a separate feasible set for each target role, seniority and target-quality specification. Comparing a quick route into one occupation with a longer route into a different occupation on time/cost alone does not establish which career is better. Cross-career comparison must retain target identity, preference fit and job-quality differences.

**M0:** one monthly decision grid, at most 24 months, with exact known dates retained as source data. Starts are selected from at most two reviewed, explicit offerings per action; M0 does not generate every possible day or optimise arbitrary continuous start dates. One target solve selects at most six actions from at most 24 concepts, with at most one bridge-role transition. Current commitments and completed prerequisites are part of the initial state, not hidden free actions. These bounds are disclosed in every result.

**M1:** longer horizons and finer scheduling require a new model version and qualification. A model bound or conservative monthly rejection is not evidence that a real transition is impossible.

Let $A$ be the finite researched action catalogue; $S$ skills; $K$ credentials; $G$ targets; and $\Omega$ a declared scenario set. Each action $a$ has entry predicates, possible start dates, duration, workload, payment schedule, learning/evidence outcomes and a completion condition. Include information-gathering, application and waiting actions so time is not free.

The state at time $t$ is:

$$ z_t=(q_t,k_t,e_t,b_t,d_t,\ell_t,u_t), $$

where $q_t$ is capability evidence, $k_t$ recognised credentials, $e_t$ employment/experience state, $b_t$ cash, $d_t$ debt obligations, $\ell_t$ location and $u_t$ unresolved conditions. A valid transition satisfies:

$$ z_{t+1}=F(z_t,a_t,\omega),\qquad a_t\in\mathcal A(z_t,t). $$

For overlapping actions, $a_t$ denotes the active action set and completion events. The transition function is deterministic for a fixed input snapshot and scenario. LLMs propose extracted facts; they do not execute $F$, approve feasibility or invent numerical transition probabilities.

## Monthly decision contract [M0, TIME-1]

A month is a named calendar month in the work area's timezone. Keep actual start, finish, application and payment dates on cards and exports. Reserve every month touched by a dated activity; a prerequisite becomes available only at the following month boundary after completion. Do not snap an actual intake earlier or shorten a course by rounding its duration down. Display both coarse model months and known actual dates.

If an application is needed, its action must complete in a month strictly before the deadline month, unless an already completed application/admission is verified in the initial state. This deliberately excludes some viable same-month transitions; say **“not resolved by this monthly model”**, not “ineligible”. A source deadline still cannot be ignored after the date passes.

**Workload:** monthly averaging is not enough. For each active month, reserve each action's maximum weekly load across that month and compare their sum with the user's minimum weekly availability in that month. This is a conservative envelope, evaluated once per month; there are no weekly start-decision variables. Include employment, study, commute and fixed care commitments consistently. If only total course hours are known, the envelope is unknown until a timetable assumption is confirmed. Simultaneous sessions known to conflict fail separately. M1 can recover viable schedules lost to this coarse envelope.

$$\sum_{a\text{ active in }m}\bar h_{am}\le\underline H_m.$$

A naive sum of monthly hours can pass two 20-hour courses concentrated in the same week even when only 20 hours are available in that week. Merely multiplying a weekly allowance by four does not solve that problem.

**Liquidity:** a month-end balance does not establish ability to pay on the first day. M0 uses conservative prefunding: every month's outflows must be covered by opening cash plus receipts proven available before those outflows. Other receipts become available for the following month's opening balance. Do not borrow against an unaccepted job offer or an unconfirmed grant.

$$ B_m^{open}+I_m^{early}-O_m\ge B_{min}, $$
$$ B_{m+1}^{open}=B_m^{open}+I_m^{early}+I_m^{later}-O_m. $$

Here $O_m$ includes living costs, transition payments and debt service. If a within-month sequence cannot be represented by this rule, flag the conservative rejection for review; do not claim the person cannot afford any real schedule. For example, 100 opening cash, a 200 fee on day one and 300 pay on day 28 has a positive month-end balance but fails prefunding.

The financial comparison horizon is common to all routes and covers the entire bounded planning horizon used in that comparison. Income after readiness follows a stated continuation scenario; delaying costs or earnings loss beyond the comparison window must not manufacture an advantage. M0 uses nominal integer GBP minor units and user-confirmed net incomes; it does not infer tax or benefits from gross advertised pay.

## Decision variables and prerequisites [M0]

Use selection $x_a\in\{0,1\}$, start date $s_a$, finish date $f_a$, and funding/route choices. In M0 each reviewed offering has a fixed active-month mask, prerequisite set, cost ledger and workload envelope. Selection chooses those records; it does not invoke an interval solver. Entry predicates can include any-of/all-of credentials, proficiency thresholds, experience types, employment offers and location eligibility.

For a selected precedence relation $a\rightarrow b$:

$$ f_a\le s_b. $$

A learning action is not a guaranteed additive proficiency increment. Use threshold-based outcomes tied to an assessed completion event, with an uncertainty flag and a verification milestone. Two beginner courses do not sum to expert proficiency. Experience accumulates only from relevant tasks, at an appropriate responsibility level, after the employment gate has been satisfied.

Model acquisition of an intermediate job as a conditional event: application/search effort, an uncertain wait, then an offer/acceptance gate. The plan cannot spend assumed wages before that gate. Current jobs the user intends to retain are included as current commitments; an intended resignation date is an explicit decision, never an automatic side effect.

## Route families and schedule identity [M0, ROU-1]

Define a `RouteFamily` from a canonical action/prerequisite graph, learning/provider choices, delivery mode, relevant job-role sequence and material financing/conditional gates. A part-time versus full-time qualification or a different substantive bridge role is a different family. A later intake for the same sequence is normally a schedule variant. Preserve precedence and parallelism; an unordered action set is insufficient identity.

A family can have several efficient schedules: dates can change fees, funding, work income, liquidity and available concurrency. Never assume one universally best schedule or fixed cost per structure. Keep meaningful schedules and group them under a family card, with dates as expandable variants.

Compute Pareto layers over the declared feasible schedule set. The overview shows distinct families first and suppresses repeat visual cards, not underlying evidence. A family's best displayed rank is the lowest rank among its retained variants; label it as such. A layer may contain no new family after deduplication. Do not invent additional grey families or relabel a schedule's mathematical rank to fill a visual quota.

## Objective definitions [M0, FIN-1]

The default comparison is elapsed time to the target's **modelled application-readiness milestone** and **economic transition cost relative to a confirmed baseline**, measured over a common financial horizon $H$. Readiness includes required evidence, credentials, experience and waits; it does not guarantee employment. Projected time to a target job remains a separate conditional result.

Let $C^{direct}(p,\omega)$ be total incremental transition expenditure: tuition, assessment, materials, necessary equipment, additional travel/childcare, relocation and financing charges, less confirmed applicable non-repayable support in scenario $\omega$. Include contractual liabilities incurred by the plan even if their payments extend past $H$, with timing disclosed. Loan principal is a liquidity source, not a discount or an additional copy of tuition cost.

Let $Y^0_m(\omega)$ be baseline take-home income and $Y^p_m(\omega)$ income under the route. The baseline may be staying in the current role, continuing a job search or another user-confirmed counterfactual; “staying put” is not appropriate for everyone. Then:

$$ C_H^{econ}(p,\omega)=C^{direct}(p,\omega)+\sum_{m=1}^{H}\left[Y^0_m(\omega)-Y^p_m(\omega)\right]. $$

$$\min_{p\in\mathcal P_g}\bigl(T_g(p,\omega_0),C_H^{econ}(p,\omega_0)\bigr).$$

Use the same start, horizon, currency, baseline and scenario definitions for all routes in a comparison panel. Income after readiness requires an explicit continuation/job-search scenario. Do not infer immediate target employment or use a different earnings window ending at each route's own completion date. The formula counts lost income and bridge/apprentice/target wages once, through the income difference; do not subtract those wages a second time.

The base scenario $\omega_0$ must treat offers consistently: if an intermediate offer at month four contributes experience to readiness, its modelled earnings start only at that gate. A delayed/no-offer scenario changes both time and income. Label unaccepted offers and possible funding as conditions, never guaranteed receipts. Keep nominal amounts by default; any inflation/discounting mode must state its common assumptions.

**Example in local currency units:** with a 12-month comparison horizon and baseline net pay of 2,000/month, six months out of work plus six months at baseline pay loses 12,000. If that route costs 3,000 directly, economic cost is 15,000. A 12-month part-time route retaining baseline pay and costing 5,000 has economic cost 5,000. They trade time against economic cost; the short route should not be described as universally cheaper merely because its fees are lower.

Always show direct expenditure, income change, peak payments, cash reserve and debt separately. Economic cost may be negative relative to the baseline; the UI must handle that without treating future income as cash available today. Direct-spend and monthly-payment caps remain hard affordability constraints. An economic-cost cap is a distinct optional preference. Negative economic cost does not permit fee-churning loops or artificial job switches.

When income/baseline assumptions are missing, show the unresolved economic comparison. An explicit **Compare direct spending only** mode uses $C^{direct}$ as the second objective, with that wording on charts and dominance explanations. Do not switch silently. Both modes are valid questions; only the economic mode addresses lost earnings. $C$ below denotes the selected, recorded cost definition.

Use favourable/base/adverse scenarios without probabilities unless empirically calibrated. Robust optimisation may minimise worst-case $T$ and $C$ over the same declared set. Worst-case-vector dominance is not the same as dominance in every paired scenario. No invented percentile labels.

## Hard feasibility constraints [M0]

All returned routes must pass the following checks under their stated scenario assumptions:

- Prerequisites, legal/regulatory gates, recognition of credentials, residence/work permissions and programme entry requirements.
- Confirmed intake windows, application dates, travel/location consistency and a finite planning horizon.
- A chosen weekly availability ceiling, including work, study, commute and user-defined care/rest commitments; no double-counted time.
- Total direct transition-spend cap and monthly payment cap; an optional economic-cost cap is separate.
- Minimum cash reserve, maximum permissible drawdown, borrowing consent, debt limits and financing compatibility.
- Minimum target salary/work-quality preferences as target filters or scenario constraints, with uncertainty about actual offers kept visible.
- Funding exclusivity, eligible-cost caps, disbursement delays and conditions; uncertain awards handled as contingent cases.
- Explicitly enabled AI Resilience Score thresholds, with separate target/intermediate-role scope, selected scenario semantics, assessment horizon and missing-score policy.
- No redundant credentials, repeated fee-churning actions, negative-cost loops or repeated employment switches solely to exploit a model artefact.

Apply the TIME-1 monthly workload envelope and prefunding condition to every candidate. Actual dates remain evidence and validation inputs, not a second set of scheduling decisions.

For monthly liquid balance, use a separate ledger:

$$ B_m=B_{m-1}+Y_m+G_m+D_m-L_m-P_m-R_m. $$

Here $Y_m$ is take-home income available in the stated scenario; $G_m$ cash grants; $D_m$ loan draws; $L_m$ committed living outgoings; $P_m$ direct transition payments; and $R_m$ loan repayments. Third-party payments made directly to a provider are represented consistently on both sides or excluded from both; never count them twice. Track the debt balance separately, including interest accrual and principal repayment.

$$ B_m\ge B_{min},\qquad P_m+R_m\le M_m,\qquad C^{direct}(p)\le C^{direct}_{max}. $$

$M_m$ is the user's monthly payment cap. If the user instead specifies an incremental deficit cap, use a separately named constraint; do not conflate the two. The TIME-1 prefunding inequality is also required in M0; a monthly net balance alone is insufficient. M1 may replace conservative prefunding with a qualified event-date cash checker.

In an illustrative GBP-denominated plan, an option costing £2,400 with £1,800 due immediately fails a £250/month payment ceiling without an approved alternative schedule, even when the direct-spend budget is £3,000. A small average monthly cost is not evidence of affordability.

## Uncertainty and conditional plans [M0]

Maintain distinct **verified inputs**, **modelled outcomes** and **conditions to resolve**. A primary route can include conditional steps, but its status must say so. Show branches such as “if funding is approved” and “if an intermediate offer is accepted”; do not present both branches as simultaneously affordable.

Stress cases include no funding award, a missed intake, slower learning, a longer job search, reduced study capacity and a higher required commute cost. Reuse the same scenarios across competing routes. **M0:** evaluate fixed candidate plans under a base case and explicit delay/no-award/no-offer stress cases; report failed readiness or cash checks. Do not optimise adaptive policies. **M1:** when scenario-contingent decisions are added, choices before observation must be identical across indistinguishable histories; prevent clairvoyant plans.

For paired scenarios, call $p$ scenario-wise dominant over $q$ only if $T(p,\omega)\le T(q,\omega)$ and $C(p,\omega)\le C(q,\omega)$ for every $\omega\in\Omega$, with at least one strict comparison. Base-case dominance alone earns the label “better in the base scenario”; mark reversals or unresolved scenarios explicitly. Whisker overlap alone neither proves nor disproves dominance. Keep joint scenario points so independent marginal ranges do not imply nonexistent combinations.

Avoid learning individual hiring probabilities from convenience samples or extrapolating rejection rates across demographic groups. Until calibrated outcome data exist, use scenario ranges and human-reviewable assumptions. A more elaborate stochastic optimiser is not an improvement if its probability inputs are fictional.

## Solver architecture and choice [M0, OPT-1]

**Committed solver:** deterministic Python exhaustive depth-first search over the reviewed, finite monthly catalogue. No second solver, stochastic search or Rust binding is in the M0 stack. M1 continues with the same engine until measured needs justify a separately approved specification change; no latent runtime fallback is required.

Use a canonical action order. For each concept, branch on skip or one reviewed start/variant; enforce mutually exclusive variants, prerequisites, capacity, cash and target gates. Visit each allowed selected offering set exactly once. Schedule order/parallelism is encoded by the chosen dates and action DAG, not by permuting equivalent lists. Information-gathering and work actions remain eligible where they affect feasibility; minimal skill covers are insufficient.

Prune only an irreparable constraint violation or a certified bound under the actual model. Negative economic cost and future income make naive accumulated-economic-cost pruning unsafe. Future funding must not be ignored when deriving a lower bound. Do not prune on first-front dominance, count of dominators, or current readiness alone: such pruning can destroy F2/F3 or economically distinct supersets. Stop-at-readiness pruning is allowed only where a proved domain rule makes every extension outside the defined route scope.

Persist every distinct feasible schedule encountered to a disk-backed, versioned archive, including dominated schedules. Recompute layers over that archive, grouping families only for presentation. Do not evict candidates to make a completeness claim fit in memory. State/resource caps stop the run before an unrecorded candidate is silently lost.

**M0 limits:** 30 seconds wall time, 1,000,000 expanded search states and 50,000 archived feasible schedules per target, whichever is reached first. These are explicit resource limits, not throughput predictions. Canonical ordering, model/data versions and all limits are recorded. An optional longer run is M1. After reaching any cap, retain the archive and report the exact stop reason.

`search_coverage` is **complete** only after exhausting the entire declared finite search tree with sound pruning; otherwise it is **budget_truncated**. Separate operational states remain queued, running, succeeded, failed, cancelled and invalid-input. A crash is not a successful truncated result. Record expanded states, feasible count, remaining-work indicator, model limits, pruning-rule version and truncation reason. No elaborate certificate file is needed in M0, but these facts are not optional.

A complete run with zero feasible schedules proves only **no feasible route in this bounded monthly model and catalogue**. Incomplete coverage cannot establish even that. A complete run proves the three layers only over the declared model; it does not prove global optimality across unresearched courses or excluded dates. Tens of options with two intakes can still create millions of combinations, so completion within the budget is not assumed.

**Consequence of the M0 limits.** At the M0 upper bound (24 concepts, two starts each, at most six selected), the selection space alone holds $\sum_{k=0}^{6}\binom{24}{k}2^k=10{,}161{,}633$ selected sets, so the 1,000,000-state cap cannot exhaust it unless sound pruning removes most of it. `budget_truncated` is therefore the expected coverage for large catalogues, and `NO_ROUTE_IN_BOUNDED_MODEL` is correspondingly rare near the bound. Results, UI and exports treat truncation as the normal state: lead with “Best trade-offs found”, state the instance size, and say which narrowing (fewer concepts, one start, a shorter horizon) would let the search complete. Solver qualification reports the measured instance sizes at which complete coverage is reached. No rule changes: completeness semantics, the caps and the layer definitions stay as written.

Retain the counterexample: $(1,3),(2,2),(3,1)$ are mutually nondominated and all dominate $(4,4)$, which lies in F2. Being beaten three times is not a valid exclusion rule. Correctness tests compare this DFS against a simple independent Cartesian-product oracle on tiny instances. No network or LLM call occurs inside candidate evaluation.

## The three Pareto layers [M0]

For two feasible paths to the same target under the same assumptions:

$$ p\prec q\iff T(p)\le T(q),\ C(p)\le C(q),\ (T(p),C(p))\ne(T(q),C(q)). $$

For the evaluated feasible archive $\mathcal P$, define:

$$ F_1=ND(\mathcal P),\qquad F_2=ND(\mathcal P\setminus F_1), $$

$$ F_3=ND\bigl(\mathcal P\setminus(F_1\cup F_2)\bigr). $$

Equal objective values do not dominate one another; preserve materially different route alternatives behind an equivalent-point grouping. The first front contains no route bettered on both objectives without a trade-off. The second and third fronts are obtained by peeling earlier fronts, not by assigning arbitrary grey scores.

**Critical implementation rule:** retain the full feasible archive encountered under OPT-1, including dominated schedules, and recompute layers over it. A resource cap truncates search and must be disclosed. Lead with “Best trade-offs found” or a concrete better-route margin. Keep layer numbers as secondary technical detail and record whether their scope is exact or approximate. Never claim these are the complete mathematical layers over all possible careers.

A first-front-only pruning algorithm may deliberately discard everything needed for layers 2 and 3. Only label all three layers exact when enumeration or a separately proven layer-preserving method establishes completeness. An epsilon sweep proving some efficient objective pairs does not by itself prove all routes or dominated layers.

Illustrative verification fixture in **direct-spending-only mode**, all routes feasible and reaching the same readiness target. It validates dominance mechanics, not the default economic-cost model:

| Route | Months | Total direct transition cost | Layer |
|---|---:|---:|---:|
| A | 6 | £4,800 | 1 |
| B | 9 | £2,400 | 1 |
| C | 12 | £900 | 1 |
| D | 8 | £5,400 | 2 |
| E | 11 | £3,000 | 2 |
| F | 14 | £1,200 | 2 |
| G | 10 | £6,200 | 3 |
| H | 13 | £3,600 | 3 |
| I | 16 | £1,600 | 3 |

This fixture tests ranking, not real training-market feasibility. Store route identity, schedule, objective values, feasibility report, objective definitions, dataset version, profile version, algorithm/version, deterministic ordering, scenario set, runtime, search bounds and coverage status. A complete run on the same immutable input reproduces the same result. State-count-limited replay is reproducible; wall-clock truncation can stop at different prefixes and must not be promised bit-for-bit repeatable.

# 13 The route comparison experience

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Coordinated comparison and journey views [M0, VIS-2]

Use one comparison panel per target role/level, with shared axes only when currency, horizon, baseline and objective definitions are comparable. A cheap route to a different occupation never dominates another target's route. Switching targets preserves each target's filters and selected path.

The **Trade-off view** leads quantitative comparison: time horizontally and the selected cost measure vertically. Plot discrete feasible schedules; highlight the nondominated points. A staircase or shaded dominance boundary can aid reading, but must be labelled a comparison boundary, not an attainable continuum. No smooth interpolated frontier suggests training routes between actual options.

Every point with supported scenario estimates has labelled time/cost whiskers or an expandable scenario envelope. Focus reveals joint scenario points and the assumptions that move them. No probability is implied. Display absent scenario evidence as unknown rather than zero-width uncertainty.

Layers 2 and 3 remain visible in readable grey. Lead their cards with a concrete margin, such as “Route B is 2 months faster and costs 600 less in this scenario”, naming the currency and cost basis. Use a consistent, declared comparator selection rule; when several dominators exist, expose them rather than asserting an inherently nearest one across incomparable units. Preserve layer and family identity in accessible text. Focus increases contrast without hiding dominance status.

The **Journey view** provides the requested sense of progression. **M0:** show one static selected-plan Gantt with work/study bands, waits and gates. **M1:** animate the transition into focus and add up to two pinned comparators on the same time axis. Branches represent actual alternatives or conditional events; vertical ordering merely separates routes. The complete archive remains available in a grouped list. This preserves organic, striking visual progression while avoiding 12-18 overlapping strands.

## Controls and filters [M0]

Keep the requested top time/cost sliders, exact numeric inputs and keyboard operation. **M1:** add a directly draggable chart range box as a synchronised optional control. A visual brush never replaces the accessible sliders. Label economic cost with its baseline and horizon; a direct-spend budget is a separate control. Expose monthly payments, hours, borrowing and scenarios in the practical-limits panel.

View filters hide/reveal already evaluated routes immediately without changing recorded ranks. An explicit “best within these choices” action can rerank the full eligible retained archive; changed planning constraints create a new solve/input version. A route does not become globally optimal because its dominator is hidden. Pinned out-of-range routes keep an explicit badge.

Group repeat intake schedules under ROU-1 family cards. Prioritise distinct route families when choosing which grey alternatives to show. Changing a display cap or grouping does not alter the mathematical archive or proof scope. Preserve earlier results during recomputation and never replace an inspected route silently.

## Focused route cards [M0]

Clicking a strand dims other routes and reveals compact step cards. Each shows the action, provider/employer or role class, start/end range, workload, direct outlay/payment timing, income effect, funding status, requirements gained, evidence to produce, prerequisites, source freshness and a primary action link. Job steps separate “search/travel costs” from “net pay after an accepted offer”; a single price on a job card is insufficient. Conditions have clear gate markers. Parallel activities are visible as overlapping bands rather than falsely serial steps.

**M0:** every card uses a fixed licensed icon. **M1:** every card contains a small contextual generated illustration when available. Use a consistent art brief and asset cache keyed by action concept, visual style and model version. Generate shared topic images in advance; generate a truly specific image only when needed. Do not send CV content, diagnoses or user identifiers in image prompts. Images never encode the schedule or important facts.

**M1:** Use Meta Muse Image for the production image adapter when the user's key and region support it. It has its own image endpoint/model, separate from text inference. Static licensed icons are the explicit, visible alternative while generation is pending or unavailable; lack of an illustration never blocks comparison or printing. Images are labelled decorative/illustrative and must not impersonate a provider logo, real campus or endorsed credential. [1,39]

Show a diverse selection of discrete points/family cards, with all retained routes available in the list; the journey surface is limited to the selected route and two pinned comparators. Preserve lowest-cost, shortest-time and structurally distinct alternatives. Explain any “balanced route” as a chosen preference rule, not a uniquely optimal answer; do not invent a universal knee-point recommendation across currencies and unnormalised units.

# 14 Visual system and interaction quality

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Art direction [M0]

**A calm observatory of possibilities.** Use an ink-blue spatial canvas, fine luminous branching lines, crisp typography and warm, tactile cards. The personal conversation feels quiet and human; the opportunity and route views carry the visual spectacle. Organic movement must reveal structure or change, not compete with reading.

The visual identity uses a simple open-circle/branch motif. Avoid literal brains, robotic faces, ladders that imply one correct hierarchy and generic stock photographs of successful executives. The app should feel personal without a fictional human persona claiming experience or credentials.

| Token group | Proposed system |
|---|---|
| Surfaces | Ink #09121F; raised ink #142338; light canvas #F5F7FA; light cards #FFFFFF |
| Text | On dark: #EEF4FC primary, #B1C1D6 secondary; on light: #142338 primary |
| Focus/action | Sea-glass #5DE0C1 on dark; accessible darker variant on light; one shared focus-ring system |
| Industry palette | Blue, amber, violet, coral and olive; at most five named industries plus neutral Other in an overview. Reserve sea-glass for selection/action. Keep mappings stable across filters, and supplement colour with labels/shapes |
| Status | Separate icon/text semantics for complete, conditional, stale, error and unknown; industry colour never doubles as status |
| Type | Humanist sans for body/UI, expressive but readable display face; tabular digits for money/time; self-hosted licensed fonts |
| Scale | 4/8/12/16/24/32/48 spacing; 16px body baseline; restrained 12/16/24px corner radii |
| Motion [M1] | 120-180ms controls, 220-320ms panels, 450-700ms deliberate graph reveals; interrupted transitions continue smoothly |
| Pulse [M1] | Soft 3-4 second halo cycle, at most five nodes; pause when reading, tab hidden or reduce-motion enabled |

All values are design proposals to validate, not a claim that hex colours alone establish accessibility. Maintain tokens in code and design files, with semantic names rather than raw values scattered through components. Cards, chips, evidence drawers, controls, empty states and printable documents share the same vocabulary.

## Accessibility and performance are part of the visual brief [M0]

Target WCAG 2.2 AA, keyboard-only completion, visible focus, meaningful headings, screen-reader announcements, zoom/reflow and no colour-only information. Respect `prefers-reduced-motion` and offer an in-app calm mode. Provide a pause control for ongoing animation; no flashing, forced camera movement or animation required to understand a result. W3C guidance explicitly addresses animation sensitivity and pausing moving content. [29]

SVG semantics must be designed and tested; choosing SVG does not automatically make a graph accessible. Any canvas text/cards have DOM equivalents. Focus moves predictably when a node opens a drawer; filtering never discards keyboard focus. Make every action possible through a list, including comparison and selection. Tooltips do not contain unique information. Validate with users who experience vestibular sensitivity, visual impairment, attention difficulties or motor limitations.

Use SVG with D3 layout/geometry for all committed graph/chart surfaces. Use stable anchors, bounded visible marks and list pagination. M0 caps the graph projection at 100 visible job nodes with visible aggregation counts; the list retains the full result set. Measure keyboard use, readability and selection responsiveness. **M1:** worker layout, semantic zoom and animation are added to this same renderer. No alternative GPU renderer is selected. [28]

**M1 qualification targets:** p75 LCP at most 2.5 seconds, INP at most 200ms and CLS at most 0.1 on the chosen field-measurement cohort. Target 60fps during interaction with 500 visible nodes and 1,000 edges on a specified MacBook Air M1/8GB test device in current supported Safari/Chrome; aggregate larger datasets. Target at least 30fps on a specified mid-range mobile device. Log frame-time percentiles and battery/thermal behaviour. These are targets requiring measurement, not promises based on a framework choice.

# 15 Progression and the chosen plan

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Progress without pressure [M0]

The six chapters form a visible journey, with completed evidence and decisions becoming stable illuminated landmarks. Distinguish **planning progress**, **evidence acquired** and **real-world action completed**. A filled profile is not a gained skill, and clicking a course is not learning.

**M0:** use clear step completion, evidence labels and one next-action card. No external reminder integration is required. **M1:** celebrate a verified artifact, a clarified constraint, an application submitted by the user or a completed assessment. A small animation and plain-language acknowledgement are sufficient. Offer achievable next actions with estimated effort and user-chosen reminders. No streak loss, leaderboards, scarcity countdowns, shame messages or rewards for spending on courses. Pauses and changes of direction preserve achievements.

A “Today” card offers one useful action, a short alternative and a rest/reschedule control. Default milestones are concrete: verify funding; contact a course provider; complete a diagnostic; create a portfolio example. The user decides which action to take. If they return after a long break, greet them with a concise update, not a debt of missed tasks.

Track readiness through separate requirement bands: evidenced, planned, conditional and unresolved. Show progress within a user's own plan; never compare them to other users or infer career worth from speed. Optional anonymous product research must be separately consented and cannot affect recommendations.

## Select, commit and revise [M0]

Choosing a route produces a summary of the target, major trade-offs, direct spending, economic cost and its baseline/horizon, peak monthly payments, cash reserve, workload, conditions and source dates. Ask for confirmation of consequential assumptions before treating the plan as active. This is not confirmation of an application, enrolment or resignation.

Pin the route as a versioned plan. Completed steps become factual history; future steps remain proposals. If an intake closes or a provider changes fees, show a change comparison with affected steps and alternatives. Preserve user edits and explicitly accepted commitments. A replan optimises remaining choices with sunk costs and completed learning treated correctly; it must not recommend repeating completed work merely because it rebuilt the catalogue.

## Printable and portable plan [M0]

**M0:** generate an ink-efficient browser print view with print CSS and downloads of the same immutable plan snapshot as JSON and ICS. Users can use browser Save as PDF; a dedicated PDF generator and tagged accessible PDF are M1. Check actual dates, model-month labels, costs, gate conditions and page clipping. ICS events are labelled proposed/conditional, with original timezone/date semantics; the download does not create external events. The default printed plan contains:

1. A one-page overview: chosen target, region, goal definition, schedule, direct spending, economic cost with baseline/horizon, peak monthly payment, conditions and the next three actions.
2. A dated sequence showing concurrent activities, intake/application deadlines, waiting periods and offer/assessment gates.
3. Step details: provider/role class, prerequisites, workload, cost/payment timing, outcome evidence, funding status and source/application links.
4. A monthly budget with earnings assumptions, payment schedule, reserve checks and outstanding debt; clearly separate favourable funding from guaranteed expenditure.
5. Contingency instructions, review dates and assumptions requiring verification.
6. AI Resilience Scores for the destination and intermediate roles, scope/horizon, evidence quality, scenario ranges and the date for reassessment.
7. Source register, last checked dates, plan ID/version and the limits of the optimisation result.

**M1:** offer a compact two-page summary, a complete plan, and an optional one-page adviser handoff containing only the user-approved objective, constraints, evidence gaps and questions. Discover current local public/nonprofit career services through the regional adapter; do not imply a referral or send the handoff automatically. All export formats use the chosen locale and preserve original currency/source references.

Include clickable links and optional QR codes for action pages, but never put secrets, sensitive details or publicly accessible private-plan links in a QR code. Allow sensitive notes, illustrations and financial detail to be excluded. All essential information remains readable in monochrome; avoid splitting a step card across pages. **M1:** dedicated PDFs have searchable text, bookmarks and tagged accessibility, tested independently of browser print support.

M0 provides JSON and ICS downloads; neither creates external events. **M1:** coach sharing and external notifications/calendar integrations require explicit scoped permissions and revocation. The default plan remains private.

# 16 Model strategy and API key handling

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Current Meta choices and M0 selection [M0]

The verified Meta catalogue at the research date lists `muse-wonder-1.0` for high-capability reasoning, `muse-spark-1.3` as the current Spark version, and `muse-image-1.0` for images. Muse Wonder Full is available through Muse Code subscriptions, not the Model API; it must not appear as an API-key option. The older Llama line is therefore not the default “latest Meta” choice. [1]

**M0:** use the pinned approved Spark model for all application text tasks and Meta search for discovery. No automatic model escalation or provider substitution. **M1:** add a tested Wonder escalation policy for difficult synthesis. Mathematical evaluation remains deterministic. Never make a more expensive model call merely to decorate the experience. Use the user's key only for that user's authorised tasks.

Maintain a model registry containing endpoint, exact identifier, release/deprecation status, supported schema/tools, region availability, context/output limits, price version and evaluation status. **M0:** check availability at key setup and pin the selected release for the beta/run. **M1:** poll official metadata regularly, but do not switch models during a run or silently deploy an untested release. “Latest” means latest available approved Meta model for the selected capability; explain if a newer release is awaiting qualification.

Pydantic AI now documents a native Meta provider. Use that integration with an explicitly tested model/profile instead of maintaining an unnecessary generic-provider wrapper. Its documented tool-choice restrictions mean that forced-tool structured output must not be assumed to work: choose a supported native schema-output mode and verify the exact pinned model/library combination. Contract-test streaming, schemas, refusals, truncation, timeouts and usage reporting. Structural validation still cannot establish factual truth. [3,59]

## Privacy mode and failure semantics [M0]

Use Standard model IDs for personal data. Meta's published Standard mode excludes model-training use; Contributor variants permit training use in exchange for lower pricing. The product must not silently select Contributor mode. “Not used for training” is not equivalent to zero retention: retention, subprocessors and transfers require their own review and accurate user disclosure. [2]

If a key is invalid, over budget, unavailable in the region or lacks an image capability, preserve the work and explain the exact limitation. Manual profile editing, a clearly labelled synthetic-data demo, saved comparison and existing-plan printing remain usable. Retain the user-supplied Meta key requirement; a proposed institution-funded or provider-key mode would be a separate explicit product decision, not a silent replacement. Never route personal data to a different provider without explicit configuration and consent.

## Secret storage and spend controls [M0]

Accept the key through a secure form over TLS. Store only a secret reference in domain records and workflow history. **M0:** encrypt the separate credential record using authenticated encryption (AES-GCM through a maintained library), a unique nonce, workspace/record IDs as authenticated context, and a versioned runtime key held in GCP Secret Manager outside the database, code and backups. Enforce ownership before decryption; test nonce/key rotation and revocation. This has a broader compromise impact than per-tenant key separation and must be disclosed in the private-beta risk assessment. **M1:** tenant-bound envelope encryption/KMS.

**M0:** never place the user key in browser localStorage, URLs, analytics, errors, PDF exports, model prompts or agent memory. Resolve it just in time inside authorised model-call activities. Rotation/revocation immediately affects queued future calls.

**M0:** persistent background work requires explicit agreement to encrypted key storage. If declined, manual editing and saved-plan access remain available. Explain that the backend uses the supplied key for the requested service; it is not an end-to-end encrypted chat hidden from the backend.

**M1:** add a session-only option with a truthful expiry contract: disconnect/expiry cancels future key-dependent work. Such a session cannot support unattended research after the secret expires.

Set per-run and per-period spend limits and display estimated incremental cost before deep research. Reserve budget for concurrent calls, reconcile actual usage, cap tokens/tool calls and stop new requests when the budget is consumed. Provider-side limits are an additional control because in-flight usage can make local estimates imperfect. Separate user API charges from product subscription, scraping and data-licensing charges.

**M1 cost illustration, including features not enabled in M0:** an illustrative uncached workload: Spark with 60,000 input and 12,000 output tokens costs $0.126 at published Standard rates; Wonder with 30,000 input and 6,000 output costs $0.24. Twenty Meta searches add $0.05 and six images add $0.06, totalling **$0.476** before tax and non-Meta infrastructure. This is an arithmetic example, not a measured plan cost or a spending guarantee. The published prices and model counts must be checked at runtime. [2]

# 17 Software architecture and technology stack

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Architectural shape [M0]

Use a modular monolith for the transactional product, with separate execution processes for durable workflows, untrusted HTTP fetch/parse and optimisation. Browser/document parsing and server-side PDF rendering are M1. Modules enforce boundaries in code, not merely directory names. Keep complex business rules independent of vendors, transport, UI and LLM frameworks.

The request path is: accessible web client to authenticated API; API to application use case; domain validation to transactional repository; durable job submission through an outbox. Workflow workers retrieve immutable input versions and call restricted adapters. Verified outputs return through explicit domain commands and events. A browser worker cannot write a person's skill profile, and an LLM cannot directly alter a selected plan.

Use PostgreSQL as the authoritative store. Model graph relations in normal relational tables initially: skills/prerequisites, template requirements, action outcomes and provenance edges. A specialised graph database is unnecessary until measured query needs justify it. M0 retrieval uses PostgreSQL full-text search and explicit ESCO aliases/skill links. No embeddings provider or vector database is selected.

## Concrete stack [M0, ARC-1]

| Layer | Fixed M0 choice | Responsibility |
|---|---|---|
| Web | React, TypeScript, Next.js | Authenticated shell, chat, comparisons and print CSS |
| UI | Tailwind tokens, Radix controls, fixed licensed SVG icons | Consistent responsive components; no image endpoint or animation framework required |
| Graphics | SVG and D3 | Cost-time points, selected Gantt and bounded city/company dendrite |
| Client data | TanStack Query, small local selection state | Separate server state and interaction state |
| API | Python 3.12, FastAPI, Pydantic v2 | Typed commands, auth/ownership, validation |
| LLM | Pydantic AI native Meta provider; pinned Spark model | Bounded proposals/extraction with user-supplied key |
| Workflows | DBOS Python, PostgreSQL, transactional outbox | Durable runs; one retry owner; no second engine |
| Acquisition | ESCO/ASHE import scripts, Adzuna adapter, Scrapling HTTP | Bounded selected-page retrieval; no crawling or browser automation |
| Solver | Deterministic Python DFS in a cancellable child process | Finite monthly search, complete encountered archive, independent checker |
| Data | PostgreSQL 16, SQLAlchemy, Alembic | Domain records, private cache, run/archive state; no PostGIS/Redis |
| Identity | Firebase Authentication, Google sign-in, verified invitation allowlist | Backend verifies ID token and invitation/ownership on every request; sign-in alone is not authorisation |
| Hosting | Cloud Run web/API; non-preemptible GCE DBOS worker; Cloud SQL; Cloud Storage; Secret Manager | HTTPS web endpoint and persistent workers; private objects and runtime secrets |
| Diagnostics | Structured redacted logs, run IDs, basic counters/error alerts | Observable failures and spend; no raw chat/CV/key logs |
| Quality | pytest, Hypothesis for critical invariants, Playwright and axe | Fixtures, independent solver oracle, access isolation and browser checks |
| Reproducibility | uv/pnpm lockfiles, pinned container digests, migration scripts, deployment commands | Rebuildable beta; no infrastructure-as-code requirement at M0 |

Pin mutually compatible package versions in the first reproducible build; a specification is not evidence that an untested dependency combination works. M0 explicitly excludes CP-SAT, Rust solvers, PyO3, PixiJS, Temporal, Redis, PostGIS and embedding services. M1 may add features/tools only through a later explicit architecture decision; they are not latent fallback paths.

**DBOS is the committed workflow engine.** Use the documented Pydantic AI integration with pinned compatible versions and test interruption/restart before relying on it. A two-hour investigation can expose a blocker; it cannot establish recovery correctness or justify a silent swap to a jobs-table loop. If the combination fails, preserve explicit failure/manual states and revise the architecture deliberately before continuing dependent work. No Temporal port or alternative worker implementation is required. [57,58]

Use a transactional outbox for domain writes that create work. Dispatch with stable run/workflow IDs and idempotent handlers. DBOS step recovery does not make external model calls exactly once; reconcile uncertain spend and cap retries. Keep secrets out of durable arguments/results and test that the integration does not serialise credentials into workflow history. [57,58]

Deploy the web/API as separate Cloud Run services, the durable worker as a long-lived GCE container, and PostgreSQL on Cloud SQL. No worker depends on an HTTP request remaining open. Use a single approved UK deployment region for M0 infrastructure, least-privilege service identities, private object access and Secret Manager runtime secrets; review external Meta/data-provider transfers separately. Backend authentication checks the Firebase token's project/issuer/expiry, enables the Admin SDK revocation check, checks the invitation record, then enforces workspace ownership. [68,69]

**M1:** add tenant envelope encryption, qualified operational telemetry/SLOs, Terraform and signed builds/SBOM. PostGIS and Redis are not automatically required for launch; add them only if a defined feature/query need warrants them. The same applies to any future solver or renderer change. This resolves implementation choices without pretending future requirements are already known.

## Domain modules [M0]

| Module | Owns | Must not own |
|---|---|---|
| Identity and consent | Accounts, access, consent, secret references | Career-suitability judgments |
| Profile | Confirmed circumstances, preferences, evidence provenance | Scraping or solver internals |
| Career exploration | Interview state, grounded title suggestions, diversity policy, target confirmation | Autonomous commitment to a career or personality-based exclusion |
| Market intelligence | Taxonomies, regions, role cards, AI resilience methodology/assessments and claims | Private profile inference |
| Acquisition | Source registry, attempts, snapshots and parsed facts | Personal recommendation policy |
| Capability assessment | Rubrics, skill evidence, gap classification | Funding approval or hiring prediction |
| Opportunity catalogue | Jobs, training, intakes, funding instruments | Final route ranking |
| Planning | Feasible action graph, scenarios, objective definitions | Web access or model prompts |
| Optimisation | Solve request/result, candidate archive and proof metadata | Creating unsupported facts |
| Plan and progress | Chosen route versions, commitments, milestones, exports | Mutating past evidence silently |

Dependencies point inward: vendor adapters implement domain/application ports. Use explicit dependency injection, small cohesive functions, immutable value objects for money/date/evidence, typed errors and transaction boundaries. Avoid a generic “agent manager” owning every workflow. Keep research prompting separate from feasibility and presentation.

## Durable execution [M0]

Each research workflow snapshots its profile/targets, fans out bounded region/role queries, fetches, validates, deduplicates, synthesises and commits a versioned catalogue. A separate solve workflow consumes that snapshot; a separate export workflow consumes a selected plan version. No solve depends on a moving live catalogue.

Activities are retryable and may execute more than once. Use idempotency keys, source fingerprints, unique database constraints and a transactional outbox. Do not claim exactly-once external model calls if the provider cannot guarantee idempotency; reconcile ambiguous responses and account for possible duplicate spend. One layer owns each retry budget to prevent multiplied retries.

Workflow histories contain identifiers and small encrypted private payload references, not raw API keys, entire CVs or large web pages. Account deletion must remove private payloads and object-store copies according to policy, including workflow histories or their encrypted payload keys. Define cancellation for upstream browser/model jobs and compute processes, not just the UI spinner.

Long-running operations return `202 Accepted` plus a run ID; server-sent events stream durable status and partial verified results with event IDs for reconnect. The terminal API state, not the last animated message, is authoritative. Partial results have completeness and freshness fields. A stale profile version cannot overwrite a newer one.

# 18 Data contracts and invariant examples

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## Core records [M0]

| Record | Critical fields |
|---|---|
| ProfileVersion | User/workspace ID, version, field states, constraints, evidence IDs, consent scope |
| TargetRole | Canonical occupation, local title/aliases, level, region scope, desired outcomes, confirmation, zero-to-three exemplars |
| OccupationConcept and Crosswalk | Native taxonomy/version/code, language, aliases, tasks, broader/narrower/related mappings, confidence and provenance |
| RegionCapability | Jurisdiction/work area, capability, verified-local/partial-inherited/user-assisted/unavailable state, language/source coverage, last check |
| CareerSuggestion and Slate | Grounded occupation, rationale/profile evidence, candidate channel, novelty/uncertainty, feasibility state, slate version and diversity audit |
| SourceClaim | Subject, field, value/unit, actual geography, source URL/span, retrieval/publication/effective dates, licence, validation state |
| AIResilienceAssessment | Occupation/seniority, inherited scope and supported modifiers, horizon, anchored ordinal band, lower/upper bound or null, optional reference point, evidence quality, source/method versions, review/invalidation state |
| SourceAttempt | Provider, requested URL, timestamp, allowed/blocked/error/success status, HTTP metadata, charged usage, retry parent |
| JobPosting | Canonical job/employer, source copies, title, tasks, location/work mode, pay terms, requirements, dates/status |
| SkillRequirement | Skill/credential ID, task, ordered level, gate/preferred type, importance, rubric/template/source versions |
| SkillEvidence | Claimant, task/context, artifact or statement reference, independence, recency, assessment status, permitted AI/tool use |
| LearningOption and Offering | Stable syllabus/provider plus separate dated intake, fees, timetable, places, prerequisites and outcomes |
| FundingInstrument | Jurisdiction, rules/version, eligible costs, award state, timing, exclusions, repayment/obligations |
| PlanAction | Option/role-class reference, explicit starts/month masks, prerequisites, payments/income/workload, completion gate, typed OUT-1 outcomes, assumptions and condition |
| SolveRun | Immutable input versions, objective/scenario specification, limits, solver/version/order, operational status, search coverage, limits and counts |
| RouteFamily | Canonical action DAG, material format/credential/job/finance structure, schedule variant IDs; presentation grouping never changes proof |
| Route | Family/actions/schedule, feasibility report, direct/cash/economic ledgers, baseline/horizon/scenarios, target, objective values, rank scope and contingencies |
| PlanVersion | Chosen route, user confirmations/edits, commitments, completed evidence, change history and export metadata |

Maintain referential integrity and provenance for every derived object. A source URL alone is insufficient: a reviewer must be able to locate what supported a value at retrieval time. For content that cannot be retained, preserve permitted minimal evidence and a truthful re-verification limitation.

## Typed contract sketch [M0]

The following defines the shape of the core user-facing constraints; it is not a complete implementation. Cross-record rules such as currency compatibility, unique cities, work rights, span end > start, allowed source hash/offsets, evidence semantics and M0 region/horizon limits belong in domain validation. The JSON personas are fixtures, not instances of this deliberately partial application schema. Do not send the entire domain schema to the LLM when a small patch schema will suffice.

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Money(StrictModel):
    minor_units: int = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")

class SignedMoney(StrictModel):
    minor_units: int
    currency: str = Field(pattern=r"^[A-Z]{3}$")

class CityPreference(StrictModel):
    place_id: str
    label: str
    country_code: str
    max_commute_minutes: int | None = Field(default=None, ge=0)

class Exemplar(StrictModel):
    evidence_id: str
    kind: Literal["url", "upload", "pasted_text"]

class TargetRole(StrictModel):
    occupation_id: str
    title: str
    seniority: str | None = None
    confirmed: bool = False
    exemplars: list[Exemplar] = Field(default_factory=list, max_length=3)

class SourceSpan(StrictModel):
    source_id: str
    source_hash: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)

class PlannedSkillOutcome(StrictModel):
    skill_id: str
    level_on_completion: int | None = Field(default=None, ge=0, le=4)
    evidence_kind: Literal[
        "topic_mention", "practice", "assessed_work_sample", "exam"
    ]
    confidence: Literal["unsupported", "provisional", "corroborated"]
    source_span: SourceSpan
    rubric_version: str
    claim_state: Literal["planned_conditional"] = "planned_conditional"
    review_state: Literal["proposed", "accepted_assumption", "reviewed", "rejected"]

class M0SearchLimits(StrictModel):
    max_actions: int = Field(default=24, ge=1, le=24)
    max_starts_per_action: int = Field(default=2, ge=1, le=2)
    max_selected_actions: int = Field(default=6, ge=0, le=6)
    max_months: int = Field(default=24, ge=1, le=24)
    wall_seconds: int = Field(default=30, ge=1, le=30)
    max_states: int = Field(default=1_000_000, ge=1, le=1_000_000)
    max_feasible_archive: int = Field(default=50_000, ge=1, le=50_000)

class PlanningDraft(StrictModel):
    schema_version: Literal["1.2"] = "1.2"
    cities: list[CityPreference] = Field(default_factory=list, max_length=3)
    targets: list[TargetRole] = Field(default_factory=list, max_length=3)
    remote_only: bool = False
    employment_countries: list[str] = Field(default_factory=list)
    direct_spend_cap: Money | None = None
    objective_basis: Literal["economic", "direct_spending"] = "economic"
    comparison_horizon_months: int | None = Field(default=None, ge=1)
    income_baseline_id: str | None = None
    monthly_payment_cap: Money | None = None
    weekly_study_hours: float | None = Field(default=None, ge=0, le=168)
    borrowing_allowed: bool | None = None
    min_ai_resilience_score: int | None = Field(default=None, ge=0, le=10)
    ai_filter_mode: Literal["lower_bound", "reference_point"] = "lower_bound"
    include_unscored_roles: bool = True
```

Drafts may have no targets. Starting a local search requires a confirmed target and valid work-area scope; starting a budget-qualified solve requires confirmed budget semantics. Runtime domain checks enforce these stage-specific invariants instead of pretending every draft is complete. AI discovery filters become planning constraints only through an explicit command specifying target and intermediate-role scope; the draft filter alone is not such a command. Economic objective values can be negative and use `SignedMoney`; payments/fees use `Money`. Currency minor-unit exponents are metadata, not an assumed division by 100. An economic solve requires a confirmed common horizon and income baseline; if these are unavailable, request them or offer an explicit direct-spending comparison. Never switch objective semantics silently. “Unknown” money is null, not zero. An explicit field-state wrapper preserves whether null means skipped, unasked or unresolved.

For conversation output, use a bounded `InterviewTurn` containing the reply, proposed field updates, supporting message references, next question, missing critical fields and readiness for user review. Profile storage applies only allowlisted updates validated against the referenced profile version. Secret fields and plan commitments are never patchable by model output.

## API surface [M0]

Use versioned endpoints for profile patch/confirmation, interview turns, target selection, exemplar import, research-run creation, catalogue retrieval, assessment evidence, solve requests, route comparisons, chosen-plan creation, progress updates and exports. Separate writes from read queries; require auth/ownership on every object. Use cursor pagination for listings and graph projection queries by viewport/cluster.

Error envelopes include a stable code, human-readable message, retryability, affected stage and correlation ID. Required codes include:

```text
SOURCE_BLOCKED              RETRIEVAL_FAILED
INSUFFICIENT_EVIDENCE        SCHEMA_INVALID
MODEL_UNAVAILABLE           BUDGET_EXCEEDED
SOLVE_LIMIT_REACHED         STALE_INPUT_VERSION
FEATURE_NOT_IN_M0           MODEL_SCOPE_EXCEEDED
COARSE_MODEL_UNRESOLVED     NO_ROUTE_IN_BOUNDED_MODEL
```

Use `NO_ROUTE_IN_BOUNDED_MODEL` only with complete search coverage. Budget truncation has its own coverage value and stop reason; it is not infeasibility. Near the M0 bound truncation is the expected coverage (section 12, OPT-1): a truncated result leads with the best trade-offs found, states the instance size and names the narrowing that would let the search complete. A proven result states the precise model and catalogue scope. Return no fabricated empty success payloads.


# 19 Security, privacy and operational integrity

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

**M0:** document the processing purpose, data flows, lawful basis, retention, access controls and pre-test privacy risk assessment. Complete a DPIA before real-person processing where required; private-beta status is not an exemption. Use synthetic data until that decision and required safeguards are in place. Do not defer the assessment simply because the service is invitation-only. [64]

**M1:** broader jurisdiction-specific product/legal review before launch. ICO guidance treats health information and certain inferences as specially protected data and is itself under review following legislative changes; this document does not establish a legal basis or claim regulatory compliance. Avoid collecting health narratives when a practical accommodation suffices. [31]

Keep private profile/assessment data separate from shared public market data. Enforce tenant isolation in application access and database row-level controls; test object-storage URLs and background-job access as well as HTTP endpoints. Do not use personality, health or protected-characteristic proxies to deny careers or market debt. Citizenship/work rights are collected only where relevant to explicit eligibility.

No third-party advertising or session replay on chat, financial, CV or assessment screens. Redact sensitive fields from telemetry. Logs contain record IDs and error classes by default. Support data export, correction, deletion and revocation of shared access; publish retention periods, deletion timelines and backup expiry. A reasonable proposed default is automatic deletion of raw uploads 30 days after confirmed extraction unless the user opts to retain them, with explicit exceptions for user-selected evidence storage.

Public research workers cannot access personal files; image prompts use generic action concepts. The model receives the minimum profile subset necessary for its task. External webpages never receive names, financial circumstances or entire CVs through search queries. Do not use a user's key or sensitive session state to enrich the shared global catalogue for other customers.

**M0:** retain dependency locks and licence notes; run secret/dependency checks, migration checks and a basic backup/restore exercise. **M1:** add the SBOM, signed builds and wider restore/incident qualification. Research-provider outages degrade to dated saved data with clear labels or an explicit unavailable state, not to invented facts. M0 has no alternate-provider fallback. The explicit manual-text route is a user-selected input mode, not a fabricated retrieval success. Any later automatic fallback needs an approved contract preserving data/privacy and failure semantics.

**M1:** Recommended availability target is 99.9% for core editing and saved-plan access, with external-data availability reported separately. Set explicit recovery objectives, initially RPO at most 24 hours and RTO at most four hours, then verify them with restore exercises. These are service design targets, not current performance claims.

Model output evaluations must cover hallucinated course names, fabricated citations, altered constraints, unsafe financial assumptions, demographic stereotyping, excessive reassurance and prompt injection. Human review is mandatory for reference-template publication and critical exception queues; it is not necessary for every routine fetch. Give users an error-reporting mechanism with correction provenance.

# 20 Quality gates and acceptance criteria

**Chapter gate: M0.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

## M0 fixture pack and worked trace [M0, TEST-1]

The accompanying `Nessa_M0_Fixtures.zip` contains five **synthetic** JSON personas, a complete numeric worked trace, a source-corpus manifest and a small executable validation script. No persona is a real user; no synthetic course price or regulatory fixture is published as evidence. These fixtures are contract examples for the future application, not proof that an application has been built or tested end to end.

| Persona | Scenario | Required result |
|---|---|---|
| P01 | Sure, employed; compare earnings-preserving study routes | Reproduce TRACE-01's financial ledger, three fronts and selected print snapshot |
| P02 | Unsure, unemployed; practical interests and unknown baseline | Grounded diverse shortlist, no forced personality test, no economic solve with an invented income baseline |
| P03 | Low budget; unapproved grant and bridge wages | Reject payment-cap violation; do not spend grant/offer income before its gate |
| P04 | Regulated target; attempted removal of registration gate | Refuse gate demotion; distinguish unresolved eligibility and out-of-model horizon from ineligibility |
| P05 | Returner already meeting modelled requirements | Lead with apply-now guidance; no forced training or degenerate frontier as the main screen |

**TRACE-01:** synthetic Manchester-based data-quality target; current evidence lacks independent querying and validation, while communication already meets its row. Each offered course proposes both missing outcomes with an assessed-work-sample gate. Provider/source IDs use a `fixture:` namespace. Admission is already completed in the synthetic initial state. All figures below are hypothetical GBP and cover a common six-month horizon.

Baseline net income is £2,000/month; opening cash £6,000; living costs £1,000/month; reserve £500; direct-spend and monthly transition-payment caps £1,500. User-approved work-pattern assumptions differ by route. No grant, new borrowing or immediate target-job salary is assumed.

| Route | Readiness months | Direct spend | Six-month income loss | Economic cost | Front |
|---|---:|---:|---:|---:|---:|
| A | 2 | £1,200 | £4,000 | £5,200 | 1 |
| B | 4 | £600 | £0 | £600 | 1 |
| C | 3 | £700 | £1,500 | £2,200 | 1 |
| D | 4 | £1,100 | £0 | £1,100 | 2 |
| E | 5 | £1,300 | £0 | £1,300 | 3 |

B retains earnings and pays £150/month for four months. The selected print snapshot must show 4 months, £600 direct/economic cost, £150 peak transition payment, six-month comparison basis and conditional readiness after assessment. With conservative prefunding, its minimum within-month lower cash bound is £4,850, above the £500 reserve. Do not overwrite current skill evidence with planned outcomes.

The synthetic score [5,8] fails a minimum-6 lower-bound filter. The five-route example is **economic-cost mode**; the earlier A-I fixture is **direct-spending mode**. They are separate datasets and must never share route IDs without their fixture namespace.

## M0 source corpus and acceptance [M0]

Before tester use, curate **20 labelled full job postings, 10 course pages and at least three funding pages** with permitted retention or reproducible source references. Label fields/spans, dates, missingness and failure cases; include predicted salary, snippets, closed jobs, ambiguous mappings, topic mentions without assessment, grants with conditions, HTML drift and prompt injection. These real-source pages have **not** been collected in this specification update. The manifest explicitly records that outstanding work; synthetic personas do not satisfy it.

Run fixtures and core checks after each meaningful change and in CI. Bind the future application's profile-to-print flow to the expected trace outputs. For LLM steps, evaluate schema/grounding and acceptable semantic sets rather than exact prose. Add at least one deployed real-provider smoke test with a consented key, cost cap, durable restart and browser print check. A mocked API run is not that test.

| Non-deferrable check | M0 pass condition |
|---|---|
| Readiness/outcomes | OUT-1 spans and rubrics are inspectable; planned != demonstrated; statutory gates cannot be demoted |
| Money/time | TRACE-01 and FIN-1 arithmetic; prefunding counterexample; conservative workload envelope; original dates preserved |
| Search correctness | Tiny-instance DFS agrees with independent exhaustive oracle; F1-F3, equal points, family variants and three-dominator counterexample pass |
| Failure semantics | Budget/state/archive limit, failed source, cancellation, crash and true empty complete archive are distinct |
| Permissions | Uninvited and cross-workspace access fail for API, cache, objects, stream, workflow and key use |
| Secrets/spend | No key in logs/history/prompts/export; revocation stops future calls; concurrent budget reservation and duplicate-spend ambiguity tested |
| Untrusted input | SSRF/redirect blocks, source access policy and page prompt-injection tests pass |
| Research | Snippets do not become full descriptions; missing data and unscored roles remain visible; no invented providers or awards |
| Recovery | Restart resumes a run without corrupting accepted records; stale writes fail; cancellation reaches child processes |
| UI/export | List, simple dendrite, scatter, sliders and static Gantt share selection/filter state; keyboard works; print/JSON/ICS agree with chosen snapshot |
| Privacy/operations | Pre-test privacy/DPIA decision, notice/consent where appropriate, deletion and basic restore verified |

A defect in a critical gate blocks M0 tester use even if a demo looks convincing. Five personas cannot replace isolation, cash-flow, failure and solver tests. The fixture validator delivered here checks its own arithmetic/contracts only; it does not certify those application gates.

## M1 qualification [M1]

Retain the broader specification's requirements for three contrasting jurisdictions, expert template/AI assessment qualification, inter-rater review, 500-URL extraction benchmark, source coverage/drift measurement, accessibility and named-device performance targets, tagged PDF, incident/restore objectives and security/operational controls. Test sure/unsure users, returners, low-budget users and regulated-role seekers across languages and data-rich/data-poor settings.

A 10-15-person concierge study is useful qualitative discovery, not proof of effectiveness or global validity. Measure decision comprehension, actionable uncertainty, affordability surprises and longer-term outcomes with appropriate consent and study design. Do not equate satisfaction or improved confidence with employment success. These are launch evidence requirements, not a day-by-day implementation plan.



# 21 Essential blind spots and decisions before implementation

**Chapter gate: M1.** Explicit M0/M1 subsection or paragraph labels take precedence. M1 includes M0.

| Blind spot | Required product response |
|---|---|
| An attractive route may be unattainable | Distinguish learning, evidence, admission, funding and employment gates |
| Cheap/fast can be the wrong life | Optimise within explicit suitability, quality and workload constraints |
| Familiar occupations crowd out better possibilities | Full-taxonomy and evidence-based discovery, multiple retrieval channels, diverse slates and region/language evaluation [DIV-1] |
| Personality can become a stereotype | User-editable work-style hypotheses, behavioural evidence and exploratory experiments; no deterministic type-to-career mapping [REC-1] |
| A global interface can hide local coverage gaps | Capability-specific regional contracts and native taxonomies; no silent English/UK fallback [GLO-1] |
| A future job may not exist | Plan role-class transitions and re-search gates; retain current vacancies separately |
| A course may teach little or confer no recognition | Verify syllabus, assessment and credential value; compare assessment/project alternatives |
| Confidence is not competence | Behavioural evidence, optional work samples, neutral uncertainty handling |
| Historical ads may be unavailable | Disclose coverage; never fabricate a trend from a current snapshot |
| AI exposure can be mistaken for inevitable replacement | Publish the score as an explainable, uncertain resilience indicator; distinguish adoption, role redesign and entry-level hiring; never claim AI-proof work |
| Regional data can be sparse | Label the actual geography and uncertainty; do not fake city precision |
| Income/funding may arrive late | Separate direct spending, lost-earnings objective, scheduled cash, reserves and debt [FIN-1] |
| Instant scraping can extract the wrong fact | Field-level provenance, semantic validation and visible extraction failure |
| Any optimiser may lose dominated routes | Preserve the required archive/layers and proof scope; do not assume exact first-front pruning preserves F2/F3 [OPT-1] |
| Animation may overwhelm the user | Calm mode, stable layout, static/list alternatives and pause controls |
| BYOK may deter nontechnical users | Clear onboarding, a synthetic-data demo and transparent charge separation; no secret exposure |
| “Latest model” can change behaviour | Registry, evaluation gate, version pinning and a user-visible model policy |
| Replanning can erase intent | Immutable chosen versions, user review of changes, preserved commitments |
| A trusted-looking card can overstate evidence | Show source, scope, date, uncertainty and a practical verification action |

M0 already fixes England, English, GBP and the bounded horizon. Business decisions still requiring an owner for M1: expanded geographic coverage and languages; rights/licences for job-board and historical salary data; product pricing and who pays shared research costs; the human-review service level; maximum supported planning horizon; whether institutional coach accounts are included; retention defaults; and commercial clearance of the provisional name **Careerwright**. The nearby name **Nesta**, already active in career-transition research, is a concrete discoverability/confusion concern, not a legal conclusion; retain Careerwright only as a working name pending a proper global brand and pronunciation check.

These decisions do not prevent a coherent architecture, but they do prevent honest promises of universal coverage, fixed unit economics or regulatory readiness. The implementation plan should be written against the proposed M0 boundary and its acceptance gates, as a separate exercise. The private-beta assumption still requires confirmation before deployment decisions.

# 22 Feedback assessment and revision record

## L0 build decisions, 2026-10-31, approved by the product owner

A whole-solution audit of the local build (L0) against this specification (`docs/reviews/l0-audit-2026-10-31.md`) proposed these decisions, and the product owner approved them on 31 October 2026. They record how L0 applies this specification. They are recorded here only: the sections they touch are unchanged, the version stays 1.3, no requirement is relaxed and no non-deferrable invariant changes. The development plan (v1.5) and ADR 0015 carry them for L0.

| Decision | What it means for L0 |
|---|---|
| The ONS coding index corroborates titles (section 4, DIV-1) | The pinned ONS SOC 2020 coding index, already a TAX-1 input, is an authoritative occupational source for DIV-1: a title idea from the model that it lists is corroborated, as an ESCO label is. **"Independent"** in "independent employer evidence" means distinct hosts or distinct employers; syndicated copies of one advert count once. A title verified as a quoted span on pages from two independent permitted sources, or on one official source's page, is also corroborated. A title the person supplies is always kept in their own words, as a provisional concept. The model proposes, deterministic code corroborates and the person chooses. |
| Options for any target (sections 10 and 11) | An option the person adds, and one that live research finds, for any target, is a workspace record in the section 18 shapes with `review_state: proposed`, never part of the option pack. A route built on one is qualified, never an unqualified "affordable and feasible", which is section 10's checkpoint rule. |
| Muse Wonder for the product owner's live sessions (section 16) | `muse-wonder-1.0` (Standard) is brought forward from M1 for the product owner's own live sessions only: qualified first, started only by an explicit session command, capped per run and per session, and every call ledgered. It is not an escalation policy and is never automatic. The pinned Spark model stays the default and the release model unless the product owner decides otherwise, and automated checks never call a model. |
| L0 deferrals | Not built in L0, and recorded so their absence is visible: one deep-research run that maps a person's whole role space (M1); the numeric salary and AI-range filters on the opportunity map, while L0 holds no reviewed pay mapping or AI score (a plain statement says so instead); two-minute, five-minute and deeper session modes (section 4); optional work samples (section 9); a what-if copy of a plan (section 3); the RegionCapability record (section 18); a revision history of answers on screen (section 3; every version is still kept); and language and region disparities in discovery's evaluation, since L0 has one language and one region. |

## Version 1.3 review decisions

Version 1.3 (28 October 2026) applies an assessment of this specification and the local development plan against the repository after its first three local sprints (`docs/plan/l0-assessment-handover.md`). It makes two clarifications and one disclosure. No requirement is relaxed and no non-deferrable invariant changes. The product owner confirmed decisions D1 and D3 on 28 October 2026.

| Reviewer proposal | Decision and change |
|---|---|
| A reviewed, dated option pack for the qualification personas' targets, with live research proposing records to the same catalogue (D1) | **Accept (confirmed by the product owner).** Section 11 and BND-1: the pack is an immutable public evidence pack and a permitted common read-only input in M0. Date and review state are always shown; a pack record never fills a live field and is never shown as current. Live research writes to the same catalogue contract inside its own workspace with `review_state: proposed`, excluded from unqualified recommendations until reviewed. No shared cross-tenant cache is added (still M1). |
| Disclose what the OPT-1 limits imply | **Accept as a disclosure.** Sections 12 and 18: at the M0 bound the selection space holds 10,161,633 selected sets, so `budget_truncated` is the expected coverage for large catalogues. Results lead with “Best trade-offs found”, state the instance size and name the narrowing that would let the search complete. Completeness semantics, caps and layer definitions are unchanged. |
| Model-written, span-cited explanations on career suggestions (D3) | **Accept (confirmed by the product owner).** Section 4, REC-1: at most one bounded call per slate; quotations only from confirmed answers and the grounded occupation record, each verified server-side; one repair, then invalid output. Deterministic provenance remains underneath and is what exports cite. |

## Version 1.2 review decisions

The ten-day private-beta assumption is proposed, not user-confirmed. The M0 boundary reduces integrations and scheduling freedom without changing the global product's data model. It is not a delivery guarantee or public-launch declaration.

| Reviewer proposal | Decision and change |
|---|---|
| Separate M0 and M1 | **Accept.** Explicit chapter/subsection gates and BND-1 precedence apply throughout. England/English/GBP is the beta adapter, not the product's permanent scope. |
| Defer operational breadth | **Accept selectively.** Defer large benchmarks, advanced graphics, images, tagged PDF, shared research cache and launch SLO tooling. Keep basic security, recovery, permissions, data provenance and privacy assessment before real testers. |
| No rights registry or DPIA until launch | **Reject blanket deferral.** Use a small checked-in permission manifest rather than a registry application. DPIA applicability depends on processing risk, not whether the product is public. [64] |
| Exhaustive DFS; remove competing solver choices | **Accept for bounded M0.** One deterministic Python engine and full encountered archive. Exactness still requires sound enumeration/pruning and actual completion; tens of options do not guarantee it. |
| Only complete/truncated statuses | **Qualify.** Use those for search coverage, with separate failure/cancellation/invalid-input states. Retain concise reproducibility and pruning metadata. |
| DBOS, then a jobs-table fallback after two hours | **Accept DBOS; reject automatic fallback.** A timebox can reveal a blocker but cannot validate equivalent durability, cancellation and duplicate-spend semantics. Revise deliberately if blocked. |
| Monthly grid is automatically conservative | **Reject as stated; accept a conservative monthly model.** Preserve exact dates, reserve touched months, use workload envelopes and prefund outflows. Month-end cash and averaged hours alone can falsely pass infeasible plans [TIME-1]. |
| Make course outcomes explicit | **Accept strongly.** Typed row mappings, assessment evidence, accountable owner and editable assumptions. Planned completion is not demonstrated skill [OUT-1]. |
| Toggle essential rows; readiness is all essential rows | **Accept with protected gates.** Preferences can change; statutory/admission/credential gates cannot be removed to obtain readiness. All edits version the target [RDY-1]. |
| Apply-now short circuit | **Accept.** Lead with current readiness and application checks; do not force training or a degenerate frontier. |
| ESCO and snippets replace full-posting sampling for M0 | **Accept with labelling.** Provisional matrix, actual sample counts, no specialist-review claim and no treating absent snippet words as absent requirements [MAP-1]. |
| ISCO spine and automatic resilience from two datasets | **Partly accept.** ISCO grouping and versioned joins; retain distinct ESCO roles. Reject lossless SOC assumptions and an automatic replacement score. M0 uses reviewed range records or unknown [TAX-1, AIR-1]. |
| Five personas and one worked trace | **Accept.** Deliver synthetic JSON fixtures and an executable arithmetic validator. Real-source extraction cases and deployed end-to-end testing remain explicit M0 gates, not falsely reported complete [TEST-1]. |
| Workspace cache, full-text retrieval, icons, simpler views | **Accept.** Fix these M0 choices. The simple dendrite remains in M0; richer motion/interaction and generated images remain M1. |
| These changes make a ten-day build certain | **Do not adopt.** Package/provider access, data rights, implementation capacity and integration tests still determine feasibility. A fixed scope supports estimation; it does not prove a duration. |

## Version 1.1 decisions retained as history

The table below records the prior review. **Where solver, renderer or workflow choices differ, v1.2 BND-1 and section 17 supersede them.** This history is not a menu of implementation alternatives.

| Feedback | Decision and resulting specification |
|---|---|
| Lost earnings belong in cost | **Accept with a definition.** The old direct-spend frontier was mathematically valid for that narrower objective, but incomplete for affordability decisions. Default to common-horizon economic cost; keep direct spending, cash and debt separate [FIN-1]. |
| Intake clones crowd the frontier | **Accept the problem, qualify the solution.** Group route structures, retain all materially efficient schedules. Different dates can change grants, earnings and feasible cost, so one schedule per structure is not always sufficient [ROU-1]. |
| Show scenario fragility and better-route margins | **Accept.** Keep base-case dominance distinct from scenario-wise dominance; add scenario ranges and named comparator margins. Ranges are not probabilities [VIS-2]. |
| Replace NSGA-II with exact minimal covers/CP-SAT | **Partly accept.** Use exact solving first on bounded qualified instances, retaining Rust for a demonstrated need. Minimal skill covers are not the whole planning problem; work/finance actions may be required for cash feasibility [OPT-1]. |
| Remove an option beaten by three other options | **Reject as stated.** Three mutually nondominated points can all dominate a point in F2. A proven three-link dominance chain is different. Any pruning must preserve the required first three layers [OPT-1]. |
| Use Adzuna, apprenticeship feeds, Skills England and Career Causeways | **Accept as optional regional adapters/research seeds.** Keep predicted salaries flagged and snippets incomplete. Skills England is England-specific; Career Causeways is archived research, not current worldwide feasibility evidence. Add native/global taxonomy contracts [GLO-1]. |
| Simplify scraping to one baseline | **Accept.** Scrapling plus permitted feeds is the baseline. Defer managed/browser-agent alternatives until a measured coverage or cost problem justifies them. No unrun benchmark establishes a fastest scraper. |
| Rename/rework AI Safety Score | **Accept with the user's scale retained.** AI Resilience Score uses 0-10 anchored ordinal bands, range first and lower-bound filtering. Reject uncalibrated weighted-sum or exposure-times-realisation probability claims [AIR-1]. |
| Earlier result and plain chapter names | **Accept.** You, Roles, Skills, Options, Routes, Plan; an early provisional sketch with conspicuous unknowns. It cannot promise a verified route in five minutes. |
| Replace user API keys with a hosted key | **Decline.** It conflicts with the explicit requirement. Improve setup and provide a synthetic demo; a funded mode needs a separate product decision. |
| Replace the dendrite, remove pulse/images, replace sliders | **Decline the removals.** Preserve requested features; add salary comparison, stable industry colours, calm mode and accessible controls. A quantitative trade-off view coordinates with the focused journey [VIS-1, VIS-2]. |
| SVG/D3 and DBOS simplify the architecture | **Accept conditionally.** Use them as the qualified baseline with replaceable ports. SVG needs accessibility/performance testing; DBOS does not automatically provide exactly-once external calls or eliminate an outbox [ARC-1]. |
| Ten to fifteen concierge users validate the product | **Accept for qualitative discovery only.** A small single-region study does not validate a global product or effectiveness claims. Require cross-region/language evaluation [GLO-1]. |
| “No competitor does this”; alternative services cost nothing | **Do not adopt.** No systematic comparison supports exclusivity or universal zero costs. Describe the actual product benefit without either claim. |
| Name may be confused with Nesta | **Accept as a brand risk.** Careerwright remains provisional; neither name availability nor infringement is established here. |
| Reduce repetitive qualifications | **Accept in structure.** Use canonical requirement IDs and linked acceptance conditions. Retain limitations that change the user's financial or career decision. |

The user's additional direction is incorporated through **personality-informed, evidence-grounded career suggestions [REC-1]**, **diverse multi-channel discovery beyond common-role templates [DIV-1]**, and a **global regional-capability contract [GLO-1]**. These additions do not increase the limit of three active target roles or require a personality test.

# 23 Research and source register

Sources were checked on **26 October 2026**. References retained for earlier decision history are not selected dependencies; section 17 is the authoritative stack. Provider capabilities, prices, model identifiers, programme eligibility and software APIs are time-sensitive. Verify them again when implementing or making a real expenditure. The following are primary research, official statistics, official documentation or upstream source repositories. A supplier's benchmark or feature description is not an independent comparative evaluation.

**[1] Meta — [Model catalogue](https://dev.meta.ai/docs/models).** Current API model identifiers, capability and availability distinctions. The specification pins observed choices rather than assuming the Llama family is still Meta's latest offering.

**[2] Meta — [Pricing and rate limits](https://dev.meta.ai/docs/pricing-rate-limits).** Standard/Contributor policy and published token, search and image prices used in the illustrative calculation. Actual access, charges and retention terms require verification.

**[3] Meta — [Structured output](https://dev.meta.ai/docs/structured-output).** JSON-schema controls and supported constraints. Structural compliance does not verify the truth of extracted facts.

**[4] Pydantic AI — [Output documentation](https://pydantic.dev/docs/ai/core-concepts/output/).** Typed output modes and validation patterns for bounded interview proposals.

**[5] Firecrawl — [Scrape documentation](https://docs.firecrawl.dev/features/scrape).** Supported retrieval formats and rendered-page extraction. Background for a deferred managed challenger; not a baseline dependency.

**[6] Firecrawl — [Pricing](https://www.firecrawl.dev/pricing).** Published plan and credit rules; no application-specific cost benchmark has been run.

**[7] Crawl4AI — [Official documentation](https://docs.crawl4ai.com/).** Python crawling/extraction and self-hosted/cloud options. A potential challenger, not an evaluated production dependency.

**[8] Browser Use — [Pricing](https://browser-use.com/pricing).** Browser, traffic and hosted-agent charge components. The comparison deliberately avoids equating browser-hour price with cost per correct record.

**[9] Meta — [Search grounding](https://dev.meta.ai/docs/search-grounding).** Search-assisted research capability; it does not replace a versioned opportunity database.

**[10] moors / moo-rs — [Upstream repository](https://github.com/andresliszt/moo-rs) and [Rust API](https://docs.rs/moors/latest/moors/).** Rust multiobjective algorithms and Python bindings. Historical v1.0-v1.1 candidate; not a v1.2 runtime dependency.

**[11] nsga-rs — [Upstream repository](https://github.com/s-simoncelli/nsga-rs).** Historical solver comparator; not a v1.2 runtime dependency. Older [optirustic documentation](https://docs.rs/crate/optirustic/latest) points to the successor project.

**[12] Google OR-Tools — [CP-SAT model and response contract](https://github.com/google/or-tools/blob/stable/ortools/sat/cp_model.proto).** Solver status, bounds and termination semantics relevant to exactness claims. A status must be interpreted with the model and gap settings.

**[13] moo-rs — [Metrics documentation](https://andresliszt.github.io/moo-rs/user_guide/metrics/metrics.html).** Multiobjective quality indicators used to inform the proposed benchmark. A common reference set and objective normalisation remain our responsibility.

**[14] Australian Journal of Career Development — [2025 adult career-development scoping review](https://journals.sagepub.com/doi/10.1177/10384162251345595).** Adult intervention evidence, approaches and limitations; heterogeneous research does not validate this application.

**[15] Journal of Career Assessment — [2026 online career-counselling meta-analysis](https://journals.sagepub.com/doi/10.1177/10690727261433253).** Published abstract reviewed; full text was not available in this research session. Used only for the qualified high-level finding described in section 4.

**[16] O*NET Resource Center — [Interest Profiler](https://www.onetcenter.org/IP.html) and [technical manual](https://www.onetcenter.org/reports/IP_Manual.html).** Interest assessment and instrument guidance. Altered conversational items must not be presented as the validated instrument.

**[17] Office for National Statistics — [Employee earnings in the UK: 2026](https://www.ons.gov.uk/releases/employeeearningsintheuk2026).** Official earnings release, including published geography/occupation tables and reliability qualifications.

**[18] Skills England — [Annual skills report 2026](https://assets.publishing.service.gov.uk/media/6a47c33a045e1108aaa5eb48/Skills_England_annual_skills_report_2026.pdf).** Sector and skills-demand context; not a universal city-level projection.

**[19] US Bureau of Labor Statistics — [Employment projections concepts](https://www.bls.gov/emp/factsheets/concepts.htm) and [programme](https://www.bls.gov/emp/).** Distinctions among employment change, occupational openings and projection vintages.

**[20] International Labour Organization — [Generative AI and Jobs: A Refined Global Index of Occupational Exposure](https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure), 2025.** Task-based exposure methodology; exposure and possible transformation are not individual replacement probabilities. DOI: 10.54394/HETP0387.

**[21] European Commission — [ESCO web-service API](https://esco.ec.europa.eu/en/use-esco/use-esco-services-api/esco-web-service-api).** Occupation/skill taxonomy access. Pin a tested release and reconcile mappings rather than assuming cross-taxonomy equivalence.

**[22] O*NET Resource Center — [Database releases](https://www.onetcenter.org/db_releases.html).** Versioned occupational data, release history and licence context.

**[23] Greenhouse — [Job Board API](https://docs.greenhouse.io/job-board.html).** Public job-board GET endpoints and payloads. Technical access alone does not settle downstream reuse rights.

**[24] GOV.UK — [Free courses for jobs](https://www.gov.uk/guidance/free-courses-for-jobs).** Example official discovery source for England; individual eligibility must be checked against current rules.

**[25] GOV.UK — [Advanced Learner Loan](https://www.gov.uk/advanced-learner-loan).** Example financing scheme. Loans require separate eligibility, cash-flow and repayment treatment.

**[26] GOV.UK — [Find an apprenticeship](https://www.gov.uk/apply-apprenticeship).** Official entry point for discovering apprenticeship vacancies and the appropriate national service.

**[27] PixiJS — [Introduction](https://pixijs.com/8.x/guides/getting-started/intro).** Historical renderer candidate; not selected in v1.2.

**[28] D3 — [Force simulation](https://d3js.org/d3-force).** Layout primitives. The product adds stable anchors, worker execution and interaction constraints.

**[29] W3C — [Reduced-motion technique C39](https://www.w3.org/WAI/WCAG22/Techniques/css/C39) and [Pause, Stop, Hide](https://www.w3.org/WAI/WCAG21/Understanding/pause-stop-hide.html).** Motion accessibility guidance; complete WCAG conformance requires broader testing.

**[30] Temporal — [Workflow execution](https://docs.temporal.io/workflow-execution).** Durable workflow concepts. Business idempotency, data minimisation and external-call semantics still require explicit design.

**[31] Information Commissioner's Office — [What is special category data?](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-is-special-category-data/).** Guidance relevant to sensitive health information and inferences. This specification is not a determination of regulatory compliance.

**[32] US Office of Personnel Management — [Structured interviews](https://www.opm.gov/policy-data-oversight/assessment-and-selection/structured-interviews/).** Behavioural questions and consistent rating principles. This does not validate Careerwright's adaptive self-assessment as a hiring test.

**[33] Pydantic AI — [OpenAI-compatible models](https://pydantic.dev/docs/ai/models/compatible-apis/).** Provider/profile configuration and compatibility limits. “Compatible endpoint” is not evidence that all features behave identically.

**[34] Scrapling — [Upstream repository](https://github.com/D4Vinci/Scrapling).** Licence, Python fetch/parse/browser/crawler features and entry points. Primary proposed scraper at the user's request.

**[35] Scrapling — [MCP server](https://scrapling.readthedocs.io/en/latest/ai/mcp-server.html).** Agent-facing access; production exposes narrower, policy-controlled tools.

**[36] Scrapling — [Adaptive parsing](https://scrapling.readthedocs.io/en/latest/parsing/adaptive.html).** Element relocation behaviour and limitations; candidate relocation does not establish semantic correctness.

**[37] Scrapling — [Benchmark source](https://github.com/D4Vinci/Scrapling/blob/main/benchmarks.py).** Synthetic parser benchmark implementation. Its timings do not establish whole-system job-record accuracy, browser success or production economics.

**[38] Scrapling — [Spider architecture](https://scrapling.readthedocs.io/en/latest/spiders/architecture.html).** Scheduling, checkpoints and crawler controls, including the need to enable and instrument source-policy handling.

**[39] Meta — [Image generation](https://dev.meta.ai/docs/image-generation).** Image capability for decorative step illustrations, subject to key access, region, cost and policy.

**[40] Pydantic AI — [Temporal integration](https://pydantic.dev/docs/ai/capabilities/durable_execution/temporal/).** Durable-agent integration and execution boundary. A transient HTTP call does not automatically become a durable workflow.

**[41] Anthropic — [Labor market impacts of AI: A new measure and early evidence](https://www.anthropic.com/research/labor-market-impacts), 5 March 2026.** Distinguishes theoretical capability from observed use and examines early labour outcomes. Platform usage is a partial view of adoption, not a universal replacement forecast.

**[42] Stanford Digital Economy Lab — [August 2026 revision of Canaries in the Coal Mine](https://digitaleconomy.stanford.edu/news/canariesaug26/).** Updated payroll-based patterns, entry-level hiring and methodological cautions. The authors explicitly distinguish descriptive patterns from causal estimates.

**[43] ILO — [International Standard Classification of Occupations, ISCO-08](https://researchrepository.ilo.org/esploro/outputs/book/International-Standard-Classification-of-Occupations-ISCO-08/995673746502676).** International comparison framework, not a substitute for native occupational classifications or local market evidence.

**[44] European Commission — [ESCO overview and multilingual scope](https://employment-social-affairs.ec.europa.eu/policies-and-activities/skills-and-qualifications/skills-jobs/european-skillscompetences-qualifications-and-occupations-esco_en).** Multilingual occupational/skills terminology; language availability does not imply worldwide labour-market coverage.

**[45] Employment and Social Development Canada — [National Occupational Classification and OaSIS](https://www.canada.ca/en/employment-social-development/services/noc.html).** Canadian occupational information and classification resources, illustrating a native-country adapter.

**[46] Australian Bureau of Statistics — [Occupation Standard Classification for Australia](https://www.abs.gov.au/statistics/classifications/osca-occupation-standard-classification-australia).** OSCA classification/version information; pin the applicable native release.

**[47] Directorate General of Employment, India — [National Classification of Occupations](https://www.dge.gov.in/national_classification_of_occupations).** Native occupation taxonomy, including locally specific titles; classification membership is not a verified vacancy.

**[48] Brazil Ministry of Labour and Employment — [Classificação Brasileira de Ocupações](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/cbo).** Native occupational reference. Classification and regulation of a profession are distinct.

**[49] South Africa DHET — [Skills Development resources](https://www.dhet.gov.za/SitePages/SkillsDevelopmentNew.aspx) and [2024 government skills-list publication](https://www.gov.za/sites/default/files/gcis_document/202404/50510gen2414.pdf).** Examples of OFO-coded occupational evidence. Verify release availability and dates rather than assuming the current year has a new classification.

**[50] Skills England — [Occupational Maps public API](https://occupational-maps.skillsengland.education.gov.uk/public-api/).** Occupational standards, duties and knowledge/skills/behaviours; API access and reuse conditions apply. England's standards are a regional input, not global licensing requirements.

**[51] Adzuna — [Search API](https://developer.adzuna.com/docs/search) and [salary data](https://developer.adzuna.com/docs/salary).** Search fields, salary-prediction flag, snippet limitations and aggregate salary endpoints. Check country coverage, licence and pay basis before use.

**[52] UK apprenticeship service — [Display Vacancy Advert API](https://www.api.gov.uk/tas/display-vacancy-advert-api/) and [developer portal](https://developer.apprenticeships.education.gov.uk/).** Official vacancy feed and access/version guidance. Country/service boundaries and current vacancy status remain material.

**[53] Nesta — [Mapping Career Causeways repository](https://github.com/nestauk/mapping-career-causeways) and [user guide](https://www.nesta.org.uk/toolkit/mapping-career-causeways-user-guide/).** Reusable occupation-transition research; repository archived on 12 October 2022. Useful for candidate generation, not proof of current local transition feasibility. Check data artefact rights separately from code licence.

**[54] Hoff et al. — [Interest fit and job satisfaction: a systematic review and meta-analysis](https://www.sciencedirect.com/science/article/pii/S0001879120301287), 2020.** Modest association supports treating interests as one input, not a destiny rule. Interests and personality are related but different constructs.

**[55] Salinas et al. — [The Unequal Opportunities of Large Language Models: Revealing Demographic Bias through Job Recommendations](https://arxiv.org/abs/2308.02053), 2023/2024.** Job-recommendation bias evidence on the studied models. It motivates evaluation; it does not establish the behaviour of a current Meta release.

**[56] Lichtenberg et al. — [Large Language Models for Recommendations: Are They Really Prone to Popularity Bias?](https://arxiv.org/abs/2406.01285), 2024.** Domain-specific recommendation findings caution against assuming that all LLMs inherently increase popularity bias. Careerwright must measure its own career slates.

**[57] DBOS — [Python workflow tutorial](https://docs.dbos.dev/python/tutorials/workflow-tutorial).** Durable workflows, steps and transaction semantics; step retry does not establish exactly-once external effects.

**[58] Pydantic AI — [DBOS durable execution](https://pydantic.dev/docs/ai/capabilities/durable_execution/dbos/).** Integration and lifecycle contract; pin compatible releases and validate cancellation, recovery and data handling.

**[59] Pydantic AI — [Meta models](https://pydantic.dev/docs/ai/models/meta/).** Native Meta integration and provider restrictions, including tool choice. Verify supported native structured output for the chosen model/version.

**[60] European Commission - [ESCO occupation structure](https://esco.ec.europa.eu/en/classification/occupation_main) and [essential/optional skill relationships](https://esco.ec.europa.eu/en/about-esco/escopedia/escopedia/two-pillar-structure-esco).** ESCO URI identity, ISCO hierarchy and expert-curated relationship semantics; no implied proficiency scale.

**[61] ONS - [SOC 2020 to ISCO-08 mapping methodology](https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/classifyingthestandardoccupationalclassification2020soc2020totheinternationalstandardclassificationofoccupationsisco08) and [SOC 2020 coding index](https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/soc2020volume2codingrulesandconventions).** The published material explicitly describes split mappings and title-level coding; a simple lossless group join is not warranted.

**[62] US Bureau of Labor Statistics - [2010 SOC/ISCO crosswalks](https://www.bls.gov/soc/soccrosswalks.htm) and [2018 SOC crosswalks](https://www.bls.gov/soc/2018/crosswalks.htm).** Distinguish US classification versions from UK SOC 2020 and verify each bridge.

**[63] O*NET - [ESCO crosswalk reference](https://services.onetcenter.org/reference/online/crosswalk/esco) and European Commission [ESCO/O*NET mapping resources](https://esco.ec.europa.eu/nb/use-esco/other-crosswalks).** Version-specific correspondences, not proof of role equivalence or current regional demand.

**[64] ICO - [When do we need to do a DPIA?](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/when-do-we-need-to-do-a-dpia/).** Risk-based pre-processing requirements and screening factors. Guidance is under review following legislative change; this spec does not determine legal compliance.

**[65] Get careers information and advice - [Accessing free training and courses](https://nationalcareers.service.gov.uk/careers-advice/accessing-free-training-and-courses).** Official discovery route for free courses and Skills Bootcamps; verify actual local programme and learner conditions.

**[66] GOV.UK - [Advanced Learner Loan eligibility](https://www.gov.uk/advanced-learner-loan/eligibility), [2026-2027 funding rules](https://www.gov.uk/government/publications/advanced-learner-loans-funding-and-performance-management-rules/advanced-learner-loans-funding-and-performance-management-rules-2026-to-2027) and [post-16 funding approval rules](https://www.gov.uk/guidance/qualification-funding-approval/post-16-pathways-reform).** Course/start-date/provider interactions with LLE require current verification; a single date-only rule is insufficient.

**[67] Anthropic - [Economic Index](https://www.anthropic.com/economic-index) and [initial task-mapping methodology](https://www.anthropic.com/news/the-anthropic-economic-index).** Observed Claude task use mapped to O*NET, with sampling and coverage limits; not a calibrated replacement probability.

**[68] Google Cloud - [Cloud Run overview](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run).** Container web-service hosting reference. The selected deployment still needs tested worker, database, secrets and regional configuration.

**[69] Firebase - [Verify ID tokens](https://firebase.google.com/docs/auth/admin/verify-id-tokens).** Backend token-verification contract. Invitation, workspace ownership and the chosen revocation checks remain application responsibilities.

The proposed ordinal anchors, diversity policy, refresh intervals, performance budgets, interface design and acceptance thresholds are original specification choices. They require qualification against representative users and data; citations do not turn those choices into validated findings.
