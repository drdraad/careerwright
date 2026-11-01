import { defineConfig, devices } from "@playwright/test";
import { WEB_ORIGIN } from "./e2e/stack";

// Browser journeys against the real Compose stack in demo mode, in its own project, ports and
// CAREERWRIGHT_HOME (e2e/stack.ts). One worker: the journey restarts the shared stack.
// CAREERWRIGHT_CHROMIUM_PATH (unset by default) points the run at a Chromium already on the
// machine, for hosts that can't download the build this Playwright pins (a cloud session).
const chromium = process.env.CAREERWRIGHT_CHROMIUM_PATH;
export default defineConfig({
  testDir: "e2e",
  globalSetup: "./e2e/global-setup.ts",
  globalTeardown: "./e2e/global-teardown.ts",
  workers: 1,
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: [["list"]],
  use: {
    baseURL: WEB_ORIGIN,
    reducedMotion: "reduce",
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    ...(chromium ? { launchOptions: { executablePath: chromium } } : {}),
  },
});
