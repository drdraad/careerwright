---
name: nessa-l0-build
description: Careerwright (formerly Nessa) L0 local build — autonomous sprint execution via Opus subagents; ledger location, branch, folder and remote
metadata:
  node_type: memory
  type: project
  originSessionId: 215e3a32-af56-4146-900e-11d9bbf0dae9
  modified: 2026-11-01T09:41:42.028Z
---

Started 2026-10-27: implementing the L0 local development plan (Sprints 0–9) autonomously, one Opus 5.5 implementer subagent per task plus an independent reviewer per task (subagent-driven-development).

- Renamed Nessa → Careerwright on 2026-10-30 (product owner's call), code included: package `careerwright`, env `CAREERWRIGHT_*`, home `~/.careerwright/l0`. On 2026-11-01 the root folder became `/Users/darianraad/Code/careerwright` (was `careerpathoptimizer`) and the two Nessa-named files were renamed; CLAUDE.md lists where the old name deliberately stays. The product owner's "living world" ambition governs the UI (plan section 4, ADR 0014, CLAUDE.md "The experience"); they were angry the first prototype was bland ("I would fire whoever put this prototype in front of me"). Counterweight, 2026-10-31: "The visuals are important, but they must be subservient to having a practical, useful product."
- Speed, 2026-11-01: "I'm finding this development process too slow." They adopted R16 (one reviewer, one fix round max, full checks once per piece, up to three implementers). Keep messages short, decisions batched, and don't add ceremony.
- Branch `l0-local-release`; `main` holds the source docs plus GitHub's LICENSE/README. Remote `origin` = `git@github.com:drdraad/careerwright.git` (public, account drdraad). Push only when the user asks; merge is the user's call.
- Task breakdown and standing rulings R1–R16: `docs/plan/l0-sprint-tasks.md` (plan v1.6 adds the school-leaver tasks 6f, 12c, 7f).
- Recovery ledger: `planning/progress.md` (in the repository since 2026-11-01, with every dispatch, report and review) — trust it plus `git log` after compaction; never re-dispatch tasks marked complete.
- Fresh-session handover prompt: `planning/handover-2026-11-01.md` (supersedes `handover-2026-10-31.md`).

**Why:** the build spans many sessions/compactions; the ledger prevents re-running finished sprints.

**How to apply:** on resume, read the handover and the ledger first, then continue at the first task without a `complete` line. See [[meta-llm-cost-discipline]], [[users-without-work-history]].
