// The browser tests' own stack: project `careerwright-l0-webtest`, its own loopback ports and a
// temporary CAREERWRIGHT_HOME, driven through the same tool as `make demo` (backend/tools/stack.py).
import { execFileSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

export const PROJECT = "careerwright-l0-webtest";
const portBase = Number(process.env.CAREERWRIGHT_E2E_PORT_BASE ?? "57600");
if (!Number.isInteger(portBase) || portBase < 1024 || portBase + 232 > 65535) {
  throw new Error("CAREERWRIGHT_E2E_PORT_BASE must leave room for four local test ports");
}
export const PORTS = {
  web: portBase,
  api: portBase + 100,
  auth: portBase + 199,
  postgres: portBase + 232,
};
export const WEB_ORIGIN = `http://127.0.0.1:${PORTS.web}`;
export const AUTH_ORIGIN = `http://127.0.0.1:${PORTS.auth}`;
export const FIXTURE_WORKSPACE = "74fa4514-899d-5316-80fd-4161dc0dbda0";
/** Set by global setup; the restart and the teardown reuse the same CAREERWRIGHT_HOME. */
export const HOME_VARIABLE = "CAREERWRIGHT_WEBTEST_HOME";

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
      CAREERWRIGHT_WEB_PORT: String(PORTS.web),
      CAREERWRIGHT_API_PORT: String(PORTS.api),
      CAREERWRIGHT_AUTH_PORT: String(PORTS.auth),
      CAREERWRIGHT_PG_PORT: String(PORTS.postgres),
    },
    encoding: "utf8",
    timeout: 1_800_000,
    stdio: ["ignore", "pipe", "pipe"],
  });
}
