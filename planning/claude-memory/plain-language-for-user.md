---
name: plain-language-for-user
description: "The user wants plain, everyday language with minimal cognitive load in everything they read; dense agent prose (codes, jargon) is unacceptable"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 97b1e108-19c9-45e9-9fd3-f372d0f9e9b6
  modified: 2026-10-29T19:22:55.882Z
---

Write everything the user reads in plain, everyday English, the way a normal engineer or colleague talks: short sentences, common words, no internal codes (task, ruling, gate, ADR IDs) unless they need one to act, money in pounds, and the action first.

**Why:** On 2026-10-29 the user opened the session 2 review guide and called it "absurdly difficult to read", "Aliens more like", "This was nuts!". They asked for KISS and had a "Talking to the user" section added to the project CLAUDE.md.

**How to apply:** Applies to chat replies and to every user-facing file an agent writes (review packages, question sets, decision sheets, reports). Put plain-language requirements in subagent dispatches for user-facing docs. Before sending, reread as someone who has never seen the code. Related: [[nessa-l0-build]].
