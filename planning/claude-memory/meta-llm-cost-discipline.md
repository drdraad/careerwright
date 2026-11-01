---
name: meta-llm-cost-discipline
description: "Nessa project — track Meta LLM credits/costs; cheap models for testing, top model only for production paths"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 215e3a32-af56-4146-900e-11d9bbf0dae9
  modified: 2026-10-31T08:11:35.032Z
---

Keep careful track of Meta LLM credits and costs during testing. Use live calls sparingly; confirm things work with cheaper Meta models; reserve the most performant model for production paths only (plus the minimum calls needed to qualify it).

**Why:** The user pays for Meta API usage with their own key (META_API_KEY in the project .env) and asked for this explicitly on 2026-10-27 while the L0 build was starting.

Update 2026-10-31: "We can also start being a bit more generous with token use in human testing - I would like to use muse wonder for this." So human testing sessions (the product owner using the live product) may use `muse-wonder-1.0` with a more generous budget; ADR 0003 had left it unselected, so Task A1 works out where, the per-session budget and the ledgering. Automated tests and checks still use the cheap test model.

**How to apply:** Make model choice configuration (test vs production model). Log every live call (model, tokens, estimated cost, running total) in docs/evidence/live-usage.md. Keep live calls out of default check/acceptance commands. Relates to [[nessa-l0-build]].
