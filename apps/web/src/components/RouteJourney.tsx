"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { RouteDetail, RouteStep } from "@/generated/api";
import { formatDay, formatMonth } from "@/lib/dates";
import { formatMoney } from "@/lib/money";
import { ACTION_KIND } from "@/lib/optionWords";
import {
  stepIdentity as identity,
  planningState,
  type RouteResultStatus,
  routeIdentity,
  routeMissingFacts,
  routeStateWords,
  stepMissingFacts,
  targetRouteState,
} from "@/lib/routeState";
import { ROUTE_CONDITION } from "@/lib/routeWords";

type Props = {
  routes: RouteDetail[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  targetTitle: string;
  startLabel: string;
  planIndex?: number;
  completedSteps?: string[];
  initialExpandedIndex?: number;
  onCollapse?: () => void;
  status?: RouteResultStatus;
  scheduleCount?: number;
  detailStatus?: "pending" | "error";
  routeSetId?: string;
  revealSelected?: boolean;
};

type JourneyNode = {
  id: string;
  step?: RouteStep;
  routes: number[];
  depth: number;
  x: number;
  y: number;
  verification?: { month: string; routeIndex: number };
  bundle?: RouteDetail;
};

const month = (value: string) => formatMonth(`${value}-01`);
const dates = (step: RouteStep) =>
  `${step.start_date ? formatDay(step.start_date) : step.start_month ? month(step.start_month) : "Start unknown"} – ${step.finish_date ? formatDay(step.finish_date) : step.finish_month ? month(step.finish_month) : "finish unknown"}`;
const title = (step: RouteStep) => step.title ?? ACTION_KIND[step.kind];
const GATE_LABEL = {
  offer: "Offer needed",
  award: "Funding award needed",
  application: "Place needed",
  loan: "Loan approval needed",
};
const paymentSummary = (step: RouteStep) => {
  const first = step.payments[0];
  return first
    ? `${formatMoney({
        minor_units: step.payments.reduce((sum, payment) => sum + payment.amount.minor_units, 0),
        currency: first.amount.currency,
      })} ${step.supplied.includes("cost") ? (step.payments.every((payment) => payment.kind === "fee") ? "supplied fee" : "supplied payments") : "recorded payments"}`
    : "Payments not recorded";
};

export function stepCounts(steps: RouteStep[]) {
  const unique = Array.from(new Map(steps.map((step) => [identity(step), step])).values());
  const courses = unique.filter((step) => step.kind === "learning").length;
  const jobs = unique.filter((step) => step.kind === "work").length;
  return `${courses} course${courses === 1 ? "" : "s"}, ${jobs} job step${jobs === 1 ? "" : "s"}`;
}

export function conditionSummary(route: RouteDetail) {
  const offers = route.schedule.conditions.filter((condition) => condition.kind === "offer").length;
  const other = Array.from(
    new Set(
      route.schedule.conditions
        .filter((condition) => condition.kind !== "offer")
        .map((condition) => GATE_LABEL[condition.kind]),
    ),
  );
  return (
    [
      offers ? `Needs ${offers} offer${offers === 1 ? "" : "s"}` : null,
      ...other,
      route.schedule.verdict === "unresolved" ? "Readiness not assessed" : null,
      route.schedule.qualifications.includes("planned_outcome_assumption")
        ? "Assumes assessed outcome"
        : null,
      route.schedule.qualifications.includes("supplied_figures") ? "Figures unconfirmed" : null,
    ]
      .filter(Boolean)
      .join("; ") || "No conditional gates recorded"
  );
}

function prerequisiteProviders(route: RouteDetail, step: RouteStep) {
  return route.steps.filter(
    (other) =>
      other !== step &&
      other.grants.some((grant) => step.prerequisites.includes(grant)) &&
      other.usable_month !== null &&
      step.start_month !== null &&
      other.usable_month <= step.start_month,
  );
}

export function RouteJourney(props: Props) {
  return <JourneyView key={props.targetTitle} {...props} />;
}

function JourneyView({
  routes,
  selectedIndex,
  onSelect,
  targetTitle,
  startLabel,
  planIndex,
  completedSteps = [],
  initialExpandedIndex,
  onCollapse,
  status,
  scheduleCount = routes.length,
  detailStatus,
  revealSelected = false,
}: Props) {
  const id = useId();
  const initialRoute = routes.find(
    (route) =>
      route.schedule.index ===
      (initialExpandedIndex ?? (revealSelected ? selectedIndex : undefined)),
  );
  const [expandedIdentity, setExpandedIdentity] = useState<string | null>(
    initialRoute ? routeIdentity(initialRoute) : null,
  );
  const [expandedHint, setExpandedHint] = useState(initialRoute?.schedule.index);
  const expanded =
    routes.find(
      (route) => route.schedule.index === expandedHint && routeIdentity(route) === expandedIdentity,
    ) ?? routes.find((route) => routeIdentity(route) === expandedIdentity);
  const expandedIndex = expanded?.schedule.index ?? null;
  const collapseButton = useRef<HTMLButtonElement>(null);
  const previousExpandedIdentity = useRef<string | null>(null);
  useEffect(() => {
    if (previousExpandedIdentity.current !== expandedIdentity && expandedIndex !== null)
      collapseButton.current?.focus({ preventScroll: true });
    previousExpandedIdentity.current = expandedIdentity;
  }, [expandedIdentity, expandedIndex]);
  const routeButtons = useRef(new Map<number, HTMLButtonElement>());
  const [inspected, setInspected] = useState<string | null>(null);
  const previousSelectedIndex = useRef(selectedIndex);
  const requestedIdentity = useRef(initialRoute ? routeIdentity(initialRoute) : null);
  const awaitingDetails =
    status === "pending" ||
    detailStatus === "pending" ||
    (scheduleCount > 0 && routes.length === 0);
  useEffect(() => {
    if (selectedIndex < 0 && awaitingDetails) return;
    const next = routes.find((route) => route.schedule.index === selectedIndex);
    if (previousSelectedIndex.current === selectedIndex) {
      if (revealSelected && requestedIdentity.current === null && next) {
        requestedIdentity.current = routeIdentity(next);
        setExpandedIdentity(routeIdentity(next));
        setExpandedHint(selectedIndex);
      }
      return;
    }
    previousSelectedIndex.current = selectedIndex;
    requestedIdentity.current = next ? routeIdentity(next) : null;
    setExpandedHint(selectedIndex);
    if (next && expandedIdentity === routeIdentity(next)) return;
    setExpandedIdentity((current) => {
      return (current === null && !revealSelected) || !next ? null : routeIdentity(next);
    });
    setInspected(null);
  }, [selectedIndex, routes, expandedIdentity, revealSelected, awaitingDetails]);
  useEffect(() => {
    if (expandedIdentity !== null && !expanded && !awaitingDetails) {
      setExpandedIdentity(null);
      setInspected(null);
    }
  }, [expandedIdentity, expanded, awaitingDetails]);
  const inspectorHeading = useRef<HTMLHeadingElement>(null);
  const inspector = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (inspected === null) return;
    inspectorHeading.current?.focus();
    const preference = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const stillRoot = inspector.current?.closest(".career-workspace, .decision-proposal");
    if (preference?.matches || stillRoot?.getAttribute("data-still") === "true") return;
    const reveal = inspector.current?.animate?.(
      [
        { opacity: 0.4, transform: "translateY(6px)" },
        { opacity: 1, transform: "translateY(0)" },
      ],
      { duration: 220, easing: "ease-out" },
    );
    const stopMotion = () => {
      if (preference?.matches || stillRoot?.getAttribute("data-still") === "true") reveal?.cancel();
    };
    const stillness = new MutationObserver(stopMotion);
    if (stillRoot)
      stillness.observe(stillRoot, { attributes: true, attributeFilter: ["data-still"] });
    preference?.addEventListener("change", stopMotion);
    return () => {
      reveal?.cancel();
      preference?.removeEventListener("change", stopMotion);
      stillness.disconnect();
    };
  }, [inspected]);
  const expand = (index: number) => {
    const route = routes.find((item) => item.schedule.index === index);
    if (!route) return;
    setExpandedIdentity(routeIdentity(route));
    setExpandedHint(index);
    setInspected(null);
    onSelect(index);
  };
  const collapse = () => {
    setExpandedIdentity(null);
    setInspected(null);
    onCollapse?.();
    if (expandedIndex !== null)
      routeButtons.current.get(expandedIndex)?.focus({ preventScroll: true });
  };
  const selected = routes.find((route) => route.schedule.index === selectedIndex);
  const visible = [selected, ...routes.filter((route) => route !== selected)]
    .filter((route): route is RouteDetail => route !== undefined)
    .slice(0, 3)
    .sort((a, b) => routes.indexOf(a) - routes.indexOf(b));
  const nodes = new Map<string, JourneyNode>();
  const edges = new Map<
    string,
    { from: string; to: string; routes: number[]; prerequisite: boolean }
  >();
  const connect = (from: string, to: string, route: number, prerequisite = false) => {
    const key = JSON.stringify([from, to]);
    const edge = edges.get(key);
    if (edge) edge.routes.push(route);
    else edges.set(key, { from, to, routes: [route], prerequisite });
  };
  for (const route of expanded ? [expanded] : []) {
    for (const step of route.steps) {
      const key = identity(step);
      const node = nodes.get(key);
      if (node) continue;
      else nodes.set(key, { id: key, step, routes: [route.schedule.index], depth: 1, x: 50, y: 0 });
    }
    for (const step of route.steps) {
      const providers = prerequisiteProviders(route, step);
      if (providers.length === 0) connect("start", identity(step), route.schedule.index);
      for (const provider of providers) {
        connect(identity(provider), identity(step), route.schedule.index, true);
      }
      if (!route.steps.some((other) => prerequisiteProviders(route, other).includes(step))) {
        connect(identity(step), "target", route.schedule.index);
      }
    }
    if (route.steps.length === 0) connect("start", "target", route.schedule.index);
  }
  // Only prerequisite edges establish order; array order never does.
  for (let pass = 0; pass < nodes.size; pass++) {
    for (const edge of edges.values()) {
      const from = nodes.get(edge.from);
      const to = nodes.get(edge.to);
      if (from && to) to.depth = Math.max(to.depth, from.depth + 1);
    }
  }
  const lastDepth = Math.max(0, ...Array.from(nodes.values(), (node) => node.depth)) + 1;
  const rows = Array.from({ length: lastDepth - 1 }, (_, index) =>
    Array.from(nodes.values()).filter((node) => node.depth === index + 1),
  );
  const width = 680;
  const height = Math.max(540, lastDepth * 120, ...rows.map((row) => row.length * 190 + 120));
  for (const row of rows) {
    row.forEach((node, index) => {
      const spread = row.length === 1 ? 0 : (index / (row.length - 1)) * 2 - 1;
      node.x = 16 + (66 * node.depth) / lastDepth + spread * 11;
      node.y =
        row.length > 2
          ? 20 + (56 * index) / (row.length - 1)
          : 90 - (80 * node.depth) / lastDepth + spread * 14;
    });
  }
  const bundled = visible.filter((route) => route !== expanded);
  bundled.forEach((route, index) => {
    const key = `bundle:${route.schedule.index}`;
    nodes.set(key, {
      id: key,
      routes: [route.schedule.index],
      depth: 1,
      x: expanded ? 27 : 46 + index * 6,
      y: expanded ? 14 + index * 24 : 18 + index * 27,
      bundle: route,
    });
    connect("start", key, route.schedule.index);
    connect(key, "target", route.schedule.index);
  });
  const routeIndices = visible.map((route) => route.schedule.index);
  nodes.set("start", {
    id: "start",
    routes: routeIndices,
    depth: 0,
    x: 12,
    y: 82,
  });
  nodes.set("target", {
    id: "target",
    routes: routeIndices,
    depth: lastDepth,
    x: 85,
    y: 26,
  });
  if (routes.length === 0) connect("start", "target", -1);
  for (const route of expanded ? [expanded] : []) {
    const milestone = route.milestones.find((item) => item.kind === "verify_assessed_completion");
    const approach = Array.from(edges.values()).find(
      (edge) => edge.to === "target" && edge.routes.includes(route.schedule.index),
    );
    const from = approach && nodes.get(approach.from);
    if (!milestone || !from) continue;
    // The milestone sits on the same cubic as the final approach, without changing its order.
    const t = 0.6;
    const curve = (85 - from.x) * 0.58;
    const x =
      (1 - t) ** 3 * from.x +
      3 * (1 - t) ** 2 * t * (from.x + curve) +
      3 * (1 - t) * t ** 2 * (85 - curve) +
      t ** 3 * 85;
    const y =
      (1 - t) ** 3 * from.y +
      3 * (1 - t) ** 2 * t * from.y +
      3 * (1 - t) * t ** 2 * 26 +
      t ** 3 * 26;
    const key = `verification:${route.schedule.index}`;
    nodes.set(key, {
      id: key,
      routes: [route.schedule.index],
      depth: lastDepth,
      x,
      y,
      verification: { month: milestone.month, routeIndex: route.schedule.index },
    });
  }
  const inspectedNode = inspected ? nodes.get(inspected) : undefined;
  const step = inspectedNode?.step;
  const conditions = routes
    .filter((route) => inspectedNode?.routes.includes(route.schedule.index))
    .flatMap((route) => route.schedule.conditions)
    .filter((condition) => condition.variant_id === step?.variant_id);
  const state = targetRouteState(routes, status);
  const selectedFacts = selected ? routeMissingFacts(selected) : [];

  return (
    <section className="route-journey" aria-label="Your possible routes" data-route-state={state}>
      <p className="route-state-status" role="status">
        {routeStateWords(state)}
      </p>
      {detailStatus && (
        <p>
          {detailStatus === "error"
            ? "Some route details could not be loaded."
            : "Loading route details."}
        </p>
      )}
      {scheduleCount > routes.length && (
        <p>
          {routes.length} of {scheduleCount} route summaries loaded.
        </p>
      )}
      <div className="route-journey-toolbar">
        {routes.map((route) => (
          <button
            key={route.schedule.index}
            type="button"
            className="route-journey-choice"
            aria-pressed={route.schedule.index === selectedIndex}
            data-selected={route.schedule.index === selectedIndex}
            data-saved={route.schedule.index === planIndex}
            aria-expanded={expandedIndex === route.schedule.index}
            aria-controls={`${id}-map`}
            ref={(element) => {
              if (element) routeButtons.current.set(route.schedule.index, element);
              else routeButtons.current.delete(route.schedule.index);
            }}
            onClick={() => expand(route.schedule.index)}
          >
            <strong>Route {route.schedule.index + 1}</strong>{" "}
            {route.schedule.index === planIndex && <small>Saved plan</small>}{" "}
            {route.schedule.index === selectedIndex && (
              <small>{expandedIndex === route.schedule.index ? "Viewing" : "Selected"}</small>
            )}
          </button>
        ))}
      </div>

      <div className="route-journey-controls">
        {expanded && (
          <button ref={collapseButton} type="button" onClick={collapse}>
            All routes · Collapse route
          </button>
        )}
        <p>
          {expanded
            ? `Route ${expanded.schedule.index + 1} expanded. Other routes stay bundled.`
            : routes.length
              ? "Choose a route to reveal its steps."
              : "The destination stays visible while route information is unavailable."}{" "}
          Inspecting does not save a plan or mark completion.
        </p>
      </div>
      <div id={`${id}-map`} className="route-journey-map">
        <div
          className="route-journey-canvas"
          style={{ position: "relative", minWidth: width, height }}
        >
          <svg
            className="route-journey-lines"
            viewBox={`0 0 ${width} ${height}`}
            preserveAspectRatio="none"
            aria-hidden="true"
            focusable="false"
          >
            <defs>
              <linearGradient
                id={`${id}-trail`}
                gradientUnits="userSpaceOnUse"
                x1={width * 0.12}
                y1={height * 0.82}
                x2={width * 0.85}
                y2={height * 0.26}
              >
                <stop offset="0%" stopColor="var(--trail-near)" />
                <stop offset="100%" stopColor="var(--trail-far)" />
              </linearGradient>
              <linearGradient
                id={`${id}-selected`}
                gradientUnits="userSpaceOnUse"
                x1={width * 0.12}
                y1={height * 0.82}
                x2={width * 0.85}
                y2={height * 0.26}
              >
                <stop offset="0%" stopColor="var(--light-chosen)" />
                <stop offset="100%" stopColor="var(--light-person)" />
              </linearGradient>
              <filter id={`${id}-bloom`} x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="5" />
              </filter>
              <radialGradient id={`${id}-destination`}>
                <stop offset="0%" stopColor="var(--decision-destination)" stopOpacity="0.35" />
                <stop offset="100%" stopColor="var(--decision-destination)" stopOpacity="0" />
              </radialGradient>
            </defs>
            <circle cx={width * 0.85} cy={height * 0.26} r="62" fill={`url(#${id}-destination)`} />
            {Array.from(edges.entries(), ([key, edge]) => {
              const from = nodes.get(edge.from);
              const to = nodes.get(edge.to);
              if (!from || !to) return null;
              const x1 = (from.x / 100) * width;
              const x2 = (to.x / 100) * width;
              const y1 = (from.y / 100) * height;
              const y2 = (to.y / 100) * height;
              const curve = (x2 - x1) * 0.58;
              const d = `M${x1},${y1} C${x1 + curve},${y1} ${x2 - curve},${y2} ${x2},${y2}`;
              const selected = edge.routes.includes(selectedIndex);
              const stroke = `url(#${id}-${selected ? "selected" : "trail"})`;
              return (
                <g
                  key={key}
                  data-selected={selected}
                  data-route-state={state}
                  data-planning-state={
                    edge.routes.some((index) =>
                      routes.some(
                        (route) =>
                          route.schedule.index === index && planningState(route) === "complete",
                      ),
                    )
                      ? "complete"
                      : "partial"
                  }
                >
                  <path
                    className="route-journey-aura"
                    d={d}
                    stroke={stroke}
                    filter={`url(#${id}-bloom)`}
                  />
                  <path className="route-journey-trail" d={d} stroke={stroke} />
                  <path
                    className="route-journey-core"
                    d={d}
                    stroke={stroke}
                    data-kind={edge.prerequisite ? "prerequisite" : "route"}
                    data-selected={selected}
                  />
                </g>
              );
            })}
          </svg>
          {Array.from(nodes.values(), (node) => (
            <button
              key={node.id}
              type="button"
              className={`route-journey-node${node.bundle ? " route-journey-bundle" : ""}`}
              style={{
                position: "absolute",
                left: `${node.x}%`,
                top: `${node.y}%`,
                transform: "translate(-50%, 0)",
              }}
              data-kind={
                node.bundle
                  ? "bundle"
                  : node.verification
                    ? "verification"
                    : (node.step?.kind ?? node.id)
              }
              data-selected={node.routes.includes(selectedIndex)}
              data-inspected={inspected === node.id}
              data-route-state={state}
              data-planning-state={
                node.step
                  ? stepMissingFacts(node.step).length
                    ? "partial"
                    : "complete"
                  : node.bundle
                    ? planningState(node.bundle)
                    : selected
                      ? planningState(selected)
                      : undefined
              }
              data-saved={node.routes.includes(planIndex ?? -1)}
              data-completed={node.step ? completedSteps.includes(node.step.variant_id) : false}
              data-label-position={
                (node.bundle && expanded) || (node.step && node.depth === 1)
                  ? "left"
                  : node.id === "target"
                    ? "above"
                    : "below"
              }
              aria-expanded={node.bundle ? false : inspected === node.id}
              aria-controls={node.bundle ? `${id}-map` : `${id}-inspector`}
              onClick={() => {
                if (node.bundle) {
                  expand(node.bundle.schedule.index);
                  return;
                }
                setInspected(inspected === node.id ? null : node.id);
                const routeIndex = node.routes[0];
                if (
                  (node.step || node.verification) &&
                  node.routes.length === 1 &&
                  routeIndex !== undefined &&
                  routeIndex !== selectedIndex
                )
                  onSelect(routeIndex);
              }}
            >
              <span className="route-journey-beacon" aria-hidden="true" />
              <span className="route-journey-label">
                <small>
                  {node.bundle
                    ? "Collapsed route"
                    : node.verification
                      ? "Verification"
                      : node.step
                        ? `${ACTION_KIND[node.step.kind]} · ${node.routes.map((index) => `Route ${index + 1}`).join(" / ")}`
                        : node.id === "start"
                          ? "Starting point"
                          : !selected || selected.schedule.verdict === "unresolved"
                            ? "Readiness not assessed"
                            : "Modelled readiness"}
                </small>{" "}
                <strong>
                  {node.bundle
                    ? `Route ${node.bundle.schedule.index + 1}`
                    : node.verification
                      ? "Verify assessed outcome"
                      : node.step
                        ? title(node.step)
                        : node.id === "start"
                          ? startLabel
                          : targetTitle}
                </strong>{" "}
                {node.bundle ? (
                  <>
                    <span>{stepCounts(node.bundle.steps)}</span>
                    <small>{conditionSummary(node.bundle)}</small>
                    <small>{routeStateWords(planningState(node.bundle))}</small>
                  </>
                ) : node.verification ? (
                  <span>
                    Route {node.verification.routeIndex + 1}: {month(node.verification.month)}
                  </span>
                ) : node.step ? (
                  <>
                    <small className="route-step-status">
                      {stepMissingFacts(node.step)
                        .filter((fact) => fact !== "Payments unknown")
                        .join("; ") ||
                        (stepMissingFacts(node.step).length
                          ? "Planning facts still needed"
                          : "Planning facts recorded")}
                    </small>
                    {node.step.kind !== "work" && (
                      <span>
                        {node.step.payments.length === 0
                          ? "Payments unknown"
                          : node.step.supplied.includes("cost")
                            ? "Quote unknown"
                            : "Recorded payments"}
                      </span>
                    )}
                    {Array.from(
                      new Set(
                        routes
                          .filter((route) => node.routes.includes(route.schedule.index))
                          .flatMap((route) => route.schedule.conditions)
                          .filter((condition) => condition.variant_id === node.step?.variant_id)
                          .map((condition) => GATE_LABEL[condition.kind]),
                      ),
                    ).map((label) => (
                      <small key={label}>{label}</small>
                    ))}
                    {completedSteps.includes(node.step.variant_id) && (
                      <small>Completion self-reported</small>
                    )}
                  </>
                ) : node.id === "target" ? (
                  <>
                    {selected && selected.schedule.verdict !== "unresolved" && (
                      <span>
                        Route {selected.schedule.index + 1}:{" "}
                        {month(selected.schedule.readiness_month)}
                      </span>
                    )}
                    {selected?.schedule.qualifications.includes("planned_outcome_assumption") && (
                      <span>Assumes a future assessed outcome</span>
                    )}
                    <span>
                      {!selected || selected.schedule.verdict === "unresolved"
                        ? "Illustrative destination; readiness unknown"
                        : "Application readiness, not a job offer"}
                    </span>
                  </>
                ) : null}
              </span>
            </button>
          ))}
        </div>
      </div>
      <p className="route-journey-legend">
        Bundled trails summarise routes, not direct job transitions; expanded linked steps show
        recorded prerequisites. Distance is layout, not duration or probability.
      </p>
      <p className="route-state-legend">
        Faint trails: route support not established. Marked steps: planning facts still needed.
        Resolved trails: planning information complete. Source checks, conditions, your selection
        and reported completion remain separate.
      </p>
      {selected && (
        <p className="route-state-status">
          {selectedFacts.length ? selectedFacts.join("; ") : "Planning information complete"}.{" "}
          {conditionSummary(selected)}. Sources and current availability still need checking.
        </p>
      )}
      {routes.length > 3 && (
        <p className="route-journey-note">
          Showing the viewed route and two alternatives. Choose any route above to bring it into
          view.
        </p>
      )}
      <div
        ref={inspector}
        id={`${id}-inspector`}
        className="route-journey-inspector"
        data-inspecting={inspected !== null}
        aria-live="polite"
      >
        {inspectedNode ? (
          <>
            <h3 ref={inspectorHeading} tabIndex={-1}>
              {step
                ? title(step)
                : inspectedNode.verification
                  ? "Verify assessed outcome"
                  : inspectedNode.id === "start"
                    ? startLabel
                    : targetTitle}
            </h3>
            {step ? (
              <>
                <dl>
                  <div>
                    <dt>Planning information</dt>
                    <dd>
                      {stepMissingFacts(step).join("; ") || "Planning facts recorded"}. Source
                      verification and current availability are separate checks.
                    </dd>
                  </div>
                  <div>
                    <dt>Purpose</dt>
                    <dd>
                      {ACTION_KIND[step.kind]}
                      {step.provider ? ` with ${step.provider}` : ""}.{" "}
                      {routes.some(
                        (route) =>
                          inspectedNode.routes.includes(route.schedule.index) &&
                          route.milestones.some(
                            (milestone) => milestone.kind === "verify_assessed_completion",
                          ),
                      )
                        ? "Assessed completion must be verified."
                        : "Planned outcomes need assessment before skills or credentials can be confirmed."}
                    </dd>
                  </div>
                  <div>
                    <dt>Time</dt>
                    <dd>
                      {dates(step)}.{" "}
                      {step.weekly_hours === null
                        ? "Weekly hours unknown."
                        : `${step.weekly_hours} hours a week.`}
                      {step.usable_month &&
                        ` Modelled outcomes usable from ${month(step.usable_month)}.`}
                      {step.application_deadline &&
                        ` Apply by ${formatDay(step.application_deadline)}.`}
                    </dd>
                  </div>
                  <div>
                    <dt>Cost</dt>
                    <dd>
                      {paymentSummary(step)}.
                      {step.payments.map((payment) => (
                        <p
                          key={`${payment.kind}-${payment.month}-${payment.due}-${payment.amount.minor_units}`}
                        >
                          {formatMoney(payment.amount)}
                          {payment.due
                            ? ` due ${formatDay(payment.due)}`
                            : payment.month
                              ? ` in ${month(payment.month)}`
                              : ", payment date unknown"}
                          .
                        </p>
                      ))}
                      {step.recurring && (
                        <p>
                          {step.recurring.at_least ? "At least " : ""}
                          {formatMoney(step.recurring.amount)} per active month
                          {step.recurring.count === null
                            ? "; number of payments unknown"
                            : ` for ${step.recurring.count} payments`}
                          .
                        </p>
                      )}
                      {step.fee_loan && (
                        <p>
                          Fee loan:{" "}
                          {step.fee_loan.amount
                            ? formatMoney(step.fee_loan.amount)
                            : "amount unknown"}
                          . Must be repaid; approval must be checked.
                        </p>
                      )}
                      {step.wage && (
                        <p>Net pay after an accepted offer: {formatMoney(step.wage)} a month.</p>
                      )}
                      {step.work_pattern && (
                        <p>
                          Work alongside this: {step.work_pattern.hours_per_week} hours/week,{" "}
                          {formatMoney(step.work_pattern.net_income)} net pay a month.
                        </p>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Conditions</dt>
                    <dd>
                      {conditions.length
                        ? Array.from(
                            new Set(
                              conditions.map(
                                (condition) => ROUTE_CONDITION[condition.verification],
                              ),
                            ),
                          ).join(". ")
                        : "No conditional gate recorded."}
                      {step.prerequisites.length > 0 && (
                        <p>
                          {step.prerequisites.length} prerequisite
                          {step.prerequisites.length === 1 ? "" : "s"} required before starting. See
                          route dependencies below.
                        </p>
                      )}
                      {(step.qualified_by.length > 0 ||
                        step.records.some((record) => record.review_state !== "reviewed")) && (
                        <p>
                          {step.synthetic ? "Uses synthetic example data. " : ""}
                          {step.added_by_person ? "Option added by you. " : ""}Evidence and supplied
                          figures still need review.
                        </p>
                      )}
                      {completedSteps.includes(step.variant_id) && (
                        <p>
                          Completion self-reported. This does not verify acquired skills or
                          credentials.
                        </p>
                      )}
                    </dd>
                  </div>
                </dl>
                {step.sources.length ? (
                  <details className="route-journey-citations">
                    <summary>Source excerpts ({step.sources.length})</summary>
                    <ol className="route-journey-sources">
                      {step.sources.map((source) => (
                        <li key={`${source.source_id}-${source.locator}-${source.excerpt}`}>
                          <p>
                            {source.basis === "fixture"
                              ? "Synthetic example"
                              : source.basis === "person"
                                ? "Supplied by you"
                                : "Source page"}
                            {source.locator ? `: ${source.locator}` : ""}
                          </p>
                          {source.excerpt && <blockquote>{source.excerpt}</blockquote>}
                          {source.retrieved_on && <p>Read {formatDay(source.retrieved_on)}</p>}
                          {source.source_url && (
                            <a
                              href={source.source_url}
                              target="_blank"
                              rel="noopener noreferrer nofollow"
                            >
                              Open source page
                            </a>
                          )}
                        </li>
                      ))}
                    </ol>
                  </details>
                ) : (
                  <p>No source citations recorded.</p>
                )}
              </>
            ) : (
              <p>
                {inspectedNode.verification
                  ? `The route model calls for assessed completion to be verified in ${month(inspectedNode.verification.month)}. No passed assessment, provider confirmation or verification fee is recorded here. The planned skill remains an assumption until its evidence is reviewed.`
                  : inspectedNode.id === "start"
                    ? "Your stated starting point. Prerequisites not supplied by a route step still need to be confirmed."
                    : !selected || selected.schedule.verdict === "unresolved"
                      ? "Readiness not assessed. These routes do not establish when you could apply, or confirm a vacancy, job offer or acquired skills."
                      : "This is the modelled point for applying to the target role, under each route’s stated conditions. It does not guarantee a vacancy, a job offer or verified acquired skills."}
              </p>
            )}
          </>
        ) : (
          <p>Select a step to inspect its time, cost, conditions and sources.</p>
        )}
      </div>
      <details className="route-journey-text">
        <summary>Read route steps and dependencies</summary>
        {visible.map((route) => (
          <div key={route.schedule.index}>
            <h3>
              Route {route.schedule.index + 1}
              {route.schedule.index === planIndex ? " · Saved plan" : ""}
            </h3>
            {route.steps.length === 0 ? (
              <p>
                No additional training or job steps in this route. Check its readiness conditions.
              </p>
            ) : (
              <ol>
                {Array.from(
                  new Map(route.steps.map((item) => [identity(item), item])).values(),
                ).map((item) => {
                  const providers = prerequisiteProviders(route, item);
                  const external = item.prerequisites.filter(
                    (prerequisite) =>
                      !providers.some((provider) => provider.grants.includes(prerequisite)),
                  );
                  return (
                    <li key={identity(item)}>
                      <strong>{title(item)}</strong>. {dates(item)}.{" "}
                      {providers.length > 0
                        ? `Prerequisite can come from: ${providers.map(title).join(", ")}.`
                        : "No prior route step required."}
                      {external.length > 0 &&
                        ` ${external.length} starting prerequisite${external.length === 1 ? "" : "s"} still to confirm.`}
                    </li>
                  );
                })}
              </ol>
            )}
            <p>
              {route.schedule.verdict === "unresolved"
                ? `Readiness for ${targetTitle} has not been assessed.`
                : `Modelled readiness for ${targetTitle}: ${month(route.schedule.readiness_month)}.`}{" "}
              Not a guaranteed vacancy or offer.
            </p>
            {route.milestones.some((item) => item.kind === "verify_assessed_completion") && (
              <p>Assessed completion must be verified before the planned skill can be confirmed.</p>
            )}
          </div>
        ))}
      </details>
    </section>
  );
}
