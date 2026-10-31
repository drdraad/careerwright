import { describe, expect, it } from "vitest";
import { readWebConfig } from "./config";

const SAFE = {
  CAREERWRIGHT_API_INTERNAL_URL: "http://api:8000",
  CAREERWRIGHT_AUTH_EMULATOR_URL: "http://127.0.0.1:59099",
  CAREERWRIGHT_FIREBASE_PROJECT_ID: "demo-careerwright",
  CAREERWRIGHT_WEB_ALLOWED_HOSTS: "127.0.0.1:53000,localhost:53000",
};

describe("[SEC-03][BND1-13] the web server refuses unsafe configuration", () => {
  it("accepts the local configuration Compose gives it", () => {
    expect(readWebConfig(SAFE)).toEqual({
      apiInternalUrl: "http://api:8000",
      authEmulatorUrl: "http://127.0.0.1:59099",
      firebaseProjectId: "demo-careerwright",
      allowedHosts: ["127.0.0.1:53000", "localhost:53000"],
    });
  });

  it.each([
    ["CAREERWRIGHT_AUTH_EMULATOR_URL", "https://identitytoolkit.googleapis.com"],
    ["CAREERWRIGHT_AUTH_EMULATOR_URL", "http://192.168.1.4:9099"],
    ["CAREERWRIGHT_AUTH_EMULATOR_URL", "http://127.0.0.1:59099/path"],
    ["CAREERWRIGHT_FIREBASE_PROJECT_ID", "careerwright-real-project"],
    ["CAREERWRIGHT_API_INTERNAL_URL", "http://api.example.com:8000"],
    ["CAREERWRIGHT_API_INTERNAL_URL", "https://api:8000"],
    ["CAREERWRIGHT_WEB_ALLOWED_HOSTS", "0.0.0.0:53000"],
    ["CAREERWRIGHT_WEB_ALLOWED_HOSTS", "127.0.0.1:53000,careerwright.example.com:53000"],
    ["CAREERWRIGHT_WEB_ALLOWED_HOSTS", "127.0.0.1"],
    ["CAREERWRIGHT_WEB_ALLOWED_HOSTS", ""],
  ])("refuses %s=%j", (name, value) => {
    expect(() => readWebConfig({ ...SAFE, [name]: value })).toThrow(name);
  });

  it("names every missing variable", () => {
    expect(() => readWebConfig({})).toThrow(/CAREERWRIGHT_API_INTERNAL_URL/);
  });
});
