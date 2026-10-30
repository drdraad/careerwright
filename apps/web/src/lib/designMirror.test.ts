// @vitest-environment node
// src/design mirrors the canonical design system in docs/design (the web image's build context
// is apps/web, so it cannot reach docs/). The mirror must stay byte-identical: tokens, both
// font files and their licence texts (ruling R8), and nothing else.
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const MIRRORED = [
  "tokens/tokens.css",
  "fonts/source-sans-3/SourceSans3-Variable.ttf",
  "fonts/source-sans-3/OFL.txt",
  "fonts/outfit/Outfit-Variable.ttf",
  "fonts/outfit/OFL.txt",
];

const here = (path: string) => fileURLToPath(new URL(`../design/${path}`, import.meta.url));
const canonical = (path: string) =>
  fileURLToPath(new URL(`../../../../docs/design/${path}`, import.meta.url));

describe("[UI-04][UI-03] the web app uses the reviewed tokens and licensed fonts unchanged", () => {
  it.each(MIRRORED)("%s is identical to docs/design", (path) => {
    expect(readFileSync(here(path)).equals(readFileSync(canonical(path)))).toBe(true);
  });

  it("holds no retired file (Newsreader retired with the calm observatory)", () => {
    const files = readdirSync(here(""), { recursive: true, withFileTypes: true })
      // Finder's .DS_Store and other hidden files are not part of the mirror.
      .filter((entry) => entry.isFile() && !entry.name.startsWith("."))
      .map((entry) =>
        `${entry.parentPath.slice(here("").length)}/${entry.name}`.replace(/^\//, ""),
      );
    expect(files.sort()).toEqual([...MIRRORED].sort());
  });
});
