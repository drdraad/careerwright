import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { RouteDetail, RouteStep } from "@/generated/api";
import { routeDetailFixture } from "@/test/routeDetailData";
import { completePlanningRoute } from "@/test/routeStateData";
import { RouteJourney } from "./RouteJourney";

const first = routeDetailFixture.steps[0];
if (!first) throw new Error("Missing route test step");
const course = first;
const route = (steps: RouteStep[], index = 1): RouteDetail => ({
  ...routeDetailFixture,
  schedule: { ...routeDetailFixture.schedule, index },
  steps,
});
const props = {
  selectedIndex: 1,
  onSelect: vi.fn(),
  targetTitle: "Registered nurse",
  startLabel: "Your experience today",
};

const expand = async (index = 1) => {
  const buttons = Array.from(document.querySelectorAll<HTMLButtonElement>(".route-journey-choice"));
  const button = buttons.find((item) => item.textContent?.startsWith(`Route ${index + 1}`));
  if (!button) throw new Error("Missing route control");
  await userEvent.click(button);
};

afterEach(() => {
  Reflect.deleteProperty(HTMLElement.prototype, "animate");
  vi.unstubAllGlobals();
});

describe("a bounded journey preserves computed route meaning", () => {
  it("allows inspected details to scroll into view while expansion and collapse preserve the map's scroll", async () => {
    const focus = vi.spyOn(HTMLElement.prototype, "focus");
    render(<RouteJourney {...props} selectedIndex={0} routes={[completePlanningRoute]} />);
    await expand(0);
    expect(focus).toHaveBeenLastCalledWith({ preventScroll: true });
    await userEvent.click(screen.getByRole("button", { name: /Reporting practice/ }));
    expect(screen.getByRole("heading", { name: "Reporting practice" })).toHaveFocus();
    expect(focus.mock.lastCall?.[0]).toBeUndefined();
    await userEvent.click(screen.getByRole("button", { name: /Collapse route/ }));
    expect(focus).toHaveBeenLastCalledWith({ preventScroll: true });
    focus.mockRestore();
  });
  it("marks a particular missing fact and keeps its inspection through saved-result updates", async () => {
    const { rerender } = render(
      <RouteJourney {...props} selectedIndex={0} routes={[completePlanningRoute]} />,
    );
    await expand(0);
    const node = screen.getByRole("button", { name: /Reporting practice/ });
    const position = node.getAttribute("style");
    await userEvent.click(node);
    expect(node).toHaveAttribute("data-planning-state", "complete");
    const updated = {
      ...completePlanningRoute,
      schedule: { ...completePlanningRoute.schedule, index: 7 },
      steps: completePlanningRoute.steps.map((step) => ({
        ...step,
        weekly_hours: null,
        sources: [],
      })),
    };
    rerender(<RouteJourney {...props} selectedIndex={7} routes={[updated]} status="stale" />);
    const updatedNode = screen.getByRole("button", { name: /Reporting practice/ });
    expect(updatedNode).toHaveAttribute("data-inspected", "true");
    expect(updatedNode).toHaveAttribute("data-planning-state", "partial");
    expect(updatedNode.getAttribute("style")).toBe(position);
    expect(within(updatedNode).getByText("Weekly hours unknown")).toBeVisible();
    expect(screen.getByRole("heading", { name: "Reporting practice" })).toHaveFocus();
    expect(screen.getByRole("status")).toHaveTextContent("Saved results need updating");
    expect(screen.getByText("No source citations recorded.")).toBeVisible();
  });

  it("collapses a removed meaningful route without inspecting a replacement at the same index", async () => {
    const { rerender } = render(
      <RouteJourney {...props} selectedIndex={0} routes={[completePlanningRoute]} revealSelected />,
    );
    await userEvent.click(screen.getByRole("button", { name: /Reporting practice/ }));
    const replacement = {
      ...completePlanningRoute,
      steps: completePlanningRoute.steps.map((step) => ({
        ...step,
        variant_id: "different-course",
        title: "Replacement course",
      })),
    };
    rerender(<RouteJourney {...props} selectedIndex={0} routes={[replacement]} revealSelected />);
    expect(screen.queryByRole("button", { name: /Replacement course/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Reporting practice" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Route 1 Selected" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("shows complete planning information while keeping source checks, a place condition and completion separate", async () => {
    render(
      <RouteJourney
        {...props}
        selectedIndex={0}
        routes={[completePlanningRoute]}
        completedSteps={["fictional-course"]}
        planIndex={0}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Planning information complete");
    await expand(0);
    const node = screen.getByRole("button", { name: /Reporting practice/ });
    expect(node).toHaveAttribute("data-planning-state", "complete");
    expect(within(node).getByText("Place needed")).toBeVisible();
    await userEvent.click(node);
    expect(
      screen.getByText(/Source verification and current availability are separate checks/),
    ).toBeVisible();
    expect(screen.getByText(/This does not verify acquired skills or credentials/)).toBeVisible();
    expect(screen.getByText(/Evidence and supplied figures still need review/)).toBeVisible();
  });

  it("keeps a destination visible for a confirmed unsupported result without inventing readiness", () => {
    const { container } = render(<RouteJourney {...props} routes={[]} status="unsupported" />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "No supported route found in this monthly model",
    );
    expect(screen.getByRole("button", { name: /Registered nurse/ })).toBeVisible();
    expect(container.querySelector('g[data-route-state="unsupported"] path')).toBeInTheDocument();
    expect(screen.queryByText(/June 2028/)).not.toBeInTheDocument();
  });

  it("respects calm stillness for inspected steps without losing keyboard focus", async () => {
    const animate = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "animate", { configurable: true, value: animate });
    render(
      <div className="career-workspace" data-still="true">
        <RouteJourney {...props} selectedIndex={0} routes={[completePlanningRoute]} />
      </div>,
    );
    await expand(0);
    await userEvent.click(screen.getByRole("button", { name: /Reporting practice/ }));
    expect(animate).not.toHaveBeenCalled();
    expect(screen.getByRole("heading", { name: "Reporting practice" })).toHaveFocus();
  });
  it("uses actual granted prerequisites rather than array order, leaving parallel steps beside each other", async () => {
    const prerequisite = { ...course, grants: ["credential:nursing"] };
    const job: RouteStep = {
      ...course,
      variant_id: "job",
      kind: "work",
      title: "Supervised clinical role",
      start_month: "2030-09",
      prerequisites: ["credential:nursing"],
      grants: [],
    };
    const independent = { ...course, variant_id: "independent", title: "Independent course" };
    const { container } = render(
      <RouteJourney {...props} routes={[route([job, prerequisite, independent])]} />,
    );
    await expand();
    expect(container.querySelectorAll('path[data-kind="prerequisite"]')).toHaveLength(1);
    const courseNode = screen.getByRole("button", { name: /Nursing degree/ });
    const jobNode = screen.getByRole("button", { name: /Supervised clinical role/ });
    const independentNode = screen.getByRole("button", { name: /Independent course/ });
    expect(courseNode.style.top).not.toBe(independentNode.style.top);
    expect(Number.parseFloat(jobNode.style.left)).toBeGreaterThan(
      Number.parseFloat(courseNode.style.left),
    );
    expect(Number.parseFloat(jobNode.style.left)).toBeGreaterThan(
      Number.parseFloat(independentNode.style.left),
    );
    await userEvent.click(screen.getByText("Read route steps and dependencies"));
    expect(screen.getByText(/Prerequisite can come from: Nursing degree/)).toBeVisible();
  });

  it("keeps missing payments unknown and exposes dates, conditions and source citations on inspection", async () => {
    render(<RouteJourney {...props} routes={[route([course])]} />);
    await expand();
    const node = screen.getByRole("button", { name: /Nursing degree/ });
    expect(within(node).getByText("Payments unknown")).toBeVisible();
    expect(within(node).getByText("Loan approval needed")).toBeVisible();
    await userEvent.click(node);
    const inspector = document.querySelector(".route-journey-inspector");
    if (!(inspector instanceof HTMLElement)) throw new Error("Missing inspector");
    expect(within(inspector).getByText("Payments not recorded.")).toBeVisible();
    expect(within(inspector).queryByText(/£0/)).not.toBeInTheDocument();
    expect(within(inspector).getByText(/1 September 2027 – 1 July 2030/)).toBeVisible();
    expect(
      within(inspector).getByText(/Needs the loan to be approved and repaid later/),
    ).toBeVisible();
    await userEvent.click(screen.getByText("Source excerpts (1)"));
    expect(within(inspector).getByText("The course starts in September.")).toBeVisible();
    expect(within(inspector).getByText("Read 1 October 2026")).toBeVisible();
  });

  it("shows identical scheduled steps once in an expanded route without merging different dates", async () => {
    const sameStep = { ...course };
    const later = { ...course, start_date: "2028-09-01", start_month: "2028-09" };
    render(<RouteJourney {...props} routes={[route([course, sameStep, later])]} />);
    await expand();
    expect(screen.getAllByRole("button", { name: /Nursing degree/ })).toHaveLength(2);
  });

  it("keeps inspected steps, compared routes, saved plans and self-reported completion distinct", async () => {
    const onSelect = vi.fn();
    render(
      <RouteJourney
        {...props}
        onSelect={onSelect}
        planIndex={0}
        completedSteps={[course.variant_id]}
        routes={[route([course], 0), route([course], 1)]}
      />,
    );
    const saved = screen.getByRole("button", { name: "Route 1 Saved plan" });
    const compared = screen.getByRole("button", { name: "Route 2 Selected" });
    expect(saved).toHaveAttribute("aria-pressed", "false");
    expect(within(saved).getByText("Saved plan")).toBeVisible();
    expect(compared).toHaveAttribute("aria-pressed", "true");
    await expand();
    onSelect.mockClear();
    const node = screen.getByRole("button", { name: /Nursing degree/ });
    node.focus();
    await userEvent.keyboard("{Enter}");
    expect(node).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("heading", { name: "Nursing degree" })).toHaveFocus();
    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.getByText(/This does not verify acquired skills or credentials/)).toBeVisible();
    await userEvent.click(saved);
    expect(onSelect).toHaveBeenCalledWith(0);
  });

  it("supports immediate readiness without inventing training or a job offer", async () => {
    const { container } = render(<RouteJourney {...props} routes={[route([])]} />);
    await expand();
    expect(container.querySelectorAll(".route-journey-node")).toHaveLength(2);
    expect(
      screen.getByRole("button", { name: /Starting point.*Your experience today/ }),
    ).toBeVisible();
    await userEvent.click(
      screen.getByRole("button", { name: /Modelled readiness.*Registered nurse/ }),
    );
    expect(screen.getByText(/It does not guarantee a vacancy, a job offer/)).toBeVisible();
    await userEvent.click(screen.getByText("Read route steps and dependencies"));
    expect(screen.getByText(/No additional training or job steps/)).toBeVisible();
  });

  it("starts with bundles, expands one route, and restores toolbar focus on collapse", async () => {
    const onSelect = vi.fn();
    const routes = [0, 1, 2, 3].map((index) =>
      route([{ ...course, variant_id: `course-${index}`, title: `Course ${index}` }], index),
    );
    const { container, rerender } = render(
      <RouteJourney {...props} routes={routes} onSelect={onSelect} />,
    );
    expect(container.querySelectorAll(".route-journey-bundle")).toHaveLength(3);
    expect(container.querySelectorAll('[data-kind="learning"]')).toHaveLength(0);
    await userEvent.click(screen.getByRole("button", { name: /Collapsed route Route 2/ }));
    expect(onSelect).toHaveBeenLastCalledWith(1);
    expect(screen.getByRole("button", { name: /Course 1.*Payments unknown/ })).toBeVisible();
    expect(container.querySelectorAll(".route-journey-bundle")).toHaveLength(2);
    await expand(3);
    expect(screen.getByRole("button", { name: /Course 3.*Payments unknown/ })).toBeVisible();
    expect(
      screen.queryByRole("button", { name: /Course 1.*Payments unknown/ }),
    ).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Collapse route/ }));
    expect(container.querySelectorAll('[data-kind="learning"]')).toHaveLength(0);
    expect(screen.getByRole("button", { name: "Route 4" })).toHaveFocus();
    await expand(3);
    rerender(
      <RouteJourney {...props} targetTitle="Another target" routes={routes} onSelect={onSelect} />,
    );
    expect(container.querySelectorAll('[data-kind="learning"]')).toHaveLength(0);
  });

  it("draws curved trails joined to actual beacons within a bounded width", async () => {
    const { container } = render(
      <RouteJourney
        {...props}
        routes={[
          route([course], 0),
          route([{ ...course, variant_id: "other", title: "Other course" }], 1),
        ]}
      />,
    );
    await expand();
    const origin = screen.getByRole("button", { name: /Starting point/ });
    const target = screen.getByRole("button", { name: /Modelled readiness/ });
    expect([origin.style.left, origin.style.top]).toEqual(["12%", "82%"]);
    expect([target.style.left, target.style.top]).toEqual(["85%", "26%"]);
    const svg = container.querySelector("svg");
    const [width, height] = (svg?.getAttribute("viewBox") ?? "").split(" ").slice(2).map(Number);
    if (!width || !height) throw new Error("Missing journey dimensions");
    expect(width).toBeLessThanOrEqual(700);
    const landmarks = Array.from(container.querySelectorAll<HTMLElement>(".route-journey-node"));
    const points = landmarks.map((node) => [
      (Number.parseFloat(node.style.left) / 100) * width,
      (Number.parseFloat(node.style.top) / 100) * height,
    ]);
    const paths = container.querySelectorAll("path[data-kind]");
    expect(paths).toHaveLength(4);
    expect(container.querySelectorAll(".route-journey-aura")).toHaveLength(4);
    for (const path of paths) {
      const d = path.getAttribute("d") ?? "";
      expect(d).toContain(" C");
      const coordinates = d.match(/-?\d+(?:\.\d+)?/g)?.map(Number) ?? [];
      expect(points).toContainEqual(coordinates.slice(0, 2));
      expect(points).toContainEqual(coordinates.slice(-2));
    }
    expect(landmarks.every((node) => node.querySelector(".route-journey-beacon"))).toBe(true);
    expect(screen.getByText(/Distance is layout, not duration or probability/)).toBeVisible();
  });

  it("labels an explicitly supplied zero fee without treating it as a verified price", async () => {
    const zeroFee = {
      ...course,
      payments: [
        {
          kind: "fee" as const,
          amount: { minor_units: 0, currency: "GBP" as const },
          due: null,
          month: null,
        },
      ],
    };
    render(<RouteJourney {...props} routes={[route([zeroFee])]} />);
    await expand();
    expect(screen.getByText("Quote unknown")).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: /Nursing degree/ }));
    expect(screen.getByText(/£0 supplied fee/)).toBeVisible();
  });

  it("places the computed assessment verification on its trail without claiming it has been passed", async () => {
    const computed = route([course]);
    computed.milestones = [
      { kind: "verify_assessed_completion", month: "2030-08", months_to_readiness: 35 },
    ];
    const { container } = render(<RouteJourney {...props} routes={[computed]} />);
    expect(container.querySelectorAll('[data-kind="verification"]')).toHaveLength(0);
    await expand();
    expect(container.querySelectorAll('[data-kind="verification"]')).toHaveLength(1);
    const gate = screen.getByRole("button", { name: /Verify assessed outcome/ });
    await userEvent.click(gate);
    expect(screen.getByRole("heading", { name: "Verify assessed outcome" })).toHaveFocus();
    expect(
      screen.getByText(
        /No passed assessment, provider confirmation or verification fee is recorded here/,
      ),
    ).toBeVisible();
    expect(screen.getByText(/verified in August 2030/)).toBeVisible();
  });
  it("follows parent route selection only while a route is expanded", async () => {
    const routes = [
      route([{ ...course, title: "First course" }], 0),
      route([{ ...course, title: "Second course" }], 1),
    ];
    const { rerender } = render(<RouteJourney {...props} routes={routes} />);
    rerender(<RouteJourney {...props} routes={routes} selectedIndex={0} />);
    expect(screen.queryByRole("button", { name: /First course/ })).not.toBeInTheDocument();
    await expand(0);
    await userEvent.click(screen.getByRole("button", { name: /First course/ }));
    expect(screen.getByRole("heading", { name: "First course" })).toBeVisible();
    rerender(<RouteJourney {...props} routes={routes} selectedIndex={1} />);
    expect(screen.getByRole("button", { name: /Second course/ })).toBeVisible();
    expect(screen.queryByRole("button", { name: /First course/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "First course" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Route 2 Viewing" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });

  it("reveals the inspected job without moving the map, cancels motion, and respects live preferences", async () => {
    const cancel = vi.fn();
    const animate = vi.fn(() => ({ cancel }));
    Object.defineProperty(HTMLElement.prototype, "animate", { configurable: true, value: animate });
    const preference = Object.assign(new EventTarget(), { matches: false });
    vi.stubGlobal(
      "matchMedia",
      vi.fn(() => preference),
    );
    const job = { ...course, variant_id: "job", kind: "work" as const, title: "Clinical role" };
    const { container, unmount } = render(
      <RouteJourney {...props} routes={[route([course, job])]} />,
    );
    await expand();
    const jobNode = screen.getByRole("button", { name: /Clinical role/ });
    const position = jobNode.getAttribute("style");
    await userEvent.click(jobNode);
    expect(jobNode).toHaveAttribute("data-inspected", "true");
    expect(jobNode.getAttribute("style")).toBe(position);
    expect(screen.getByRole("heading", { name: "Clinical role" })).toHaveFocus();
    expect(container.querySelector(".route-journey-inspector")).toHaveAttribute(
      "data-inspecting",
      "true",
    );
    expect(animate).toHaveBeenCalledOnce();
    expect(animate.mock.instances[0]).toBe(container.querySelector(".route-journey-inspector"));
    expect(animate).toHaveBeenCalledWith(
      [
        { opacity: 0.4, transform: "translateY(6px)" },
        { opacity: 1, transform: "translateY(0)" },
      ],
      { duration: 220, easing: "ease-out" },
    );
    preference.matches = true;
    act(() => preference.dispatchEvent(new Event("change")));
    expect(cancel).toHaveBeenCalledOnce();
    await userEvent.click(screen.getByRole("button", { name: /Nursing degree/ }));
    expect(jobNode).toHaveAttribute("data-inspected", "false");
    expect(screen.getByRole("heading", { name: "Nursing degree" })).toHaveFocus();
    expect(animate).toHaveBeenCalledOnce();
    preference.matches = false;
    await userEvent.click(jobNode);
    expect(animate).toHaveBeenCalledTimes(2);
    unmount();
    expect(cancel).toHaveBeenCalledTimes(3);
  });
});
