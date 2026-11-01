// The profile editor against a scripted API at the network edge (fetch): expected-version
// saves, the stale-version path, and idempotent retries (GC7, ADR 0004 decisions 6 and 7).
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ProfileDocument, ProfileOut, SourceOut, SupportNoteOut } from "@/generated/api";
import { client } from "@/generated/api/client.gen";
import { configureApiClient } from "@/lib/api";
import { SupportShown } from "@/lib/world/settings";
import { EvidenceDrawer, EvidenceProvider } from "./EvidenceDrawer";
import { ProfileEditor } from "./ProfileEditor";

const WS = "74fa4514-899d-5316-80fd-4161dc0dbda0";
const SRC = "8d1f6f8e-46a1-5c2b-9d0e-3f7a1b2c4d5e";

function documentWith(cities: string[]): ProfileDocument {
  return {
    schema_version: "4",
    work_status: { state: "unasked", value: null, source_ref_id: null },
    qualifications: { state: "unasked", value: null, source_ref_id: null },
    preferred_name: { state: "unasked", value: null, source_ref_id: null },
    current_role: { state: "unasked", value: null, source_ref_id: null },
    cities: { state: "provided", value: cities, source_ref_id: SRC },
    target_titles: { state: "provided", value: ["Data quality analyst"], source_ref_id: SRC },
    weekly_study_hours: { state: "unasked", value: null, source_ref_id: null },
    direct_spend_cap: {
      state: "provided",
      value: { minor_units: 150000, currency: "GBP" },
      source_ref_id: SRC,
    },
    monthly_payment_cap: { state: "unknown", value: null, source_ref_id: SRC },
    enjoyed_tasks: { state: "unasked", value: null, source_ref_id: null },
    confident_tasks: { state: "unasked", value: null, source_ref_id: null },
    evidenced_tasks: { state: "unasked", value: null, source_ref_id: null },
    work_style: { state: "unasked", value: null, source_ref_id: null },
    minimum_salary: { state: "unasked", value: null, source_ref_id: null },
  };
}

const profileOut = (version: number, cities: string[]): ProfileOut => ({
  workspace_id: WS,
  version,
  document: documentWith(cities),
  created_by: null,
  created_at: "2027-01-01T00:00:00Z",
});

/** Version 2 as another tab saved it: the total spending limit changed, nothing else. */
function versionTwoWithCap(minor: number): ProfileOut {
  return {
    ...profileOut(2, ["Manchester"]),
    document: {
      ...documentWith(["Manchester"]),
      direct_spend_cap: {
        state: "provided",
        value: { minor_units: minor, currency: "GBP" },
        source_ref_id: SRC,
      },
    },
  };
}

const fixtureSource: SourceOut = {
  source_ref_id: SRC,
  kind: "fixture",
  label: "Synthetic fixture persona P01 (supplied M0 pack)",
  locator: "fixtures/m0/personas/P01.json",
  content_sha256: "03e72eefa7f975fc50c075a17f2136a0f39385efce25ccdb2834b5f9a5ec518e",
  recorded_by: null,
  observed_at: "2027-01-01T00:00:00Z",
  created_at: "2027-01-01T00:00:00Z",
};

type Sent = { method: string; url: string; key: string | null; body: unknown };

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/** A fresh 409 each time: a Response body can be read only once. */
const stale = () =>
  json(409, {
    error: {
      code: "STALE_INPUT_VERSION",
      message: "ignored by the UI",
      retryable: false,
      stage: "profile",
      correlation_id: "c1",
      details: { current_version: 2 },
    },
  });

type Edge = {
  /** The profile GET fails at the network (the API went away after the PUT). */
  profileUnreachable?: boolean;
  /** Answers the sources list; defaults to an empty list at once. */
  sources?: () => Promise<Response>;
};

/** Answers GETs from `current` and each PUT with the next scripted answer. */
function api(current: { profile: ProfileOut }, puts: Array<Response | Error>, edge: Edge = {}) {
  const sent: Sent[] = [];
  client.setConfig({
    fetch: async (input: RequestInfo | URL) => {
      const request = input as Request;
      const body = request.method === "PUT" ? await request.json() : null;
      sent.push({
        method: request.method,
        url: request.url,
        key: request.headers.get("Idempotency-Key"),
        body,
      });
      if (request.method === "GET" && request.url.endsWith("/profile")) {
        if (edge.profileUnreachable) throw new TypeError("network");
        return json(200, current.profile);
      }
      if (request.method === "GET" && request.url.includes("/sources"))
        return edge.sources?.() ?? json(200, { items: [], next_cursor: null });
      const next = puts.shift();
      if (next === undefined) throw new Error("unscripted request");
      if (next instanceof Error) throw next;
      return next;
    },
  });
  return sent;
}

function renderEditor(profile: ProfileOut, supportShown: (shown: boolean) => void = () => {}) {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queries}>
      <SupportShown.Provider value={supportShown}>
        <EvidenceProvider>
          <ProfileEditor workspaceId={WS} profile={profile} />
          <EvidenceDrawer />
        </EvidenceProvider>
      </SupportShown.Provider>
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

/** The API's panel beside a direct edit (`careerwright.profile.safety.SUPPORT_NOTE_ENTRY`). */
const entryPanel = (saved: boolean): SupportNoteOut => ({
  policy_version: "support-policy-9",
  review_status: "accepted for L0 at session 1 (human gate H-12)",
  message:
    "If anything you typed is about how you are feeling, support is available any time, " +
    "from people trained to help. " +
    (saved
      ? "Your answers were saved as usual."
      : "Your answers were not saved; the reason is shown with them."),
  resources: [
    {
      name: "Samaritans",
      contact: "Call 116 123",
      when: "To talk",
      source_url: "https://www.samaritans.org/",
      checked_on: "2026-10-28",
    },
  ],
});

beforeEach(() => {
  configureApiClient(async () => "token");
  // Node's Request (used under jsdom) needs an absolute URL; a browser resolves "/api" itself.
  client.setConfig({ baseUrl: "http://localhost:3000/api" });
});

describe("[DUR-04][API-04] saving the profile is an expected-version, idempotent command", () => {
  it("sends the loaded version with a key, and says it is saved", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    const sent = api(current, [json(201, profileOut(2, ["Leeds"]))]);
    const user = renderEditor(current.profile);

    await user.clear(screen.getByRole("textbox", { name: "Work area 1" }));
    await user.type(screen.getByRole("textbox", { name: "Work area 1" }), "Leeds");
    expect(screen.getByText("Unsaved changes")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByText("Saved.")).toBeInTheDocument();
    // Plain words: the person sees their answers saved, never a version number (D-M5).
    expect(document.body.textContent).not.toMatch(/version/i);
    const put = sent.find((request) => request.method === "PUT");
    expect(put?.url).toBe(`http://localhost:3000/api/v1/workspaces/${WS}/profile`);
    expect(put?.key).toMatch(/^[0-9a-f-]{36}$/);
    expect(put?.body).toMatchObject({
      expected_version: 1,
      profile: {
        cities: { state: "provided", value: ["Leeds"] },
        direct_spend_cap: { state: "provided", value: { minor_units: 150000, currency: "GBP" } },
        monthly_payment_cap: { state: "unknown" },
      },
    });
  });

  it("[PROF-13][PROF-07] saves what the person is doing now and an expected qualification through the same command", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    const sent = api(current, [json(201, profileOut(2, ["Manchester"]))]);
    const user = renderEditor(current.profile);

    await user.selectOptions(
      screen.getByRole("combobox", { name: "How you answer what you're doing now" }),
      "provided",
    );
    await user.selectOptions(
      screen.getByRole("combobox", { name: "What you're doing now" }),
      "In education or training",
    );
    await user.selectOptions(
      screen.getByRole("combobox", { name: "How you answer qualifications" }),
      "provided",
    );
    await user.type(screen.getByRole("textbox", { name: "Qualification 1" }), "A-level biology");
    // Neither status is picked for the person: unmarked, the save is refused with the reason.
    await user.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Mark each qualification achieved or expected.")).toBeVisible();
    expect(sent.some((request) => request.method === "PUT")).toBe(false);
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Qualification 1: achieved or expected" }),
      "expected",
    );
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByText("Saved.")).toBeInTheDocument();
    expect(sent.find((request) => request.method === "PUT")?.body).toMatchObject({
      expected_version: 1,
      profile: {
        work_status: { state: "provided", value: "in_education_or_training" },
        qualifications: {
          state: "provided",
          value: [{ name: "A-level biology", status: "expected" }],
        },
      },
    });
  });

  it("[STATE-11] offers “I haven't had a job yet” for the current role only, and never calls it a gap", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    const sent = api(current, [json(201, profileOut(2, ["Manchester"]))]);
    const user = renderEditor(current.profile);

    const role = screen.getByRole("combobox", { name: "How you answer current role" });
    expect(within(role).getByRole("option", { name: "I haven't had a job yet" })).toBeTruthy();
    const cities = screen.getByRole("combobox", { name: "How you answer work areas" });
    expect(within(cities).queryByRole("option", { name: "I haven't had a job yet" })).toBeNull();
    await user.selectOptions(role, "no_job_yet");
    // An answer like any other: no "less precise without it" line beside it.
    const section = role.closest("section");
    expect(section).not.toBeNull();
    expect(within(section as HTMLElement).queryByText(/Less precise without it/)).toBeNull();
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByText("Saved.")).toBeInTheDocument();
    expect(sent.find((request) => request.method === "PUT")?.body).toMatchObject({
      profile: { current_role: { state: "no_job_yet" } },
    });
  });

  it("after a stale save takes the new version's answers, keeps the person's edits, and saves on it", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    const sent = api(current, [stale(), json(201, profileOut(3, ["Leeds"]))]);
    const user = renderEditor(current.profile);
    current.profile = versionTwoWithCap(90000);

    await user.clear(screen.getByRole("textbox", { name: "Work area 1" }));
    await user.type(screen.getByRole("textbox", { name: "Work area 1" }), "Leeds");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    // The refusal and the answers that changed under the person are announced, and focus
    // moves to the notice, so nothing changes silently for a screen-reader user.
    const notice = await screen.findByRole("alert");
    expect(notice).toHaveTextContent("Your answers changed while you were editing");
    expect(notice).toHaveTextContent("The newer answers changed: Total spending limit to £900.");
    expect(notice).toHaveFocus();
    expect(document.body.textContent).not.toMatch(/version/i);
    expect(screen.getByRole("textbox", { name: "Work area 1" })).toHaveValue("Leeds");
    // The field the person did not touch now shows version 2's answer, not the old one.
    expect(screen.getByRole("textbox", { name: /Total spending limit, in pounds/ })).toHaveValue(
      "900",
    );

    await user.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Saved.")).toBeInTheDocument();
    const puts = sent.filter((request) => request.method === "PUT");
    expect(puts.map((put) => (put.body as { expected_version: number }).expected_version)).toEqual([
      1, 2,
    ]);
    expect(puts[1]?.body).toMatchObject({
      profile: {
        cities: { state: "provided", value: ["Leeds"] },
        direct_spend_cap: { state: "provided", value: { minor_units: 90000, currency: "GBP" } },
      },
    });
    expect(puts[0]?.key).not.toBe(puts[1]?.key); // a different request needs a new key
  });

  it("shows a conflict when both the person and the newer version changed the same answer", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    api(current, [stale()]);
    const user = renderEditor(current.profile);
    current.profile = versionTwoWithCap(90000);

    const amount = screen.getByRole("textbox", { name: /Total spending limit, in pounds/ });
    await user.clear(amount);
    await user.type(amount, "1,200");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByRole("alert")).toHaveFocus();
    expect(amount).toHaveValue("1,200");
    // The conflict is part of the control's description, not only text beside it.
    expect(amount).toHaveAccessibleDescription(
      "The newer answers have £900 here. Saving keeps your answer instead.",
    );
    expect(
      screen.getByRole("combobox", { name: "How you answer total spending limit" }),
    ).toHaveAccessibleDescription(
      "The newer answers have £900 here. Saving keeps your answer instead.",
    );
  });

  it("names no conflict where the person's edit already matches the newer version", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    api(current, [stale()]);
    const user = renderEditor(current.profile);
    current.profile = versionTwoWithCap(90000);

    const amount = screen.getByRole("textbox", { name: /Total spending limit, in pounds/ });
    await user.clear(amount);
    await user.type(amount, "900");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The newer answers changed: Total spending limit to £900.",
    );
    expect(screen.queryByText(/Saving keeps your answer instead/)).not.toBeInTheDocument();
    expect(amount).not.toHaveAccessibleDescription();
  });

  it("says so when the newer version cannot be loaded after a stale save", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    api(current, [stale()], { profileUnreachable: true });
    const user = renderEditor(current.profile);

    await user.clear(screen.getByRole("textbox", { name: "Work area 1" }));
    await user.type(screen.getByRole("textbox", { name: "Work area 1" }), "Leeds");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    // One announcement, on the notice that has focus; the cause follows it in place.
    const notice = await screen.findByRole("alert");
    expect(notice).toHaveTextContent(
      "Your answers changed elsewhere, and the newer ones couldn't be loaded",
    );
    expect(notice).toHaveFocus();
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(screen.getByText("Careerwright's service isn't reachable")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Work area 1" })).toHaveValue("Leeds");
  });

  it("retries a failed send of the same change with the same key", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    const sent = api(current, [new TypeError("network"), json(201, profileOut(2, ["York"]))]);
    const user = renderEditor(current.profile);

    await user.clear(screen.getByRole("textbox", { name: "Work area 1" }));
    await user.type(screen.getByRole("textbox", { name: "Work area 1" }), "York");
    await user.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Careerwright's service isn't reachable")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Saved.")).toBeInTheDocument();
    const keys = sent.filter((request) => request.method === "PUT").map((put) => put.key);
    expect(keys).toHaveLength(2);
    expect(keys[0]).toBe(keys[1]);
  });

  it("refuses to send an invalid amount and says why beside the field", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    const sent = api(current, []);
    const user = renderEditor(current.profile);

    const amount = screen.getByRole("textbox", { name: /Total spending limit, in pounds/ });
    await user.clear(amount);
    await user.type(amount, "12.345");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByText("Use at most two decimal places (pence).")).toBeInTheDocument();
    expect(amount).toHaveAttribute("aria-invalid", "true");
    await waitFor(() => expect(sent.filter((r) => r.method === "PUT")).toHaveLength(0));
  });
});

describe("[PROF-09] a direct entry with a risk word is saved, with the calm support panel", () => {
  // The product owner's decision (31 October 2026): What we know's direct entries go through
  // the support screen, as a message does. The API screens; the form shows its panel. The
  // words are the support tests' own (`YouChapter.test.tsx`).
  const RISK = "I volunteer on a suicide prevention helpline.";

  it("shows the panel the API sends with a save, stills the world, and keeps it until dismissed", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    const sent = api(current, [
      json(201, { ...profileOut(2, ["Manchester"]), support_note: entryPanel(true) }),
    ]);
    const shown = vi.fn();
    const user = renderEditor(current.profile, shown);

    const target = screen.getByRole("textbox", { name: "Target role 1" });
    await user.clear(target);
    await user.type(target, RISK);
    const save = screen.getByRole("button", { name: "Save changes" });
    await user.click(save);

    const panel = await screen.findByRole("region", { name: "Support is available" });
    expect(panel).toHaveTextContent("Your answers were saved as usual.");
    expect(panel).toHaveTextContent("Samaritans: Call 116 123");
    expect(shown).toHaveBeenLastCalledWith(true); // the world is drawn still
    expect(screen.getByRole("status")).toHaveTextContent(
      "Saved. Support information is shown above Save changes.",
    );
    // Beside where the person saved, above the button.
    expect(panel.compareDocumentPosition(save) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
    // Saved as entered: the person's own edit, sent as usual.
    expect(sent.find((s) => s.method === "PUT")?.body).toMatchObject({
      profile: { target_titles: { state: "provided", value: [RISK] } },
    });

    await user.click(within(panel).getByRole("button", { name: "Dismiss the support note" }));
    expect(screen.queryByRole("region", { name: "Support is available" })).toBeNull();
    expect(save).toHaveFocus();
    expect(shown).toHaveBeenLastCalledWith(false);
  });

  it("shows the panel beside a refused save too, saying the answers were not saved", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    api(current, [
      json(409, {
        error: {
          code: "STALE_INPUT_VERSION",
          message: "ignored by the UI",
          retryable: false,
          stage: "profile",
          correlation_id: "c1",
          details: { current_version: 2 },
        },
        support_note: entryPanel(false),
      }),
    ]);
    current.profile = versionTwoWithCap(90000);
    const user = renderEditor(profileOut(1, ["Manchester"]));

    const target = screen.getByRole("textbox", { name: "Target role 1" });
    await user.clear(target);
    await user.type(target, RISK);
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Your answers changed while you were editing",
    );
    expect(screen.getByRole("region", { name: "Support is available" })).toHaveTextContent(
      "Your answers were not saved; the reason is shown with them.",
    );
  });
});

describe("[BND1-12][UI-09] the source drawer shows the live provenance state", () => {
  it("moves from loading to the record when the sources arrive after it opened", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    let answer!: (response: Response) => void;
    api(current, [], {
      sources: () =>
        new Promise<Response>((resolve) => {
          answer = resolve;
        }),
    });
    const user = renderEditor(current.profile);

    await user.click(screen.getByRole("button", { name: "Source for work areas" }));
    expect(await screen.findByText("Loading the source record")).toBeInTheDocument();
    answer(json(200, { items: [fixtureSource], next_cursor: null }));

    expect(await screen.findByText(fixtureSource.label)).toBeInTheDocument();
    expect(screen.queryByText("Loading the source record")).not.toBeInTheDocument();
  });

  it("looks again before saying an answer has no source record", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    let calls = 0;
    api(current, [], {
      sources: async () => {
        calls += 1;
        return json(200, { items: calls === 1 ? [] : [fixtureSource], next_cursor: null });
      },
    });
    const user = renderEditor(current.profile);

    await user.click(screen.getByRole("button", { name: "Source for work areas" }));

    expect(await screen.findByText(fixtureSource.label)).toBeInTheDocument();
    expect(screen.queryByText(/no source record was found/)).not.toBeInTheDocument();
    expect(calls).toBe(2); // the first list predated the answer's source; it looked again
  });
});
