# ADR 0005: The web app, its toolchain and same-origin access to the API

- Status: Accepted (Task 4, Sprint 1; evidence: `make check`, `make acceptance`). Decision 1's
  provisional age exception for Next.js 16.4.1 was removed in Task 6c (2026-10-28).
- Date: 2026-10-28
- Requirements: S1.4, S1.5, ARC1-01/03/10, BND1-11/12/13, UI-04/05/06/09/11, STATE-01/07,
  DUR-03, SEC-04; Global Constraints 2, 9, 10 and 11

## Context

Sprint 1's shell (`apps/web`) is the first JavaScript product code. Spec section 17 fixes
React, TypeScript and Next.js, Tailwind tokens, Radix controls and TanStack Query. The plan
asks for one JS lint/format toolchain, a TypeScript client generated from FastAPI's OpenAPI
contract, API and events routed through the web origin, and a fixture adapter that supplies
labelled content without any component hard-coding financial examples. ADR 0004 fixes the
loopback boundary the web service must join without weakening.

## Decisions

1. **Versions** (all in `docs/dependencies.md`, each at least 14 days old, enforced by
   pnpm's `minimumReleaseAge`). Next.js 16.4.1, React 19.3.0, TypeScript 6.0.3,
   Tailwind CSS 4.3.3, Radix Dialog and Popover 1.3.1, TanStack Query 5.104.2, and the
   Firebase JS SDK as `@firebase/app` 0.16.3 and `@firebase/auth` 1.13.7.
   - **No exception to the 14-day rule.** Next.js 16.4.1 was pinned at 13.5 days old under a
     provisional exception, because every older 16.x is affected by GHSA-2464-fhr4-w9xw and
     GHSA-673q-mjm6-r5xr (critical) and GHSA-p3m5-59mp-jv5r (high). It turned 14 days old
     at 2026-10-28T17:43Z, and Task 6c removed the exception the same day:
     `minimumReleaseAgeExclude` is gone from `apps/web/pnpm-workspace.yaml`, and
     `pnpm install --frozen-lockfile` passes with the lockfile unchanged.
   - **TypeScript 6, not 7.** TypeScript 7 ships no JavaScript compiler API; the client
     generator uses it. 6.0.3 is the newest release that has it. Next.js type-checks with it.
   - **The Firebase packages, not the `firebase` umbrella.** Only app and auth are used; the
     umbrella also installs Firestore's gRPC stack (with a high-severity advisory) for code
     the app never loads.

2. **One lint and format toolchain: Biome 2.5.15.** One tool formats and lints TypeScript,
   React and Next.js code (its `next`, `react` and `test` rule domains). ESLint plus
   Prettier would be two tools, and Next.js 16 no longer ships `next lint`. Generated and
   mirrored files are excluded.

3. **The client generator: `@hey-api/openapi-ts` 0.99.0**, emitting types, enums as runtime
   objects and an SDK with its fetch client bundled (no runtime dependency). Rejected:
   `openapi-typescript` 7.13.0 with `openapi-fetch`, whose peer range stops at TypeScript 5.
   - The document comes from `backend/tools/openapi.py`, which builds exactly what the API
     serves at `/openapi.json` without a database or keys, so generation runs offline.
     Both the document and the client are committed under `apps/web/src/generated/`.
   - Drift fails three ways: `pnpm run check` regenerates and compares (in `make check`),
     `tests/api/test_openapi.py` compares the committed document with the backend, and a
     stack test compares it with what the running API serves.
   - API operations now have named IDs (`get_profile`, `put_profile`, ...), so the SDK's
     function names are readable. Only the `operationId` values changed in the contract.
   - Enums, money and error codes reach the UI only from this output. The UI's own tables
     (`src/lib/vocabulary.ts`) are `Record<GeneratedEnum, ...>`, so a new API value fails
     the type check until it has words.

4. **Same-origin API access.** The browser calls `/api/v1/*` on the web origin; a Next.js
   route handler forwards it to `http://api:8000/v1/*` on the internal network. The API's
   checks stay meaningful and its allowlists are unchanged:
   - **Origin:** the browser's Origin header is forwarded unchanged and never added, so the
     API still refuses a foreign origin and a state-changing request without one.
   - **Host:** the web server checks the browser's Host against `CAREERWRIGHT_WEB_ALLOWED_HOSTS`
     (`src/proxy.ts`), so DNS rebinding is refused at the web origin. The proxied Host is
     `api:8000`, which the API already allowed.
   - **Client address:** the web container is on the internal subnet, which the API already
     serves (ADR 0004 decision 2), and the web container is reachable only through the
     edge on 127.0.0.1.
   - **What passes:** only the headers the contract uses. Cookies and forwarding headers
     do not.
   - **Unreachable API:** a 502 without an envelope, which the UI reports as unreachable,
     never as an API error.
   - **Content-Security-Policy:** connections, scripts, fonts and images may come only from
     the web origin and the Auth emulator. The page cannot make an external request even by
     accident.
   - **No telemetry:** Next.js and Storybook telemetry are off (Makefile, Dockerfile,
     Storybook config).

5. **Status events.** EventSource cannot send an Authorization header, so the stream is
   read with `fetch` and parsed (`src/lib/sse.ts`).
   - **Resume:** every reconnect sends `Last-Event-ID`, the last event the page received. A
     newly opened page starts after the workspace's `last_event_seq` (returned with the
     workspace), so a reopened page neither replays old events nor misses new ones.
   - **"Live" means delivered:** the status turns Live when the first bytes of the stream
     reach the page through the web origin (the API sends a `retry:` frame at once), not
     when the response headers arrive. A browser test checks that a change saved by another
     client reaches an open page within 5 s without a reload.
   - **Stopped:** the status is shown on every screen size, so a phone also says when
     updates have stopped. Reconnect is offered only after a failed re-authentication, the
     one stop that trying again can cure; it shows Connecting at once.
   - **Re-authentication:** `event: reauthenticate` reconnects at once with a force-refreshed
     token. Signed out, or a fresh token sent back again within 10 s with nothing delivered,
     stops the stream with a stated reason instead of looping.
   - **Access ends:** `stream_ended` with NOT_INVITED or NOT_FOUND, or a 403/404 envelope,
     stops it for good.
   - **Transport failures:** they back off from the server's retry interval (never below
     1 s), doubling, capped at 30 s.
   - **What events do:** they only invalidate queries; the API's resources stay authoritative.
     A refresh that fails while the API restarts keeps what was last loaded and says so in
     the strip.

6. **The fixture adapter runs in the web server.** It reads the supplied TRACE-01 file,
   mounted read-only, and checks it against the pinned SHA-256 before anything reaches a
   page.
   - A missing, altered or non-synthetic file is a typed `failed` result, never an empty
     preview.
   - The shell shows the preview only in the named fixture workspace, labelled "Fixture
     preview: not your routes". Other workspaces show an explained empty state, so a
     fixture never fills a live workspace.
   - The adapter computes nothing. Layers are the fixture's `expected.fronts`, and figures
     are the fixture's own: ranks and affordability belong to deterministic Python.

7. **The design system is mirrored, not forked.** The web image's build context is
   `apps/web`, so `src/design/` holds byte-identical copies of `docs/design/tokens/tokens.css`
   and the two fonts with their OFL texts. A test fails if they differ.
   - The Tailwind theme is reset and rebuilt from the semantic tokens: no default palette,
     spacing or radius exists.
   - The shell's component classes port the reviewed `shell.css`.
   - The icon set is the project's own glyphs from the Sprint 0 references (no third-party
     licence), extended with the interface glyphs the shell needs in the same construction.

8. **Phone evidence sheet (carried from the Task 2 review).** It opens at the 212 px peek.
   - "More" toggles the full height (the viewport less 72 px) and becomes "Less", with
     `aria-expanded` and `aria-controls`.
   - Dragging the handle up or down by 40 px does the same, and dragging down from the peek
     closes it. The handle is hidden from assistive technology because the button already
     does everything it does.
   - The sheet is non-modal like the desktop drawer. Escape or Close dismisses it, and
     focus returns to the control that opened it.

9. **Browser storage.** The Firebase SDK keeps the emulator session in IndexedDB
   (`indexedDBLocalPersistence`, set explicitly). A browser test checks that the session is
   in IndexedDB and that no `firebase:` key is in `localStorage` or `sessionStorage`.
   - Calm mode is a per-viewer preference in `localStorage`.
   - The chapters this tab has visited are kept in `sessionStorage`, per workspace, for the
     rail's marks.
   - Nothing else is stored, and no Meta key is ever handled by the web app (MODEL-06 for
     browser storage and URLs).

## Consequences

- `make check` now runs the web checks (client drift, Biome, `tsc`, Vitest). `make
  acceptance` adds the Storybook build and the Playwright suite, which runs on its own stack
  (`careerwright-l0-webtest`, ports 576xx-578xx).
- The web image is part of every stack, so the stack tests build it too.
- Dev-only advisory accepted: `undici` 8.11.2 through `jsdom`, the unit-test DOM, which makes
  no network request. The fix (8.12.2) was under 14 days old when this was written. Recheck
  it with `pnpm audit` when bumping `jsdom`.
- A hosted milestone would keep the route handler and Host check, and replace the emulator
  with real Google sign-in.
