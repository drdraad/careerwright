import { describe, expect, it } from "vitest";
import { safeNext } from "./navigation";

describe("[BND1-13] sign-in returns only to a path on this site", () => {
  it.each([
    ["/w/123/routes", "/w/123/routes"],
    ["/", "/"],
    [undefined, "/"],
    ["https://evil.example/", "/"],
    ["//evil.example/", "/"],
    ["/\\evil.example", "/"],
    ["javascript:alert(1)", "/"],
    ["/\u0009/evil.example", "/"],
  ])("%j goes to %j", (next, expected) => {
    expect(safeNext(next)).toBe(expected);
  });
});
