// Where the browser keeps the sign-in session, and what the event stream does on a real page
// (ADR 0005 decisions 5 and 9; MODEL-06, STATE-07, DUR-03).
import { expect, test } from "@playwright/test";
import { saveElsewhere } from "./api";
import { chapterUrl, liveUpdates, signIn } from "./helpers";
import { FIXTURE_WORKSPACE, stack } from "./stack";

test.beforeEach(() => {
  stack("reset-demo");
});

test("[MODEL-06] the session tokens live in IndexedDB, never in localStorage or sessionStorage", async ({
  page,
}) => {
  await signIn(page, "ada", chapterUrl("you"));
  await expect(liveUpdates(page, "Live")).toBeVisible();

  const stores = await page.evaluate(async () => {
    const keys = (storage: Storage) =>
      Array.from({ length: storage.length }, (_, i) => storage.key(i) ?? "");
    const NAME = "firebaseLocalStorageDb";
    const STORE = "firebaseLocalStorage";
    // Opening a database that does not exist would create it: look first.
    const exists = (await indexedDB.databases()).some((database) => database.name === NAME);
    const indexed = !exists
      ? []
      : await new Promise<string[]>((resolve, reject) => {
          const open = indexedDB.open(NAME);
          open.onerror = () => reject(open.error);
          open.onsuccess = () => {
            const database = open.result;
            if (!database.objectStoreNames.contains(STORE)) return resolve([]);
            const read = database.transaction(STORE, "readonly").objectStore(STORE).getAllKeys();
            read.onsuccess = () => resolve(read.result.map(String));
            read.onerror = () => reject(read.error);
          };
        });
    return { local: keys(localStorage), session: keys(sessionStorage), indexed };
  });

  expect(stores.local.filter((key) => key.startsWith("firebase:"))).toEqual([]);
  expect(stores.session.filter((key) => key.startsWith("firebase:"))).toEqual([]);
  expect(stores.indexed.some((key) => key.startsWith("firebase:authUser:"))).toBe(true);
});

test("[STATE-07][DUR-03] a newly opened page starts its stream after the workspace's last event", async ({
  page,
}) => {
  const workspaceRead = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/api/v1/workspaces/${FIXTURE_WORKSPACE}`) && response.ok(),
  );
  const streamOpened = page.waitForRequest((request) => request.url().includes("/events/stream"));
  await signIn(page, "ada", chapterUrl("you"));
  const workspace = (await (await workspaceRead).json()) as { last_event_seq: number };
  const stream = await streamOpened;

  expect(workspace.last_event_seq).toBeGreaterThan(0);
  expect(stream.headers()["last-event-id"]).toBe(String(workspace.last_event_seq));
});

test("[STATE-07][BND1-13] a change saved elsewhere reaches an open page through the web origin, unbuffered", async ({
  browser,
}) => {
  const watcher = await (await browser.newContext()).newPage();
  await signIn(watcher, "ada", chapterUrl("you"));
  await expect(liveUpdates(watcher, "Live")).toBeVisible();
  await expect(watcher.getByRole("banner").getByText("Saved, version 1")).toBeVisible();
  const opened = watcher.url();

  // Another client saves: the event must cross the API, the web server's proxy and the
  // browser's stream reader, and the page refetch, within a few seconds and without a reload.
  const made = await saveElsewhere(
    FIXTURE_WORKSPACE,
    "ada",
    "current_role",
    "Saved from another tab",
  );

  expect(made).toBe(2);
  await expect(watcher.getByRole("banner").getByText("Saved, version 2")).toBeVisible({
    timeout: 5_000,
  });
  await expect(watcher.getByRole("textbox", { name: "Current role", exact: true })).toHaveValue(
    "Saved from another tab",
  );
  expect(watcher.url()).toBe(opened);
  await watcher.context().close();
});
