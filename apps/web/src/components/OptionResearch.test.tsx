import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { fakeApi, type Route } from "@/test/fakeApi";
import { optionEstimate, optionResearch, optionRun } from "@/test/optionResearchData";
import { OptionResearch } from "./OptionResearch";

const profile = {
  version: 4,
  document: { cities: { state: "provided", value: ["Leeds", "York"] } },
};

function shown(extra: Route[], researches: object[] = []) {
  const sent = fakeApi([
    { method: "GET", path: /\/profile$/, answer: profile },
    { method: "GET", path: /\/credentials$/, answer: { items: [{ active: true }] } },
    { method: "GET", path: /\/option-research\/estimate$/, answer: optionEstimate },
    { method: "GET", path: /\/option-research$/, answer: researches },
    ...extra,
  ]);
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <OptionResearch workspaceId="w1" target="Data quality analyst" />
    </QueryClientProvider>,
  );
  return sent;
}

describe("[OPTN-12][SEC-05] option research sends only one target and city", () => {
  it("shows the combined estimate before a start and sends the profile version shown", async () => {
    const sent = shown([
      {
        method: "POST",
        path: /\/option-research$/,
        status: 202,
        answer: {
          ...optionResearch,
          status: "searching",
          search: optionRun("search-id", "running"),
          reading: null,
          records: [],
        },
      },
    ]);
    expect(await screen.findByText(/Estimated model spending: up to \$0\.14/)).toBeVisible();
    await userEvent.selectOptions(screen.getByLabelText("City to search from"), "York");
    await userEvent.click(screen.getByRole("button", { name: "Find options for this role" }));
    await waitFor(() => expect(sent.some((item) => item.method === "POST")).toBe(true));
    expect(sent.find((item) => item.method === "POST")?.body).toEqual({
      expected_profile_version: 4,
      target: "Data quality analyst",
      city: "York",
    });
  });

  it("starts page reading once from ready_to_read without asking for a second decision", async () => {
    const ready = {
      ...optionResearch,
      status: "ready_to_read" as const,
      reading: null,
      records: [],
    };
    const sent = shown(
      [
        {
          method: "POST",
          path: /\/option-research\/[^/]+\/reading$/,
          status: 202,
          answer: { ...ready, status: "reading" },
        },
      ],
      [ready],
    );
    await waitFor(() =>
      expect(sent.filter((item) => item.path.endsWith("/reading"))).toHaveLength(1),
    );
    expect(screen.getByText(/Careerwright is starting its page checks/)).toBeVisible();
  });

  it("cancels the current reading run through the existing run command", async () => {
    const sent = shown(
      [
        {
          method: "POST",
          path: /\/runs\/reading-id\/cancel$/,
          answer: { run_id: "reading-id" },
        },
      ],
      [
        {
          ...optionResearch,
          status: "reading",
          reading: optionRun("reading-id", "running", "acquisition"),
        },
      ],
    );
    await userEvent.click(await screen.findByRole("button", { name: "Stop research" }));
    await waitFor(() =>
      expect(sent.some((item) => item.path.endsWith("/runs/reading-id/cancel"))).toBe(true),
    );
  });
});
