// @vitest-environment node
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { previewFromTrace, TRACE_SHA256 } from "./trace";

const PACK = fileURLToPath(
  new URL("../../../../../fixtures/m0/worked_trace.json", import.meta.url),
);
const bytes = readFileSync(PACK);
const text = bytes.toString("utf8");
const sha = (value: string) => createHash("sha256").update(value).digest("hex");

describe("[BND1-12] the route preview comes from the pinned TRACE-01 fixture, labelled", () => {
  it("reads the supplied pack file, whose hash is the pinned one", () => {
    expect(createHash("sha256").update(bytes).digest("hex")).toBe(TRACE_SHA256);
  });

  it("keeps the fixture's routes, numbers and stated layers, and its synthetic origin", () => {
    const preview = previewFromTrace(text, TRACE_SHA256);
    if (preview.state !== "complete") throw new Error(`unexpected ${preview.state}`);

    expect(preview.source).toMatchObject({
      locator: "fixtures/m0/worked_trace.json",
      sha256: TRACE_SHA256,
      dataAsOf: "2027-01-01",
    });
    expect(preview.routes.map((r) => [r.key, r.layer])).toEqual([
      ["TRACE-01/A", 1],
      ["TRACE-01/B", 1],
      ["TRACE-01/C", 1],
      ["TRACE-01/D", 2],
      ["TRACE-01/E", 3],
    ]);
    const b = preview.routes.find((r) => r.letter === "B");
    expect(b).toMatchObject({
      timeMonths: 4,
      economicCost: { minor_units: 60000, currency: "GBP" },
      directSpend: { minor_units: 60000, currency: "GBP" },
      conditional: true,
      start: "2027-01-01",
      finish: "2027-04-30",
    });
    expect(b?.paymentsByMonth.map((m) => m.minor_units)).toEqual([
      15000, 15000, 15000, 15000, 0, 0,
    ]);
    expect(preview.selected).toEqual({
      letter: "B",
      peakMonthlyPayment: { minor_units: 15000, currency: "GBP" },
      lowestBalance: { minor_units: 485000, currency: "GBP" },
    });
    expect(preview).toMatchObject({ targetTitle: "Data quality analyst", horizonMonths: 6 });
  });

  it("fails, never shows an empty preview, when the bytes are not the pinned file", () => {
    const altered = text.replace('"economic_cost_minor": 60000', '"economic_cost_minor": 50000');

    expect(previewFromTrace(altered, sha(altered))).toEqual({
      state: "failed",
      reason: "checksum_mismatch",
      locator: "fixtures/m0/worked_trace.json",
    });
  });

  it.each([
    [
      "not synthetic",
      (t: { synthetic: boolean }) => Object.assign(t, { synthetic: false }),
      "not_synthetic",
    ],
    [
      "a route without a stated layer",
      (t: { expected: { fronts: string[][] } }) =>
        Object.assign(t.expected, { fronts: [["A", "B", "C"], ["D"]] }),
      "malformed",
    ],
    [
      "a negative amount",
      (t: { routes: Array<{ economic_cost_minor: number }> }) =>
        Object.assign(t.routes[0] ?? {}, { economic_cost_minor: -1 }),
      "malformed",
    ],
  ])(
    "refuses content that is %s (checked after the hash, as defence in depth)",
    (_name, mutate, reason) => {
      const trace = JSON.parse(text);
      mutate(trace);

      expect(previewFromTrace(JSON.stringify(trace), TRACE_SHA256)).toMatchObject({
        state: "failed",
        reason,
      });
    },
  );
});
