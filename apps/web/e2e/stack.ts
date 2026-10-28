// The browser tests' own stack: project `nessa-l0-webtest`, its own loopback ports and a
// temporary NESSA_HOME, driven through the same tool as `make demo` (backend/tools/stack.py).
import { execFileSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

export const PROJECT = "nessa-l0-webtest";
export const PORTS = { web: 57600, api: 57700, auth: 57799, postgres: 57832 };
export const WEB_ORIGIN = `http://127.0.0.1:${PORTS.web}`;
export const AUTH_ORIGIN = `http://127.0.0.1:${PORTS.auth}`;
export const FIXTURE_WORKSPACE = "74fa4514-899d-5316-80fd-4161dc0dbda0";
/** Set by global setup; the restart and the teardown reuse the same NESSA_HOME. */
export const HOME_VARIABLE = "NESSA_WEBTEST_HOME";

const BACKEND = fileURLToPath(new URL("../../../backend/", import.meta.url));

export function newHome(): string {
  return mkdtempSync(join(tmpdir(), `${PROJECT}-home-`));
}

/** Runs `python -m tools.stack <command>` for the test project; throws on failure. */
export function stack(command: string): string {
  const home = process.env[HOME_VARIABLE];
  const args = ["run", "--locked", "--quiet", "python", "-m", "tools.stack", command];
  args.push("--project", PROJECT);
  if (home !== undefined) args.push("--home", home);
  return execFileSync("uv", args, {
    cwd: BACKEND,
    env: {
      ...process.env,
      NESSA_WEB_PORT: String(PORTS.web),
      NESSA_API_PORT: String(PORTS.api),
      NESSA_AUTH_PORT: String(PORTS.auth),
      NESSA_PG_PORT: String(PORTS.postgres),
    },
    encoding: "utf8",
    timeout: 1_800_000,
    stdio: ["ignore", "pipe", "pipe"],
  });
}
