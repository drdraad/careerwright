import { describe, expect, it } from "vitest";
import { hostAllowed, securityHeaders } from "./requestPolicy";

const ALLOWED = ["127.0.0.1:53000", "localhost:53000"];

describe("[BND1-13] the web origin answers only on its loopback address", () => {
  it.each([
    ["127.0.0.1:53000", true],
    ["LOCALHOST:53000", true],
    ["evil.example:53000", false],
    ["127.0.0.1", false],
    ["127.0.0.1:53001", false],
    [null, false],
  ])("Host %j allowed: %s", (host, allowed) => {
    expect(hostAllowed(host, ALLOWED)).toBe(allowed);
  });
});

describe("[BND1-11] the page may reach only its own origin and the local Auth emulator", () => {
  it("limits connections, scripts, fonts and images to this origin and the emulator", () => {
    const csp = securityHeaders("http://127.0.0.1:59099", false)["Content-Security-Policy"];

    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("connect-src 'self' http://127.0.0.1:59099;");
    expect(csp).toContain("font-src 'self'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).not.toContain("unsafe-eval");
    expect(csp).not.toMatch(/https:|\*/);
  });
});
