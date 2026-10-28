// Server-side half of the fixture adapter: reads the pinned file and checks its SHA-256
// before anything reaches the page. A missing or altered file is a typed failure.
// Server only: it reads the file system (a client import fails the build).
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { previewFromTrace, type RoutePreview, TRACE_LOCATOR } from "./trace";

export async function loadRoutePreview(fixturesDir: string): Promise<RoutePreview> {
  let bytes: Buffer;
  try {
    bytes = await readFile(join(fixturesDir, "worked_trace.json"));
  } catch {
    return { state: "failed", reason: "missing", locator: TRACE_LOCATOR };
  }
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  return previewFromTrace(bytes.toString("utf8"), sha256);
}
