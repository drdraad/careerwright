import { describe, expect, it } from "vitest";
import { p01Plan } from "@/test/p01DesignData";
import { routeDetailFixture } from "@/test/routeDetailData";
import { completePlanningRoute } from "@/test/routeStateData";
import {
  planningState,
  routeIdentity,
  routeMissingFacts,
  stepMissingFacts,
  targetRouteState,
} from "./routeState";

describe("route planning information states", () => {
  it("keeps complete information separate from unreviewed sources and an unmet place condition", () => {
    expect(routeMissingFacts(completePlanningRoute)).toEqual([]);
    expect(planningState(completePlanningRoute)).toBe("complete");
    expect(completePlanningRoute.schedule.conditions[0]?.verification).toBe("confirm_admission");
    expect(completePlanningRoute.steps[0]?.records[0]?.review_state).toBe("proposed");
  });

  it("names missing consequential facts without inventing costs or accepting readiness placeholders", () => {
    const course = completePlanningRoute.steps[0];
    if (!course) throw new Error("Missing fictional course");
    expect(
      stepMissingFacts({
        ...course,
        start_date: null,
        start_month: null,
        weekly_hours: null,
        payments: [],
      }),
    ).toEqual(["Start date unknown", "Weekly hours unknown", "Payments unknown"]);
    const route = {
      ...completePlanningRoute,
      schedule: { ...completePlanningRoute.schedule, verdict: "unresolved" as const },
      gates: completePlanningRoute.gates.map((gate) => ({ ...gate, month: null })),
    };
    expect(routeMissingFacts(route)).toEqual(["Readiness not assessed", "Gate date unknown"]);
    expect(planningState(routeDetailFixture)).toBe("partial");
  });

  it("keeps P01's hypothetical assessed SQL outcome partial", () => {
    expect(routeMissingFacts(p01Plan.route)).toContain("Planned skill outcome still an assumption");
    expect(planningState(p01Plan.route)).toBe("partial");
  });

  it("supports a computed direct route without requiring a course", () => {
    const direct = {
      ...completePlanningRoute,
      steps: [],
      gates: [],
      schedule: { ...completePlanningRoute.schedule, route: [], conditions: [] },
    };
    expect(targetRouteState([direct], "available")).toBe("complete");
    expect(targetRouteState([], "unsupported")).toBe("unsupported");
    expect(targetRouteState([])).toBe("not_searched");
    expect(targetRouteState([], "available")).toBe("pending");
  });

  it.each(["pending", "stale", "error", "limited", "unloaded", "unresolved"] as const)(
    "preserves %s even with previously loaded complete details",
    (status) => {
      expect(targetRouteState([completePlanningRoute], status)).toBe(status);
    },
  );

  it("keeps meaningful identity stable through source, cost, review and schedule-index updates", () => {
    expect(
      routeIdentity({
        ...completePlanningRoute,
        schedule: { ...completePlanningRoute.schedule, index: 12 },
        costs: { ...completePlanningRoute.costs, direct_cost: null },
        steps: completePlanningRoute.steps.map((step) => ({ ...step, sources: [], records: [] })),
      }),
    ).toBe(routeIdentity(completePlanningRoute));
    expect(
      routeIdentity({
        ...completePlanningRoute,
        steps: completePlanningRoute.steps.map((step) => ({ ...step, start_month: "2028-01" })),
      }),
    ).not.toBe(routeIdentity(completePlanningRoute));
  });
});
