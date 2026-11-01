# Task A1 question 4: Muse Wonder for human testing (controller's notes)

## Facts (with evidence)
- Registry: `muse-wonder-1.0` is listed, Standard mode, price $4.00 / $0.20 cached / $20.00 out
  per million tokens, **no qualified capabilities**, evaluation "not evaluated"
  (`backend/src/careerwright/identity/model_registry.py:83`). The registry's own rule: "a model
  listed but never called has none (being listed does not prove it can be called)" (:49-50).
- ADR 0003: "Not selected: Muse Wonder (M1 in the specification; no escalation in L0)"
  (`docs/adr/0003-meta-model-selection.md:66`); listed as "Preview" (:35).
- Spec section 16 (`Careerwright_Product_Specification.md:951-953`): M0 uses the pinned Spark
  model for all text tasks, no automatic escalation; M1 adds "a tested Wonder escalation
  policy for difficult synthesis"; "Never make a more expensive model call merely to decorate
  the experience." Also: Muse Wonder Full is not on the Model API and must not appear as a key
  option. Register: Muse Wonder escalation is M1 (`docs/requirements-register.md:668`).
- Mechanism already exists: the production model is configuration,
  `CAREERWRIGHT_META_PRODUCTION_MODEL` (`backend/src/careerwright/config.py:90`,
  `compose.yaml:21`). `ModelChoice.configure` refuses a non-Standard production model
  (`identity/model_choice.py:52-54`); Wonder is Standard, so it passes. Non-synthetic
  workspaces always use the production model (`model_choice.py:62-65`). So "Wonder for the
  product owner's live sessions" = start the session's stack with the production model set to
  `muse-wonder-1.0`. Synthetic workspaces keep the cheap Contributor test model; the database
  CHECK and the activity's refusal are unchanged.
- Spend caps: default per-run cap $0.15, sized for Spark's interview-turn worst case of $0.049
  times three attempts (`config.py:120-125`); default monthly cap $1.00 (`config.py:126-130`).
  Wonder's prices are 3.2x (input) and 4.7x (output) Spark Standard, so an interview turn's
  worst case is about $0.22 and three attempts about $0.66: **every Wonder interview turn
  would be refused as over budget** under the defaults. Caps are per workspace and settable
  through the API (`identity/spend_limits.py`), or as defaults by environment.
- Ledgering: `docs/evidence/live-usage.*` is written only by the explicit live commands
  (`backend/tools/live_smoke.py`, `live_eval.py`, `live_adzuna.py`, `usage_ledger.py`). Calls the
  product makes during a person's live use are recorded in the product database (run
  attempts with usage and cost, `identity/spend.py`) but **not** copied to the evidence ledger.
  R5 says every live call is ledgered; the product owner's own sessions have not been live
  so far (all 35 ledgered calls are tooling).
- Real token counts on Spark (ledger rows 13-31): interview turn ~1,130-1,430 in, ~410-820 out;
  with a repair ~3,800 in / 1,135 out; discovery ~530 in / ~600 out; slate explanation
  ~2,750 in / 1,320 out; source search 3,400-9,000 in / 400-900 out + 1-2 searches; extraction
  ~700 in / 460 out.

## Estimates on Wonder (USD, from the counts above; not measured)
- Interview turn ~$0.02 (with a repair ~$0.04). Discovery ~$0.014. Slate explanation ~$0.04.
  Source search ~$0.03-0.06. Page extraction ~$0.012.
- A 2-hour session (about 40 turns, 3 discoveries and explanations, 5 searches, 5 extractions,
  a few strength runs): about $1.50-2.00. A cap of $5 per session leaves room for repairs and
  retries; per-run cap about $0.75.

## What would need to change (for the plan)
1. Qualify Wonder: two live calls on synthetic input (schema output with usage; streaming +
   web search + schema), like Spark's calls 6-7, then a live-eval set (at most 6 cases) on
   Wonder. Record capabilities in the registry. The live-smoke production cap (worst case
   at most $0.10 per invocation) is sized for Spark: it needs a Wonder-sized cap.
   Estimated cost: under $0.50 in all.
2. ADR 0003 amendment: Wonder selected as the production model for the product owner's
   live testing sessions only (not an escalation policy, not automatic); Spark stays the
   release default unless the product owner later decides otherwise.
3. Spec/plan/register: record the pull-forward of an M1 item as a decided change for human
   testing (the spec's "never decorate" line is honoured: the purpose is the quality of
   suggestions the product owner judges).
4. A session command (e.g. `make session` / `make dev MODEL=wonder`) that starts the stack with
   Wonder, sets the workspace caps (run ~$0.75, session/month ~$5), and afterwards copies the
   session's attempt rows (model, run kind, tokens, cost, state; never content) into
   `docs/evidence/live-usage.*` with a session scope. Unknown costs count their full
   reservation.
5. Tests: the model-choice rule and caps with Wonder configured (offline); no change to the
   test-model safeguards; automated checks never call a model.

## Reading of "human testing"
Most likely: the product owner using the live product in their review sessions (live-assisted
workspace, their own data, their key). Confirm in the summary rather than ask up front.
