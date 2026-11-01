import { describe, expect, it } from "vitest";
import { ChangeKeys } from "./api";

describe("[API-01] one idempotency key per intended change (ADR 0004 decision 7)", () => {
  it("reuses the key when the same request is sent again after a failure", () => {
    const keys = new ChangeKeys();
    const first = keys.keyFor({ name: "Leeds plan", data_mode: "demo" });

    expect(keys.keyFor({ data_mode: "demo", name: "Leeds plan" })).toBe(first);
  });

  it("gives a different request, or the next change after success, a new key", () => {
    const keys = new ChangeKeys();
    const first = keys.keyFor({ name: "Leeds plan" });
    const edited = keys.keyFor({ name: "York plan" });
    keys.settled();
    const again = keys.keyFor({ name: "York plan" });

    expect(edited).not.toBe(first);
    expect(again).not.toBe(edited);
    expect(first).toMatch(/^[0-9a-f-]{36}$/);
  });
});
