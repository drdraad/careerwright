import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ComparisonOut } from "@/generated/api";
import { RouteChart } from "./RouteChart";

const comparison = {
  basis: { horizon_months: 24, objective_basis: "economic" },
  points_shown: 2,
  points_total: 2,
  points: [
    {
      point_id: 1,
      months_to_readiness: 4,
      objective_cost: { minor_units: 200000, currency: "GBP" },
      layer: 1,
      schedule_count: 1,
      schedules: [3],
    },
    {
      point_id: 2,
      months_to_readiness: 8,
      objective_cost: { minor_units: -50000, currency: "GBP" },
      layer: 2,
      schedule_count: 2,
      schedules: [7],
    },
  ],
} as ComparisonOut;

describe("[VIS2-01] the scatter uses the solver's time, cost and layer", () => {
  it("shows exact signed costs and lets a keyboard user choose a route from a point", async () => {
    const select = vi.fn();
    render(<RouteChart comparison={comparison} select={select} />);

    expect(screen.getByRole("img", { name: /months until ready and total cost/i })).toBeVisible();
    expect(screen.getByText("2 of 2 points shown.", { exact: false })).toBeVisible();
    await userEvent.click(screen.getByText("Choose a point by its exact time and cost"));
    await userEvent.click(
      screen.getByRole("button", { name: "Point 2: 8 months, −£500, F2, 2 routes" }),
    );

    expect(select).toHaveBeenCalledWith(7);
  });
});
