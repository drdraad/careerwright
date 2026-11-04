import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { routeDetailFixture } from "@/test/routeDetailData";
import { expansionTargets } from "@/test/routeExpansionData";
import { completePlanningRoute, planningStateTargets } from "@/test/routeStateData";
import { type JourneyTarget, RouteExplorer } from "./RouteExplorer";

const targets: JourneyTarget[] = ["Care coordinator", "Data analyst", "Learning designer"].map(
  (title, index) => ({
    id: `target-${index}`,
    title,
    routes: [0, 1].map((routeIndex) => ({
      ...routeDetailFixture,
      schedule: { ...routeDetailFixture.schedule, index: routeIndex },
      steps: routeDetailFixture.steps.map((step) => ({
        ...step,
        title: `Shared course for ${title}`,
      })),
    })),
  }),
);
const beacon = (name: string) =>
  screen.getByRole("button", { name: new RegExp(`${name} 2 routes`) });

const mockTransitions = () => {
  const pending: {
    update: () => void;
    finish: () => void;
    skipTransition: ReturnType<typeof vi.fn>;
  }[] = [];
  const start = vi.fn((update: () => void) => {
    let finish = () => {};
    const finished = new Promise<void>((resolve) => {
      finish = resolve;
    });
    const skipTransition = vi.fn();
    pending.push({ update, finish, skipTransition });
    return { ready: Promise.resolve(), finished, skipTransition };
  });
  Object.defineProperty(document, "startViewTransition", { configurable: true, value: start });
  return { start, pending };
};

afterEach(() => {
  Reflect.deleteProperty(document, "startViewTransition");
  vi.unstubAllGlobals();
});

describe("destination expansion", () => {
  it("preserves document scroll in native focus and return updates without overriding later user scrolling", async () => {
    const { pending } = mockTransitions();
    vi.stubGlobal("scrollX", 7);
    vi.stubGlobal("scrollY", 181);
    const scrollTo = vi.fn((position: ScrollToOptions) => {
      vi.stubGlobal("scrollX", position.left);
      vi.stubGlobal("scrollY", position.top);
    });
    vi.stubGlobal("scrollTo", scrollTo);
    render(<RouteExplorer targets={targets} startLabel="Today" />);
    await userEvent.click(beacon("Data analyst"));
    act(() => {
      vi.stubGlobal("scrollY", 0);
      pending[0]?.update();
    });
    expect(scrollTo).toHaveBeenLastCalledWith({ left: 7, top: 181, behavior: "instant" });
    expect(screen.getByRole("button", { name: "All targets" })).toHaveFocus();
    vi.stubGlobal("scrollY", 240);
    await act(async () => pending[0]?.finish());
    expect(window.scrollY).toBe(240);
    expect(scrollTo).toHaveBeenCalledOnce();
    await userEvent.click(screen.getByRole("button", { name: "All targets" }));
    act(() => {
      vi.stubGlobal("scrollY", 0);
      pending[1]?.update();
    });
    expect(scrollTo).toHaveBeenLastCalledWith({ left: 7, top: 240, behavior: "instant" });
    expect(beacon("Data analyst")).toHaveFocus();
  });

  it("does not restore a stale native navigation's scroll position", async () => {
    const { pending } = mockTransitions();
    vi.stubGlobal("scrollX", 0);
    vi.stubGlobal("scrollY", 181);
    const scrollTo = vi.fn();
    vi.stubGlobal("scrollTo", scrollTo);
    render(<RouteExplorer targets={targets} startLabel="Today" />);
    await userEvent.click(beacon("Care coordinator"));
    await userEvent.click(beacon("Data analyst"));
    act(() => {
      vi.stubGlobal("scrollY", 0);
      pending[0]?.update();
    });
    expect(scrollTo).not.toHaveBeenCalled();
    act(() => pending[1]?.update());
    expect(scrollTo).toHaveBeenCalledOnce();
    expect(scrollTo).toHaveBeenCalledWith({ left: 0, top: 181, behavior: "instant" });
    expect(screen.getByRole("heading", { name: "Data analyst" })).toBeVisible();
  });
  it("unfolds an explicit controlled route on initial focus and when requested details arrive", () => {
    const target = {
      id: "controlled",
      title: "Controlled destination",
      routes: [completePlanningRoute],
    };
    const { rerender } = render(
      <RouteExplorer
        targets={[target]}
        startLabel="Today"
        activeTargetId="controlled"
        selectedIndex={0}
      />,
    );
    expect(screen.getByRole("button", { name: /Reporting practice/ })).toBeVisible();
    rerender(
      <RouteExplorer
        targets={[{ ...target, routes: [], detailStatus: "pending" }]}
        startLabel="Today"
        activeTargetId="controlled"
        selectedIndex={3}
      />,
    );
    expect(screen.queryByRole("button", { name: /Reporting practice/ })).not.toBeInTheDocument();
    rerender(
      <RouteExplorer
        targets={[
          {
            ...target,
            routes: [
              {
                ...completePlanningRoute,
                schedule: { ...completePlanningRoute.schedule, index: 3 },
              },
            ],
          },
        ]}
        startLabel="Today"
        activeTargetId="controlled"
        selectedIndex={3}
      />,
    );
    expect(screen.getByRole("button", { name: /Reporting practice/ })).toBeVisible();
    expect(screen.getByRole("button", { name: "Route 4 Viewing" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });

  it("reports actual counts separately from loaded details and keeps every destination's state honest", () => {
    const { container, rerender } = render(
      <RouteExplorer targets={planningStateTargets} startLabel="Today" />,
    );
    expect(
      screen.getByRole("button", { name: /Fictional regulated role 0 routes/ }),
    ).toHaveAttribute("data-route-state", "unsupported");
    expect(screen.getByRole("button", { name: /Fictional data role 2 routes/ })).toHaveAttribute(
      "data-route-state",
      "partial",
    );
    expect(
      screen.getByRole("button", { name: /Fictional reporting role 1 route/ }),
    ).toHaveAttribute("data-route-state", "complete");
    rerender(
      <RouteExplorer
        targets={[
          {
            id: "saved",
            title: "Saved destination",
            routes: [completePlanningRoute],
            scheduleCount: 125,
            status: "pending",
          },
        ]}
        startLabel="Today"
      />,
    );
    expect(screen.getByRole("button", { name: /Saved destination 125 routes/ })).toHaveTextContent(
      "1 route summary loaded",
    );
    expect(container.querySelector('g[data-route-state="pending"]')).toBeInTheDocument();
    expect(
      screen.queryByText("No supported route found in this monthly model"),
    ).not.toBeInTheDocument();
  });

  it("does not select an arriving result after opening an unloaded target", async () => {
    const target = {
      id: "saved",
      title: "Saved destination",
      routes: [],
      status: "unloaded" as const,
    };
    const { rerender } = render(<RouteExplorer targets={[target]} startLabel="Today" />);
    await userEvent.click(
      screen.getByRole("button", { name: /Saved destination Route count not checked/ }),
    );
    rerender(
      <RouteExplorer
        targets={[{ ...target, routes: [completePlanningRoute], status: "available" }]}
        startLabel="Today"
      />,
    );
    expect(screen.getByRole("button", { name: "Route 1" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.queryByRole("button", { name: /Reporting practice/ })).not.toBeInTheDocument();
  });

  it("consumes an explicit unfold request so later facts do not undo a person's collapse", async () => {
    const target = {
      id: "controlled",
      title: "Controlled destination",
      routes: [completePlanningRoute],
    };
    const { rerender } = render(
      <RouteExplorer
        targets={[target]}
        startLabel="Today"
        activeTargetId="controlled"
        selectedIndex={0}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /Collapse route/ }));
    rerender(
      <RouteExplorer
        targets={[
          {
            ...target,
            routes: [
              {
                ...completePlanningRoute,
                steps: completePlanningRoute.steps.map((step) => ({ ...step, sources: [] })),
              },
            ],
          },
        ]}
        startLabel="Today"
        activeTargetId="controlled"
        selectedIndex={0}
      />,
    );
    expect(screen.queryByRole("button", { name: /Reporting practice/ })).not.toBeInTheDocument();
  });

  it("stops an in-flight focus transition when support or calm stillness turns on", async () => {
    const { start, pending } = mockTransitions();
    const { rerender } = render(
      <div className="career-workspace" data-still="false">
        <RouteExplorer targets={targets} startLabel="Today" />
      </div>,
    );
    await userEvent.click(beacon("Data analyst"));
    rerender(
      <div className="career-workspace" data-still="true">
        <RouteExplorer targets={targets} startLabel="Today" />
      </div>,
    );
    await act(async () => {});
    expect(pending[0]?.skipTransition).toHaveBeenCalledOnce();
    act(() => pending[0]?.update());
    await userEvent.click(screen.getByRole("button", { name: "All targets" }));
    expect(start).toHaveBeenCalledOnce();
    expect(beacon("Data analyst")).toHaveFocus();
  });
  it("shows three destinations and counts shared steps once without drawing job transitions", async () => {
    const { container } = render(
      <RouteExplorer targets={targets} startLabel="Your experience today" />,
    );
    expect(container.querySelectorAll(".route-explorer-target")).toHaveLength(3);
    expect(container.querySelectorAll(".route-explorer-trail")).toHaveLength(3);
    expect(container.querySelector(".route-journey")).not.toBeInTheDocument();
    expect(
      within(beacon("Care coordinator")).getByText(/2 routes · 1 course, 0 job steps/),
    ).toBeVisible();
    expect(screen.getByText(/they do not represent direct job transitions/)).toBeVisible();
    await userEvent.click(screen.getByText("Read destinations and route summaries"));
    expect(screen.getByRole("button", { name: "Care coordinator: 2 routes" })).toBeVisible();
  });

  it("opens one destination with native keyboard controls and restores focus on return", async () => {
    render(<RouteExplorer targets={targets} startLabel="Your experience today" />);
    beacon("Care coordinator").focus();
    await userEvent.keyboard("{Enter}");
    expect(screen.getByRole("button", { name: "All targets" })).toHaveFocus();
    expect(screen.getByRole("button", { name: "Data analyst" })).toBeVisible();
    expect(document.querySelectorAll(".route-journey")).toHaveLength(1);
    expect(document.querySelectorAll(".route-journey-bundle")).toHaveLength(2);
    expect(screen.queryByRole("button", { name: /Shared course for/ })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "All targets" }));
    expect(beacon("Care coordinator")).toHaveFocus();
  });

  it("remembers each target’s inspected route without saving or completing it", async () => {
    render(<RouteExplorer targets={targets} startLabel="Your experience today" />);
    await userEvent.click(beacon("Care coordinator"));
    await userEvent.click(screen.getByRole("button", { name: "Route 2" }));
    expect(
      screen.getByRole("button", { name: /Shared course for Care coordinator/ }),
    ).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Data analyst" }));
    expect(document.querySelectorAll(".route-journey-bundle")).toHaveLength(2);
    await userEvent.click(screen.getByRole("button", { name: "Care coordinator" }));
    expect(screen.getByRole("button", { name: "Route 2 Viewing" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(
      screen.getByRole("button", { name: /Shared course for Care coordinator/ }),
    ).toBeVisible();
    expect(screen.queryByText("Saved plan")).not.toBeInTheDocument();
    expect(document.querySelector('[data-completed="true"]')).not.toBeInTheDocument();
  });
  it("expands the fictional two-offer job route without exposing placeholder readiness dates", async () => {
    const { container } = render(
      <RouteExplorer targets={expansionTargets} startLabel="Your experience today" />,
    );
    const target = screen.getByRole("button", { name: /Data quality analyst 2 routes/ });
    expect(target).toHaveAccessibleName(/Per route: Needs 2 offers/);
    expect(within(target).getByText(/2 routes · 2 courses, 4 job steps/)).toBeVisible();
    await userEvent.click(target);
    expect(screen.getByRole("button", { name: /Collapsed route Route 1/ })).toHaveAccessibleName(
      /1 course, 2 job steps.*Needs 2 offers.*Readiness not assessed/,
    );
    await userEvent.click(screen.getByRole("button", { name: "Route 1 Selected" }));
    expect(container.querySelectorAll('[data-kind="learning"]')).toHaveLength(1);
    expect(container.querySelectorAll('[data-kind="work"]')).toHaveLength(2);
    expect(container.querySelectorAll('path[data-kind="prerequisite"]')).toHaveLength(2);
    expect(screen.getByRole("button", { name: /Data assistant/ })).toHaveAttribute(
      "data-label-position",
      "below",
    );
    expect(screen.queryByText(/March 2028/)).not.toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: /Readiness not assessed.*Data quality analyst/ }),
    );
    expect(screen.getByText(/These routes do not establish when you could apply/)).toBeVisible();
  });
  it("preserves a collapsed destination while retaining its selected route", async () => {
    render(<RouteExplorer targets={targets} startLabel="Your experience today" />);
    await userEvent.click(beacon("Care coordinator"));
    await userEvent.click(screen.getByRole("button", { name: "Route 2" }));
    await userEvent.click(screen.getByRole("button", { name: "All routes · Collapse route" }));
    await userEvent.click(screen.getByRole("button", { name: "Data analyst" }));
    await userEvent.click(screen.getByRole("button", { name: "Care coordinator" }));
    expect(document.querySelectorAll(".route-journey-bundle")).toHaveLength(2);
    expect(screen.queryByRole("button", { name: /Shared course for/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Route 2 Selected" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    expect(screen.getByRole("button", { name: "Route 2 Selected" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("carries only the chosen beacon, role and field into focus, then reverses and cleans up", async () => {
    const { pending } = mockTransitions();
    const { container } = render(
      <RouteExplorer targets={targets} startLabel="Your experience today" />,
    );
    await userEvent.click(beacon("Data analyst"));
    const chosen = beacon("Data analyst");
    const oldBeacon = chosen.querySelector<HTMLElement>(".route-explorer-beacon");
    const name = oldBeacon?.style.viewTransitionName;
    expect(name).toMatch(/^cw-focus-.+-beacon$/);
    expect(container.querySelectorAll('[style*="view-transition-name:"]')).toHaveLength(3);
    expect(beacon("Care coordinator").querySelector("strong")).not.toHaveAttribute("style");
    expect(document.documentElement.dataset.careerwrightTransition).toBe("focus");
    expect(document.documentElement.style.getPropertyValue("--careerwright-focus-y")).toBe("43%");
    act(() => pending[0]?.update());
    const destination = container.querySelector('.route-journey-node[data-kind="target"]');
    expect(
      destination?.querySelector<HTMLElement>(".route-journey-beacon")?.style.viewTransitionName,
    ).toBe(name);
    expect(destination?.querySelector("strong")).toHaveTextContent("Data analyst");
    expect(screen.getByRole("button", { name: "All targets" })).toHaveFocus();
    await act(async () => pending[0]?.finish());
    expect(container.querySelectorAll('[style*="view-transition-name:"]')).toHaveLength(0);
    expect(document.documentElement).not.toHaveAttribute("data-careerwright-transition");

    await userEvent.click(screen.getByRole("button", { name: "All targets" }));
    expect(document.documentElement.dataset.careerwrightTransition).toBe("overview");
    act(() => pending[1]?.update());
    expect(beacon("Data analyst")).toHaveFocus();
    expect(
      beacon("Data analyst").querySelector<HTMLElement>(".route-explorer-beacon")?.style
        .viewTransitionName,
    ).toBe(name);
    await act(async () => pending[1]?.finish());
    expect(document.documentElement.style.getPropertyValue("--careerwright-focus-y")).toBe("");
  });

  it("commits navigation immediately with reduced motion or an unavailable transition API", async () => {
    const { start } = mockTransitions();
    vi.stubGlobal(
      "matchMedia",
      vi.fn(() => Object.assign(new EventTarget(), { matches: true })),
    );
    render(<RouteExplorer targets={targets} startLabel="Your experience today" />);
    await userEvent.click(beacon("Data analyst"));
    expect(screen.getByRole("button", { name: "All targets" })).toHaveFocus();
    expect(start).not.toHaveBeenCalled();
    Reflect.deleteProperty(document, "startViewTransition");
    await userEvent.click(screen.getByRole("button", { name: "All targets" }));
    expect(beacon("Data analyst")).toHaveFocus();
  });

  it("still opens the destination if the browser cannot start a transition", async () => {
    const { start } = mockTransitions();
    start.mockImplementation(() => {
      throw new Error("Transition unavailable");
    });
    const { container } = render(
      <RouteExplorer targets={targets} startLabel="Your experience today" />,
    );
    await userEvent.click(beacon("Data analyst"));
    expect(screen.getByRole("heading", { name: "Data analyst" })).toBeVisible();
    expect(screen.getByRole("button", { name: "All targets" })).toHaveFocus();
    expect(container.querySelectorAll('[style*="view-transition-name:"]')).toHaveLength(0);
    expect(document.documentElement).not.toHaveAttribute("data-careerwright-transition");
  });

  it("keeps shared names unique when two explorers are mounted", async () => {
    const { pending } = mockTransitions();
    const first = render(<RouteExplorer targets={targets} startLabel="First starting point" />);
    const second = render(<RouteExplorer targets={targets} startLabel="Second starting point" />);
    const buttons = screen.getAllByRole("button", { name: /Data analyst 2 routes/ });
    if (!buttons[0] || !buttons[1]) throw new Error("Missing destination controls");
    await userEvent.click(buttons[0]);
    await userEvent.click(buttons[1]);
    const names = Array.from(
      document.querySelectorAll<HTMLElement>('[style*="view-transition-name:"]'),
      (element) => element.style.viewTransitionName,
    );
    expect(names).toHaveLength(6);
    expect(new Set(names).size).toBe(6);
    first.unmount();
    expect(document.documentElement.dataset.careerwrightTransition).toBe("focus");
    act(() => pending[1]?.update());
    await act(async () => pending[1]?.finish());
    expect(second.container.querySelectorAll('[style*="view-transition-name:"]')).toHaveLength(0);
  });

  it("ignores stale snapshots during rapid navigation and preserves route state", async () => {
    const { pending } = mockTransitions();
    render(<RouteExplorer targets={targets} startLabel="Your experience today" />);
    await userEvent.click(beacon("Care coordinator"));
    await userEvent.click(beacon("Data analyst"));
    expect(pending[0]?.skipTransition).toHaveBeenCalledOnce();
    act(() => pending[1]?.update());
    act(() => pending[0]?.update());
    expect(screen.getByRole("heading", { name: "Data analyst" })).toBeVisible();
    await act(async () => pending[0]?.finish());
    expect(document.documentElement.dataset.careerwrightTransition).toBe("focus");
    await userEvent.click(screen.getByRole("button", { name: "Route 2" }));
    await userEvent.click(screen.getByRole("button", { name: "Care coordinator" }));
    act(() => pending[2]?.update());
    await userEvent.click(screen.getByRole("button", { name: "Data analyst" }));
    act(() => pending[3]?.update());
    expect(screen.getByRole("button", { name: "Route 2 Viewing" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(screen.getByRole("button", { name: /Shared course for Data analyst/ })).toBeVisible();
  });

  it("stops live motion and cleans up on unmount without losing a pending destination", async () => {
    const { pending } = mockTransitions();
    const preference = Object.assign(new EventTarget(), { matches: false });
    vi.stubGlobal(
      "matchMedia",
      vi.fn(() => preference),
    );
    const { container, unmount } = render(
      <RouteExplorer targets={targets} startLabel="Your experience today" />,
    );
    await userEvent.click(beacon("Care coordinator"));
    preference.matches = true;
    act(() => preference.dispatchEvent(new Event("change")));
    expect(pending[0]?.skipTransition).toHaveBeenCalledOnce();
    act(() => pending[0]?.update());
    expect(screen.getByRole("heading", { name: "Care coordinator" })).toBeVisible();
    expect(container.querySelectorAll('[style*="view-transition-name:"]')).toHaveLength(0);
    preference.matches = false;
    await userEvent.click(screen.getByRole("button", { name: "Data analyst" }));
    unmount();
    expect(pending[1]?.skipTransition).toHaveBeenCalledOnce();
    act(() => pending[1]?.update());
    expect(document.documentElement).not.toHaveAttribute("data-careerwright-transition");
  });
});
