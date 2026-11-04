import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { savedPlan } from "@/test/planData";
import { PlanProgress } from "./PlanProgress";

describe("[PLAN-03] progress is a self-report, separate from evidence", () => {
  it("does not present a zero-step route as completion progress", () => {
    render(
      <PlanProgress
        plan={{ ...savedPlan, route: { ...savedPlan.route, steps: [] } }}
        onUpdate={vi.fn()}
        busy={false}
        error={null}
      />,
    );
    expect(screen.getByText("This route has no training steps to track.")).toBeVisible();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("records completion and commitment against the current plan version", async () => {
    const onUpdate = vi.fn();
    render(<PlanProgress plan={savedPlan} onUpdate={onUpdate} busy={false} error={null} />);
    expect(screen.getByText(/they do not verify a skill/)).toBeVisible();

    await userEvent.click(screen.getByRole("button", { name: "Report step complete" }));
    await userEvent.click(screen.getByRole("button", { name: "Record my commitment" }));

    expect(onUpdate).toHaveBeenNthCalledWith(1, {
      expected_version: 1,
      kind: "step_completed",
      variant_id: "step-1",
    });
    expect(onUpdate).toHaveBeenNthCalledWith(2, {
      expected_version: 1,
      kind: "commitment_accepted",
      variant_id: "step-1",
    });
  });

  it("records rest, resumption and review dates without changing route dates", async () => {
    const onUpdate = vi.fn();
    render(
      <PlanProgress
        plan={{
          ...savedPlan,
          progress: { completed_steps: [], rest_until: "2027-01-01", activity: [] },
        }}
        onUpdate={onUpdate}
        busy={false}
        error={null}
      />,
    );
    expect(screen.getByText(/it does not move route dates/)).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Resume planning" }));
    fireEvent.change(screen.getByLabelText("Rest from planning until"), {
      target: { value: "2027-02-01" },
    });
    await userEvent.click(screen.getByRole("button", { name: "Record rest" }));
    fireEvent.change(screen.getByLabelText("Review this plan on"), {
      target: { value: "2027-03-01" },
    });
    await userEvent.click(screen.getByRole("button", { name: "Set review date" }));
    expect(onUpdate.mock.calls.map(([body]) => body)).toEqual([
      { expected_version: 1, kind: "resume" },
      { expected_version: 1, kind: "rest", until: "2027-02-01" },
      { expected_version: 1, kind: "review_rescheduled", until: "2027-03-01" },
    ]);
  });

  it("lets a mistaken completion be corrected and keeps the historical step title", async () => {
    const onUpdate = vi.fn();
    render(
      <PlanProgress
        plan={{
          ...savedPlan,
          progress: {
            completed_steps: ["step-1"],
            activity: [
              {
                kind: "step_completed",
                variant_id: "step-1",
                step_title: "Earlier course title",
                until: null,
                recorded_at: "2026-11-03T12:00:00Z",
              },
            ],
          },
        }}
        onUpdate={onUpdate}
        busy={false}
        error={null}
      />,
    );
    await userEvent.click(screen.getByText("Activity you reported"));
    expect(screen.getByText(/step completed — Earlier course title/)).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Correct completion report" }));
    expect(onUpdate).toHaveBeenCalledWith({
      expected_version: 1,
      kind: "step_retracted",
      variant_id: "step-1",
    });
  });

  it("lets an active commitment be corrected while keeping its report visible", async () => {
    const onUpdate = vi.fn();
    render(
      <PlanProgress
        plan={{
          ...savedPlan,
          commitments: ["step-1"],
          progress: {
            completed_steps: [],
            activity: [
              {
                kind: "commitment_accepted",
                variant_id: "step-1",
                step_title: "Earlier course title",
                until: null,
                recorded_at: "2026-11-03T12:00:00Z",
              },
            ],
          },
        }}
        onUpdate={onUpdate}
        busy={false}
        error={null}
      />,
    );
    await userEvent.click(screen.getByText("Activity you reported"));
    expect(screen.getByText(/commitment accepted — Earlier course title/)).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Correct commitment report" }));
    expect(onUpdate).toHaveBeenCalledWith({
      expected_version: 1,
      kind: "commitment_retracted",
      variant_id: "step-1",
    });
  });
});
