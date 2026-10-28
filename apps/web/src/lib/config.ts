// The web server's runtime configuration, read from the environment and refused unless it is
// local (Global Constraint 9, ADR 0004 decision 3): loopback or single-label Compose hosts
// only, a `demo-` Firebase project and the emulator on loopback. Server-side only.

export type WebConfig = {
  /** Where the server forwards `/api/v1/*`: the API on the internal network. */
  apiInternalUrl: string;
  /** The Auth emulator as the browser reaches it (published by the edge on loopback). */
  authEmulatorUrl: string;
  firebaseProjectId: string;
  /** `host:port` values the web origin answers to; anything else is refused (DNS rebinding). */
  allowedHosts: string[];
  /** The supplied fixture pack, read by the fixture adapter. */
  fixturesDir: string;
};

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "[::1]"]);
const COMPOSE_NAME = /^[a-z][a-z0-9-]*$/; // a single-label service name such as `api`

class ConfigError extends Error {}

function required(env: Record<string, string | undefined>, name: string): string {
  const value = env[name];
  if (value === undefined || value.trim() === "") {
    throw new ConfigError(`${name} is required`);
  }
  return value.trim();
}

function origin(name: string, value: string, hostAllowed: (host: string) => boolean): string {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new ConfigError(`${name} must be a URL`);
  }
  if (url.protocol !== "http:" || url.pathname !== "/" || url.search || url.hash) {
    throw new ConfigError(`${name} must be a plain http origin`);
  }
  if (!hostAllowed(url.hostname)) {
    throw new ConfigError(`${name} must point at this machine`);
  }
  return url.origin;
}

function hostPort(name: string, value: string): string {
  const match = /^(\[::1\]|[^:[\]]+):(\d{1,5})$/.exec(value.trim().toLowerCase());
  if (match === null || !LOOPBACK_HOSTS.has(match[1] ?? "")) {
    throw new ConfigError(`${name} entries must be loopback host:port values`);
  }
  return match[0];
}

const VARIABLES = [
  "NESSA_API_INTERNAL_URL",
  "NESSA_AUTH_EMULATOR_URL",
  "NESSA_FIREBASE_PROJECT_ID",
  "NESSA_WEB_ALLOWED_HOSTS",
  "NESSA_FIXTURES_DIR",
] as const;

export function readWebConfig(env: Record<string, string | undefined>): WebConfig {
  const missing = VARIABLES.filter((name) => (env[name] ?? "").trim() === "");
  if (missing.length > 0) throw new ConfigError(`missing configuration: ${missing.join(", ")}`);
  const projectId = required(env, "NESSA_FIREBASE_PROJECT_ID");
  if (!projectId.startsWith("demo-")) {
    throw new ConfigError("NESSA_FIREBASE_PROJECT_ID must be a demo- project (emulator only)");
  }
  const hosts = required(env, "NESSA_WEB_ALLOWED_HOSTS")
    .split(",")
    .map((entry) => hostPort("NESSA_WEB_ALLOWED_HOSTS", entry));
  return {
    apiInternalUrl: origin(
      "NESSA_API_INTERNAL_URL",
      required(env, "NESSA_API_INTERNAL_URL"),
      (host) => LOOPBACK_HOSTS.has(host) || COMPOSE_NAME.test(host),
    ),
    authEmulatorUrl: origin(
      "NESSA_AUTH_EMULATOR_URL",
      required(env, "NESSA_AUTH_EMULATOR_URL"),
      (host) => LOOPBACK_HOSTS.has(host),
    ),
    firebaseProjectId: projectId,
    allowedHosts: hosts,
    fixturesDir: required(env, "NESSA_FIXTURES_DIR"),
  };
}

let cached: WebConfig | undefined;

/** The process configuration, checked once; a refusal fails every request that needs it. */
export function webConfig(): WebConfig {
  cached ??= readWebConfig(process.env);
  return cached;
}
