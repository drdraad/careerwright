// The profile editor against a scripted API at the network edge (fetch): expected-version
// saves, the stale-version path, and idempotent retries (GC7, ADR 0004 decisions 6 and 7).
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import type { ProfileDocument, ProfileOut } from "@/generated/api";
import { client } from "@/generated/api/client.gen";
import { configureApiClient } from "@/lib/api";
import { EvidenceDrawer, EvidenceProvider } from "./EvidenceDrawer";
import { ProfileEditor } from "./ProfileEditor";

const WS = "74fa4514-899d-5316-80fd-4161dc0dbda0";
const SRC = "8d1f6f8e-46a1-5c2b-9d0e-3f7a1b2c4d5e";

function documentWith(cities: string[]): ProfileDocument {
  return {
    schema_version: "1",
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
  };
}

const profileOut = (version: number, cities: string[]): ProfileOut => ({
  workspace_id: WS,
  version,
  document: documentWith(cities),
  created_by: null,
  created_at: "2027-01-01T00:00:00Z",
});

type Sent = { method: string; url: string; key: string | null; body: unknown };

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

const stale = json(409, {
  error: {
    code: "STALE_INPUT_VERSION",
    message: "ignored by the UI",
    retryable: false,
    stage: "profile",
    correlation_id: "c1",
    details: { current_version: 2 },
  },
});

/** Answers GETs from `current` and each PUT with the next scripted answer. */
function api(current: { profile: ProfileOut }, puts: Array<Response | Error>) {
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
      if (request.method === "GET" && request.url.endsWith("/profile"))
        return json(200, current.profile);
      if (request.method === "GET" && request.url.includes("/sources"))
        return json(200, { items: [], next_cursor: null });
      const next = puts.shift();
      if (next === undefined) throw new Error("unscripted request");
      if (next instanceof Error) throw next;
      return next;
    },
  });
  return sent;
}

function renderEditor(profile: ProfileOut) {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queries}>
      <EvidenceProvider>
        <ProfileEditor workspaceId={WS} profile={profile} />
        <EvidenceDrawer />
      </EvidenceProvider>
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

beforeEach(() => {
  configureApiClient(async () => "token");
  // Node's Request (used under jsdom) needs an absolute URL; a browser resolves "/api" itself.
  client.setConfig({ baseUrl: "http://localhost:3000/api" });
});

describe("[DUR-04][API-04] saving the profile is an expected-version, idempotent command", () => {
  it("sends the loaded version with a key, and shows the new version", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    const sent = api(current, [json(201, profileOut(2, ["Leeds"]))]);
    const user = renderEditor(current.profile);

    await user.clear(screen.getByRole("textbox", { name: "Work area 1" }));
    await user.type(screen.getByRole("textbox", { name: "Work area 1" }), "Leeds");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByText("Saved as version 2.")).toBeInTheDocument();
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

  it("keeps the edits after a stale save, names what changed, and saves on the new version", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    const sent = api(current, [stale, json(201, profileOut(3, ["Leeds"]))]);
    const user = renderEditor(current.profile);
    current.profile = {
      ...profileOut(2, ["Manchester"]),
      document: {
        ...documentWith(["Manchester"]),
        direct_spend_cap: {
          state: "provided",
          value: { minor_units: 90000, currency: "GBP" },
          source_ref_id: SRC,
        },
      },
    };

    await user.clear(screen.getByRole("textbox", { name: "Work area 1" }));
    await user.type(screen.getByRole("textbox", { name: "Work area 1" }), "Leeds");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    expect(
      await screen.findByText("Version 2 was saved while you were editing"),
    ).toBeInTheDocument();
    expect(screen.getByText(/Version 2 changed: Total spending limit/)).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Work area 1" })).toHaveValue("Leeds");

    await user.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Saved as version 3.")).toBeInTheDocument();
    const puts = sent.filter((request) => request.method === "PUT");
    expect(puts.map((put) => (put.body as { expected_version: number }).expected_version)).toEqual([
      1, 2,
    ]);
    expect(puts[0]?.key).not.toBe(puts[1]?.key); // a different request needs a new key
  });

  it("retries a failed send of the same change with the same key", async () => {
    const current = { profile: profileOut(1, ["Manchester"]) };
    const sent = api(current, [new TypeError("network"), json(201, profileOut(2, ["York"]))]);
    const user = renderEditor(current.profile);

    await user.clear(screen.getByRole("textbox", { name: "Work area 1" }));
    await user.type(screen.getByRole("textbox", { name: "Work area 1" }), "York");
    await user.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Nessa's service isn't reachable")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Saved as version 2.")).toBeInTheDocument();
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
