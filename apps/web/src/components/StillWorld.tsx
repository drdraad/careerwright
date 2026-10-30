// The still world: the same scene, the same states, drawn once as SVG with no WebGL and no
// motion. Drawn for reduced motion, calm mode and browsers without WebGL2 (plan section 4:
// stillness is a first-class version, not a fallback).
import type { ReactNode } from "react";
import { project, type View, type Viewport } from "@/lib/world/geometry";
import { journey, PALETTE } from "@/lib/world/palette";
import { type Scene, type SceneNode, type SceneTrail, seeded, type Vec3 } from "@/lib/world/scene";

const fmt = (n: number): string => n.toFixed(1);

/** Opacity per declared state; shadow is quiet and solid, never dashed and never absent. */
const OPACITY: Record<SceneTrail["state"], number> = {
  usual: 0.55,
  said: 1,
  shadow: 0.8,
  opening: 0.4,
};

function Backdrop({ vp, view }: { vp: Viewport; view: View }) {
  const hy = view.horizon;
  const at = (y: number) => Math.min(1, Math.max(0, y / vp.h)).toFixed(3);
  const rand = seeded("stars");
  const stars = Array.from({ length: 70 }, () => {
    const x = rand() * vp.w;
    const y = rand() * Math.max(0, hy - 70);
    const r = 0.6 + rand();
    const opacity = 0.25 + rand() * 0.5;
    return (
      <circle
        key={`${fmt(x)},${fmt(y)}`}
        cx={fmt(x)}
        cy={fmt(y)}
        r={r.toFixed(2)}
        fill={PALETTE.person}
        opacity={opacity.toFixed(2)}
      />
    );
  });
  return (
    <>
      <defs>
        <linearGradient id="still-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#010309" />
          <stop offset={at(hy - 90)} stopColor="#050a1a" />
          <stop offset={at(hy)} stopColor={PALETTE.horizon} />
          <stop offset={at(hy + 18)} stopColor="#0a1230" />
          <stop offset={at(hy + 160)} stopColor="#050916" />
          <stop offset="1" stopColor={PALETTE.ground} />
        </linearGradient>
        {/* Halos fade from the light outward, so a halo reads as light, never as a disc. */}
        <radialGradient id="still-halo-person">
          <stop offset="0" stopColor="#9cc4ff" stopOpacity="0.9" />
          <stop offset="0.35" stopColor="#5f8fe0" stopOpacity="0.35" />
          <stop offset="1" stopColor="#5f8fe0" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="still-halo-destination">
          <stop offset="0" stopColor={PALETTE.destination} stopOpacity="0.9" />
          <stop offset="0.4" stopColor={PALETTE.destination} stopOpacity="0.3" />
          <stop offset="1" stopColor={PALETTE.destination} stopOpacity="0" />
        </radialGradient>
        <linearGradient id="still-reflection" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={PALETTE.destination} stopOpacity="0.4" />
          <stop offset="1" stopColor={PALETTE.destination} stopOpacity="0" />
        </linearGradient>
        <filter id="still-soft" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" />
        </filter>
        <filter id="still-bloom" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" />
        </filter>
      </defs>
      <rect width={vp.w} height={vp.h} fill="url(#still-sky)" />
      {stars}
    </>
  );
}

function trailPaths(trail: SceneTrail, n: number, view: View) {
  const pts = trail.points.map((p: Vec3) => project(p, view)).filter((p) => p.visible);
  const first = pts[0];
  const last = pts[pts.length - 1];
  if (!first || !last) return { defs: null, glow: [], lines: [] };
  const said = trail.state === "said";
  const gradient = trail.state !== "shadow";
  const stroke = gradient ? `url(#still-trail-${n})` : PALETTE.shadow;
  const defs = gradient ? (
    <linearGradient
      key={`g${n}`}
      id={`still-trail-${n}`}
      gradientUnits="userSpaceOnUse"
      x1={fmt(first.x)}
      y1={fmt(first.y)}
      x2={fmt(last.x)}
      y2={fmt(last.y)}
    >
      <stop offset="0" stopColor={journey(trail.hue[0])} />
      <stop offset="1" stopColor={journey(trail.hue[1])} />
    </linearGradient>
  ) : null;
  const glow: ReactNode[] = [];
  const lines: ReactNode[] = [];
  // Short runs, so a trail narrows with distance as it does in the moving world.
  const run = 6;
  for (let i = 0; i < pts.length - 1; i += run) {
    const part = pts.slice(i, Math.min(pts.length, i + run + 1));
    const mid = part[Math.floor(part.length / 2)] ?? first;
    const u = (i + run / 2) / Math.max(1, pts.length - 1);
    const w = Math.max(
      0.7,
      (trail.width[0] + (trail.width[1] - trail.width[0]) * Math.min(1, u)) * mid.scale,
    );
    const d = `M${part.map((p) => `${fmt(p.x)} ${fmt(p.y)}`).join("L")}`;
    lines.push(
      <path
        key={`l${n}-${i}`}
        d={d}
        stroke={stroke}
        strokeWidth={fmt(w * (said ? 1.15 : 1))}
        strokeOpacity={OPACITY[trail.state]}
        fill="none"
        strokeLinecap="round"
      />,
    );
    glow.push(
      <path
        key={`b${n}-${i}`}
        d={d}
        stroke={stroke}
        strokeWidth={fmt(w * 4 + 4)}
        strokeOpacity={said ? 0.3 : trail.state === "shadow" ? 0.08 : 0.13}
        fill="none"
        strokeLinecap="round"
      />,
    );
  }
  return { defs, glow, lines };
}

function Mark({ node, view }: { node: SceneNode; view: View }) {
  const p = project(node.p, view);
  if (!p.visible) return null;
  const r = Math.max(node.kind === "opening" ? 1.6 : 2.6, node.size * p.scale);
  const x = fmt(p.x);
  const y = fmt(p.y);
  switch (node.kind) {
    case "origin": {
      // Waiting for the first answer: half the size, with a faint halo, as in the moving world.
      const lit = node.state === "said";
      return (
        <g>
          <circle
            cx={x}
            cy={y}
            r={fmt(r * (lit ? 9 : 5))}
            fill="url(#still-halo-person)"
            opacity={lit ? 0.85 : 0.35}
          />
          <circle
            cx={x}
            cy={y}
            r={fmt(r * (lit ? 1 : 0.5))}
            fill={PALETTE.person}
            opacity={lit ? 1 : 0.8}
          />
        </g>
      );
    }
    case "skill":
      return node.state === "said" ? (
        <g>
          <circle
            cx={x}
            cy={y}
            r={fmt(r * 3.2)}
            fill={journey(0.3)}
            opacity={0.6}
            filter="url(#still-soft)"
          />
          <circle cx={x} cy={y} r={fmt(r)} fill="#cfe0ff" />
        </g>
      ) : (
        <circle
          cx={x}
          cy={y}
          r={fmt(r * 0.85)}
          fill="none"
          stroke={journey(0.3)}
          strokeWidth={fmt(Math.max(1.2, r * 0.32))}
          strokeOpacity={0.85}
        />
      );
    case "destination":
      return (
        <g>
          <circle cx={x} cy={y} r={fmt(r * 4)} fill="url(#still-halo-destination)" />
          <rect
            x={fmt(p.x - r * 0.3)}
            y={fmt(p.y + r * 1.2)}
            width={fmt(r * 0.6)}
            height={fmt(r * 6)}
            fill="url(#still-reflection)"
          />
          <circle cx={x} cy={y} r={fmt(r)} fill={PALETTE.destinationCore} />
        </g>
      );
    case "opening":
      return <circle cx={x} cy={y} r={fmt(r)} fill={PALETTE.person} opacity={0.7} />;
  }
}

export function StillWorld({ scene, view, vp }: { scene: Scene; view: View; vp: Viewport }) {
  const drawn = scene.trails.map((trail, n) => trailPaths(trail, n, view));
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={vp.w}
      height={vp.h}
      viewBox={`0 0 ${vp.w} ${vp.h}`}
      aria-hidden="true"
      focusable="false"
      data-testid="still-world"
    >
      <Backdrop vp={vp} view={view} />
      <defs>{drawn.map((d) => d.defs)}</defs>
      <g filter="url(#still-bloom)">{drawn.flatMap((d) => d.glow)}</g>
      <g>{drawn.flatMap((d) => d.lines)}</g>
      <g>
        {scene.nodes.map((node) => (
          <Mark key={node.id} node={node} view={view} />
        ))}
      </g>
    </svg>
  );
}
