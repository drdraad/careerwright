"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { flushSync } from "react-dom";
import type { RouteDetail } from "@/generated/api";
import {
  type RouteResultStatus,
  routeIdentity,
  routeStateWords,
  targetRouteState,
} from "@/lib/routeState";
import { conditionSummary, RouteJourney, stepCounts } from "./RouteJourney";

export type JourneyTarget = {
  id: string;
  title: string;
  routes: RouteDetail[];
  planIndex?: number;
  completedSteps?: string[];
  status?: RouteResultStatus;
  scheduleCount?: number;
  detailStatus?: "pending" | "error";
  routeSetId?: string;
};

type Props = {
  targets: JourneyTarget[];
  startLabel: string;
  activeTargetId?: string | null;
  onTargetChange?: (id: string | null) => void;
  selectedIndex?: number | null;
  onSelect?: (targetId: string, index: number) => void;
};

function routeCountWords(target: JourneyTarget) {
  const count =
    target.scheduleCount ?? (target.routes.length || (target.status === "unsupported" ? 0 : null));
  return count === null ? "Route count not checked" : `${count} route${count === 1 ? "" : "s"}`;
}

export function RouteExplorer({
  targets,
  startLabel,
  activeTargetId,
  onTargetChange,
  selectedIndex,
  onSelect,
}: Props) {
  const id = useId();
  const [localTargetId, setTargetId] = useState<string | null>(null);
  const targetId = activeTargetId === undefined ? localTargetId : activeTargetId;
  const [viewedRoutes, setViewedRoutes] = useState<
    Record<string, { index: number; identity: string; expanded: boolean }>
  >({});
  const targetButtons = useRef(new Map<string, HTMLButtonElement>());
  const allTargetsButton = useRef<HTMLButtonElement>(null);
  const returnTarget = useRef<string | null>(null);
  const explorer = useRef<HTMLElement>(null);
  const transition = useRef<ViewTransition | null>(null);
  const navigation = useRef(0);
  const transitionElements = useRef(new Set<HTMLElement | SVGElement>());
  const clearTransition = useCallback(() => {
    for (const element of transitionElements.current) {
      element.style.removeProperty("view-transition-name");
      element.style.removeProperty("view-transition-class");
    }
    transitionElements.current.clear();
    const root = document.documentElement;
    if (root.dataset.careerwrightTransitionOwner === id) {
      delete root.dataset.careerwrightTransition;
      delete root.dataset.careerwrightTransitionOwner;
      root.style.removeProperty("--careerwright-focus-x");
      root.style.removeProperty("--careerwright-focus-y");
    }
  }, [id]);
  useEffect(() => {
    const preference = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const stillRoot = explorer.current?.closest(".career-workspace, .decision-proposal");
    const stopMotion = () => {
      if (preference?.matches || stillRoot?.getAttribute("data-still") === "true") {
        transition.current?.skipTransition();
        clearTransition();
      }
    };
    const stillness = new MutationObserver(stopMotion);
    if (stillRoot)
      stillness.observe(stillRoot, { attributes: true, attributeFilter: ["data-still"] });
    preference?.addEventListener("change", stopMotion);
    return () => {
      navigation.current++;
      transition.current?.skipTransition();
      clearTransition();
      preference?.removeEventListener("change", stopMotion);
      stillness.disconnect();
    };
  }, [clearTransition]);
  const target = targets.find((item) => item.id === targetId);
  const viewed = target ? viewedRoutes[target.id] : undefined;
  const rememberedRoute =
    target?.routes.find(
      (route) =>
        route.schedule.index === viewed?.index && viewed?.identity === routeIdentity(route),
    ) ?? target?.routes.find((route) => viewed?.identity === routeIdentity(route));
  const viewedIndex =
    selectedIndex !== undefined
      ? (selectedIndex ?? -1)
      : viewed
        ? (rememberedRoute?.schedule.index ?? -1)
        : (target?.planIndex ?? target?.routes[0]?.schedule.index ?? -1);
  useEffect(() => {
    if (targetId === null || target) return;
    navigation.current++;
    transition.current?.skipTransition();
    clearTransition();
    setTargetId(null);
    onTargetChange?.(null);
  }, [targetId, target, clearTransition, onTargetChange]);
  useEffect(() => {
    if (targetId !== null) allTargetsButton.current?.focus({ preventScroll: true });
    else if (returnTarget.current)
      targetButtons.current.get(returnTarget.current)?.focus({ preventScroll: true });
  }, [targetId]);
  const navigate = (nextId: string | null) => {
    if (nextId === targetId) return;
    if (nextId !== null) returnTarget.current = nextId;
    const request = ++navigation.current;
    transition.current?.skipTransition();
    clearTransition();
    const preference = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const commit = () => {
      // A skipped transition can still invoke its deferred update callback.
      if (request === navigation.current)
        flushSync(() => {
          if (nextId !== null && selectedIndex === undefined) {
            const nextTarget = targets.find((item) => item.id === nextId);
            const initial =
              nextTarget?.routes.find((route) => route.schedule.index === nextTarget.planIndex) ??
              nextTarget?.routes[0];
            setViewedRoutes((current) =>
              current[nextId]
                ? current
                : {
                    ...current,
                    [nextId]: {
                      index: initial?.schedule.index ?? -1,
                      identity: initial ? routeIdentity(initial) : "",
                      expanded: false,
                    },
                  },
            );
          }
          setTargetId(nextId);
          onTargetChange?.(nextId);
        });
    };
    if (
      !document.startViewTransition ||
      preference?.matches ||
      explorer.current?.closest('[data-still="true"]')
    ) {
      commit();
      return;
    }
    const mark = () => {
      const destination =
        targetButtons.current.get(returnTarget.current ?? "") ??
        explorer.current?.querySelector('.route-journey-node[data-kind="target"]');
      const parts = {
        field: explorer.current?.querySelector("svg"),
        beacon: destination?.querySelector(".route-explorer-beacon, .route-journey-beacon"),
        role: destination?.querySelector("strong"),
      };
      for (const [part, element] of Object.entries(parts)) {
        if (!(element instanceof HTMLElement || element instanceof SVGElement)) continue;
        element.style.viewTransitionName = `cw-focus-${id.replace(/[^a-zA-Z0-9_-]/g, "")}-${part}`;
        element.style.viewTransitionClass = `cw-focus-${part}`;
        transitionElements.current.add(element);
      }
    };
    document.documentElement.dataset.careerwrightTransition =
      nextId === null ? "overview" : "focus";
    document.documentElement.dataset.careerwrightTransitionOwner = id;
    const origin =
      targetButtons.current.get(returnTarget.current ?? "") ??
      explorer.current?.querySelector<HTMLElement>('.route-journey-node[data-kind="target"]');
    document.documentElement.style.setProperty(
      "--careerwright-focus-x",
      origin?.style.left || "85%",
    );
    document.documentElement.style.setProperty(
      "--careerwright-focus-y",
      origin?.style.top || "26%",
    );
    const scroll = { left: window.scrollX, top: window.scrollY };
    mark();
    try {
      const next = document.startViewTransition(() => {
        commit();
        // Replacing the focused snapshot can reset native scroll before focus prevention runs.
        if (
          request === navigation.current &&
          (window.scrollX !== scroll.left || window.scrollY !== scroll.top)
        )
          window.scrollTo({ ...scroll, behavior: "instant" });
        if (
          request === navigation.current &&
          !preference?.matches &&
          !explorer.current?.closest('[data-still="true"]')
        )
          mark();
      });
      transition.current = next;
      void next.ready.catch(() => {});
      const finish = () => {
        if (request !== navigation.current) return;
        transition.current = null;
        clearTransition();
      };
      void next.finished.then(finish, finish);
    } catch {
      clearTransition();
      commit();
    }
  };
  return (
    <section ref={explorer} className="route-explorer" aria-label="Explore possible destinations">
      {target ? (
        <>
          <div className="route-explorer-controls">
            <button ref={allTargetsButton} type="button" onClick={() => navigate(null)}>
              All targets
            </button>
            {targets.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-expanded={item.id === target.id}
                aria-controls={`${id}-focus`}
                onClick={() => navigate(item.id)}
              >
                {item.title}
              </button>
            ))}
          </div>
          <div id={`${id}-focus`}>
            <h2>{target.title}</h2>
            <RouteJourney
              key={target.id}
              routes={target.routes}
              targetTitle={target.title}
              startLabel={startLabel}
              selectedIndex={viewedIndex}
              initialExpandedIndex={
                viewed?.expanded && rememberedRoute ? rememberedRoute.schedule.index : undefined
              }
              onSelect={(index) => {
                const route = target.routes.find((item) => item.schedule.index === index);
                if (!route) return;
                setViewedRoutes((current) => ({
                  ...current,
                  [target.id]: { index, identity: routeIdentity(route), expanded: true },
                }));
                onSelect?.(target.id, index);
              }}
              onCollapse={() =>
                setViewedRoutes((current) => {
                  const viewed = current[target.id];
                  return viewed
                    ? { ...current, [target.id]: { ...viewed, expanded: false } }
                    : current;
                })
              }
              planIndex={target.planIndex}
              completedSteps={target.completedSteps}
              status={target.status}
              scheduleCount={target.scheduleCount}
              detailStatus={target.detailStatus}
              routeSetId={target.routeSetId}
              revealSelected={selectedIndex !== undefined}
            />
          </div>
        </>
      ) : (
        <>
          <p className="route-explorer-note">
            Choose a destination, then unfold one route at a time. Trails bundle possible routes;
            they do not represent direct job transitions.
          </p>
          <div id={`${id}-focus`} className="route-explorer-map">
            <div
              className="route-explorer-canvas"
              style={{
                position: "relative",
                minWidth: 640,
                height: Math.max(510, targets.length * 170),
              }}
            >
              <svg
                className="route-explorer-lines"
                viewBox={`0 0 640 ${Math.max(510, targets.length * 170)}`}
                preserveAspectRatio="none"
                aria-hidden="true"
                focusable="false"
              >
                <defs>
                  <linearGradient id={`${id}-trail`} x1="0%" y1="100%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="var(--trail-near)" />
                    <stop offset="100%" stopColor="var(--trail-far)" />
                  </linearGradient>
                  <filter id={`${id}-bloom`} x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="5" />
                  </filter>
                  <radialGradient id={`${id}-destination`}>
                    <stop offset="0%" stopColor="var(--decision-destination)" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="var(--decision-destination)" stopOpacity="0" />
                  </radialGradient>
                </defs>
                {targets.map((item, index) => {
                  const height = Math.max(510, targets.length * 170);
                  const y =
                    ((targets.length <= 3
                      ? 12 + index * 31
                      : 12 + (index * 76) / (targets.length - 1)) /
                      100) *
                    height;
                  const d = `M83.2,${height * 0.8} C260,${height * 0.8} 300,${y} 505.6,${y}`;
                  return (
                    <g key={item.id} data-route-state={targetRouteState(item.routes, item.status)}>
                      <circle cx="505.6" cy={y} r="62" fill={`url(#${id}-destination)`} />
                      <path
                        className="route-journey-aura"
                        d={d}
                        stroke={`url(#${id}-trail)`}
                        filter={`url(#${id}-bloom)`}
                      />
                      <path className="route-journey-trail" d={d} stroke={`url(#${id}-trail)`} />
                      <path className="route-explorer-trail" d={d} stroke={`url(#${id}-trail)`} />
                    </g>
                  );
                })}
              </svg>
              <div
                className="route-explorer-origin"
                style={{ position: "absolute", left: "13%", top: "80%" }}
              >
                <span className="route-explorer-beacon" aria-hidden="true" />
                <span className="route-explorer-label">
                  <small>Starting point</small>
                  <strong>{startLabel}</strong>
                </span>
              </div>
              {targets.map((item, index) => (
                <button
                  key={item.id}
                  ref={(element) => {
                    if (element) targetButtons.current.set(item.id, element);
                    else targetButtons.current.delete(item.id);
                  }}
                  className="route-explorer-target"
                  data-route-state={targetRouteState(item.routes, item.status)}
                  type="button"
                  style={{
                    position: "absolute",
                    left: "79%",
                    top: `${targets.length <= 3 ? 12 + index * 31 : 12 + (index * 76) / (targets.length - 1)}%`,
                  }}
                  aria-expanded={false}
                  aria-controls={`${id}-focus`}
                  onClick={() => navigate(item.id)}
                >
                  <span className="route-explorer-beacon" aria-hidden="true" />
                  <span className="route-explorer-label">
                    <strong>{item.title}</strong>{" "}
                    <span>
                      {routeCountWords(item)}
                      {item.routes.length ? " · " : ""}
                      {item.routes.length > 0 &&
                        stepCounts(item.routes.flatMap((route) => route.steps))}
                    </span>{" "}
                    <small className="route-state-status">
                      {routeStateWords(targetRouteState(item.routes, item.status))}
                    </small>
                    {item.scheduleCount !== undefined &&
                      item.scheduleCount > item.routes.length && (
                        <small>
                          {item.routes.length} route{" "}
                          {item.routes.length === 1 ? "summary" : "summaries"} loaded
                        </small>
                      )}
                    <small>
                      {item.routes.length > 0 &&
                        `Per route: ${Array.from(new Set(item.routes.map(conditionSummary))).join(" / ")}`}
                    </small>
                  </span>
                </button>
              ))}
            </div>
          </div>
          <p className="route-explorer-note">
            Step counts use loaded route summaries. Shared steps count once. Position and distance
            do not compare time, cost or likelihood.
          </p>
          <p className="route-state-legend">
            Faint trails: support not established. Marked trails: planning facts still needed.
            Resolved trails: planning information complete. Conditions and source checks remain
            separate.
          </p>
          <details className="route-explorer-list">
            <summary>Read destinations and route summaries</summary>
            <ul>
              {targets.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    aria-expanded={false}
                    aria-controls={`${id}-focus`}
                    onClick={() => navigate(item.id)}
                  >
                    {item.title}: {routeCountWords(item)}
                  </button>
                  <p>
                    {routeStateWords(targetRouteState(item.routes, item.status))}.{" "}
                    {item.routes.length > 0 &&
                      `${stepCounts(item.routes.flatMap((route) => route.steps))}. Per route: ${Array.from(new Set(item.routes.map(conditionSummary))).join(" / ")}.`}
                  </p>
                </li>
              ))}
            </ul>
          </details>
        </>
      )}
    </section>
  );
}
