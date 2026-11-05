import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fakeApi } from "@/test/fakeApi";
import { p01Profile } from "@/test/p01DesignData";
import { planRoute, savedPlan } from "@/test/planData";
import { ChapterView } from "./ChapterView";
import { EvidenceProvider } from "./EvidenceDrawer";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(window.location.search),
}));
vi.mock("./WorkspaceShell", () => ({
  useWorkspaceData: () => ({
    workspace: { workspace_id: "workspace" },
    profile: p01Profile,
    journey: { progress: { plan: "available", routes: "available" } },
    planCandidate: true,
  }),
}));

function wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={new QueryClient()}>
      <EvidenceProvider>{children}</EvidenceProvider>
    </QueryClientProvider>
  );
}

afterEach(() => window.history.replaceState({}, "", "/"));

describe("[PLAN-01][STATE-06] navigation within a chapter", () => {
  it("opens the new route and resets its confirmation when the plan link changes", async () => {
    const runId = savedPlan.source.solve_run_id;
    window.history.replaceState({}, "", `/?solve_run_id=${runId}&schedule_index=1`);
    const alternate = {
      ...planRoute,
      schedule: { ...planRoute.schedule, index: 2 },
      steps: planRoute.steps.map((step) => ({ ...step, title: "Alternate course" })),
    };
    fakeApi([
      {
        method: "GET",
        path: /\/planning\/solves\/[^/]+$/,
        answer: { run: { run_id: runId, status: "complete" } },
      },
      { method: "GET", path: /\/schedules\/1$/, answer: planRoute },
      { method: "GET", path: /\/schedules\/2$/, answer: alternate },
    ]);
    const { rerender } = render(<ChapterView chapter="plan" />, { wrapper });
    const confirm = await screen.findByRole("checkbox", { name: /I have reviewed this route/ });
    await userEvent.click(confirm);
    expect(confirm).toBeChecked();

    window.history.replaceState({}, "", `/?solve_run_id=${runId}&schedule_index=2`);
    rerender(<ChapterView chapter="plan" />);

    const route = await screen.findByRole("region", { name: "Route to choose" });
    expect(await within(route).findByText("Alternate course")).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: /I have reviewed this route/ })).not.toBeChecked();
  });

  it("opens the linked destination when the target query changes on Routes", async () => {
    window.history.replaceState({}, "", "/?target=Nurse");
    fakeApi([
      {
        method: "GET",
        path: /\/planning\/checkpoint$/,
        answer: {
          inputs_version: 1,
          needs: [],
          targets: ["Nurse", "Analyst"].map((target_title) => ({ target_title, options: [] })),
        },
      },
      { method: "GET", path: /\/runs$/, answer: { items: [], next_cursor: null } },
    ]);
    const { rerender } = render(<ChapterView chapter="routes" />, { wrapper });
    expect(await screen.findByRole("combobox", { name: "Destination" })).toHaveValue("Nurse");

    window.history.replaceState({}, "", "/?target=Analyst");
    rerender(<ChapterView chapter="routes" />);

    expect(await screen.findByRole("combobox", { name: "Destination" })).toHaveValue("Analyst");
  });
});
