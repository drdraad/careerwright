# Carried into Task 4 (from Task 2 review)
- Phone bottom sheet: "More" buttons ship aria-expanded="false" with no behaviour; expanded height and swipe behaviour are undesigned. Design and implement them (keyboard + screen reader correct).
- Conversation failure state: Send button stays filled beside the primary "Try again" — keep one primary action per state.
- Gantt aria-label in the route composition hard-codes route-B-specific wording ("evening course", "current job kept throughout"); generate from data when implemented (Task 14).
- Layers 2 and 3 share one grey and differ by shape + label; a human reviewer (H-02) may want a second grey.

# Carried into Task 4 (from Task 3 — platform interfaces)
- The OpenAPI schema is served by the API at `/openapi.json` (see `backend/tools/stack.py`); generate the TS client from it and make the generation reproducible (a committed generated client under `**/generated/**`, plus a check that fails on drift). Enums come only from the generated client (`backend/src/careerwright/vocabulary.py`).
- `compose.yaml` already has a `web` service slot (profile `web`, build `./apps/web`) and the edge relays `3000=web:3000`. The edge connects only to addresses inside the internal subnet, and the API guard returns 403 to clients outside loopback/the internal subnet — the web container must sit on the `internal` network. Same-origin routing of API/events through the web origin must keep the API's Host/Origin checks meaningful (do not disable them; extend the allowlist only to the web origin on 127.0.0.1).
- BND1-11 (demo mode makes no outbound request) is `planned` with the T3 part verified: Task 4 adds the web container and extends the stack probe to it, then closes the row.
- Error envelope: typed codes derived from status (`backend/src/careerwright/api/envelope.py`), correlation id header `x-correlation-id`, distinct `CREDENTIAL_REVOKED` (409), `METHOD_NOT_ALLOWED` (405). The UI maps codes to the status vocabulary; it never shows raw messages.
- Status events: SSE in `backend/src/careerwright/api/routes_events.py`; it re-checks the token and ends on revocation/expiry — the UI's reconnect path must re-authenticate rather than loop.
- Seeded identities live in `docker/auth/seed/`; the emulator image installs from a committed pnpm lockfile (`docker/auth/`).
