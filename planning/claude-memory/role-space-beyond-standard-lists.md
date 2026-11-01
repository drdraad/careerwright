---
name: role-space-beyond-standard-lists
description: Careerwright product owner requires suggestions not limited to a prefilled job list (ESCO); LLMs and deep research should fill out the role space like an all-knowing career coach
metadata:
  node_type: memory
  type: project
  originSessionId: e3bcee60-3128-4a91-bb65-a14bf9244c20
  modified: 2026-10-31T08:29:24.448Z
---

On 2026-10-31 the product owner said, verbatim: "One thing that is really important to me is that we aren't limited to a prefilled list of roles - the real world is much more complex than those standardised job lists, and I want to avoid the frustration of your ideal job not appearing as an option to select. This is where deep research and LLMs have a part to play to fill out the "role space" more fully. I want it to feel like you have an omniscient career coach who knows all possible jobs that could fit you."

**Why:** the built discovery suggests only ESCO occupations (ADR 0007: the model proposes searches only; the slate is deterministic code over ESCO), and several test personas got empty slates because their titles are not ESCO titles. The product owner sees that as the core frustration to avoid.

**How to apply:** treat "my ideal job can appear even if no standard list holds it" as a top-level product requirement when planning or reviewing discovery, the opportunity map and targets. Keep the honesty rules (verified evidence, nothing implies a job offer), but don't let them shrink the role space back to the list. Changing ADR 0007 and the CLAUDE.md discovery invariant needs the product owner's explicit approval. Raised during the whole-solution audit (Task A1); see [[nessa-l0-build]] and [[meta-llm-cost-discipline]].
