// Generate the typed API client from the backend's OpenAPI document (Global Constraint 10).
//
//   pnpm run generate         rewrite src/generated/ (openapi.json and the client beside it)
//   pnpm run generate --check fail if either committed file differs from a fresh generation
//
// The document comes from `backend/tools/openapi.py`, which builds exactly what the API
// serves at `/openapi.json` without a database or keys, so this runs offline. Enums, money
// and error shapes reach the UI only through this output; never restate them by hand.
import { execFileSync } from "node:child_process";
import { mkdtempSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createClient } from "@hey-api/openapi-ts";

const here = fileURLToPath(new URL(".", import.meta.url));
const app = resolve(here, "..");
const backend = resolve(app, "../../backend");
const generated = join(app, "src/generated");
const check = process.argv.includes("--check");

function exportDocument() {
  return execFileSync("uv", ["run", "--locked", "--quiet", "python", "-m", "tools.openapi"], {
    cwd: backend,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "inherit"],
  });
}

async function generateInto(directory, documentPath) {
  await createClient({
    input: documentPath,
    output: { path: join(directory, "api"), postProcess: [] },
    logs: { level: "silent" },
    plugins: [
      "@hey-api/client-fetch",
      { name: "@hey-api/typescript", enums: "javascript" },
      { name: "@hey-api/sdk" },
    ],
  });
}

function files(directory) {
  return readdirSync(directory, { recursive: true })
    .map(String)
    .filter((name) => statSync(join(directory, name)).isFile())
    .sort();
}

const document = exportDocument();
if (!check) {
  writeFileSync(join(generated, "openapi.json"), document);
  rmSync(join(generated, "api"), { recursive: true, force: true });
  await generateInto(generated, join(generated, "openapi.json"));
  console.log(`generated ${relative(app, generated)}/ from the backend's OpenAPI document`);
} else {
  const scratch = mkdtempSync(join(tmpdir(), "nessa-client-"));
  try {
    writeFileSync(join(scratch, "openapi.json"), document);
    await generateInto(scratch, join(scratch, "openapi.json"));
    const expected = ["openapi.json", ...files(join(scratch, "api")).map((f) => join("api", f))];
    const actual = ["openapi.json", ...files(join(generated, "api")).map((f) => join("api", f))];
    const drift = [...new Set([...expected, ...actual])].filter((name) => {
      try {
        return !readFileSync(join(scratch, name)).equals(readFileSync(join(generated, name)));
      } catch {
        return true;
      }
    });
    if (drift.length > 0) {
      console.error(
        `The committed API client is out of date (${drift.join(", ")}). Run \`pnpm run generate\` in apps/web and commit the result.`,
      );
      process.exitCode = 1;
    } else {
      console.log("generated API client matches the backend's OpenAPI document");
    }
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
}
