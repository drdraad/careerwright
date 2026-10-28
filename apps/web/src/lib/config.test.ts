import { describe, expect, it } from "vitest";
import { readWebConfig } from "./config";

const SAFE = {
  NESSA_API_INTERNAL_URL: "http://api:8000",
  NESSA_AUTH_EMULATOR_URL: "http://127.0.0.1:59099",
  NESSA_FIREBASE_PROJECT_ID: "demo-nessa",
  NESSA_WEB_ALLOWED_HOSTS: "127.0.0.1:53000,localhost:53000",
  NESSA_FIXTURES_DIR: "/fixtures/m0",
};

describe("[SEC-03][BND1-13] the web server refuses unsafe configuration", () => {
  it("accepts the local configuration Compose gives it", () => {
    expect(readWebConfig(SAFE)).toEqual({
      apiInternalUrl: "http://api:8000",
      authEmulatorUrl: "http://127.0.0.1:59099",
      firebaseProjectId: "demo-nessa",
      allowedHosts: ["127.0.0.1:53000", "localhost:53000"],
      fixturesDir: "/fixtures/m0",
    });
  });

  it.each([
    ["NESSA_AUTH_EMULATOR_URL", "https://identitytoolkit.googleapis.com"],
    ["NESSA_AUTH_EMULATOR_URL", "http://192.168.1.4:9099"],
    ["NESSA_AUTH_EMULATOR_URL", "http://127.0.0.1:59099/path"],
    ["NESSA_FIREBASE_PROJECT_ID", "nessa-real-project"],
    ["NESSA_API_INTERNAL_URL", "http://api.example.com:8000"],
    ["NESSA_API_INTERNAL_URL", "https://api:8000"],
    ["NESSA_WEB_ALLOWED_HOSTS", "0.0.0.0:53000"],
    ["NESSA_WEB_ALLOWED_HOSTS", "127.0.0.1:53000,nessa.example.com:53000"],
    ["NESSA_WEB_ALLOWED_HOSTS", "127.0.0.1"],
    ["NESSA_WEB_ALLOWED_HOSTS", ""],
    ["NESSA_FIXTURES_DIR", ""],
  ])("refuses %s=%j", (name, value) => {
    expect(() => readWebConfig({ ...SAFE, [name]: value })).toThrow(name);
  });

  it("names every missing variable", () => {
    expect(() => readWebConfig({})).toThrow(/NESSA_API_INTERNAL_URL/);
  });
});
