// The still world: the same scene, the same states, drawn once as SVG with no WebGL and no
// motion. Used for reduced motion, calm mode and browsers without WebGL2.
import type { Camera, Direction, Viewport } from "./direction.ts";
import type { Scene, SceneNode, SceneTrail, Vec3 } from "./scene.ts";

export const PALETTE = {
  blue: [64, 140, 255],
  violet: [158, 107, 255],
  teal: "#45f7d4",
  orange: "#ff9433",
  shadow: "#5d6c90",
  white: "#edf5ff",
} as const;

const smooth = (t: number): number => t * t * (3 - 2 * t);

export function journey(h: number): string {
  const t = smooth(Math.min(1, Math.max(0, h)));
  const c = PALETTE.blue.map((b, i) => Math.round(b + ((PALETTE.violet[i] as number) - b) * t));
  return `rgb(${c.join(",")})`;
}

const fmt = (n: number): string => n.toFixed(1);

export function drawStill(direction: Direction, vp: Viewport, cam: Camera, scene: Scene): string {
  const project = (p: Vec3) => direction.project(p, cam, vp);
  const defs: string[] = [];
  const glow: string[] = [];
  const lines: string[] = [];
  const marks: string[] = [];

  scene.trails.forEach((trail, n) => drawTrail(trail, n));
  for (const node of scene.nodes) drawNode(node);

  function drawTrail(trail: SceneTrail, n: number): void {
    const pts = trail.points.map(project);
    const first = pts[0];
    const last = pts[pts.length - 1];
    if (!first || !last) return;
    const said = trail.state === "said";
    let stroke: string;
    if (trail.chosen) stroke = PALETTE.teal;
    else if (trail.state === "shadow") stroke = PALETTE.shadow;
    else {
      defs.push(
        `<linearGradient id="t${n}" gradientUnits="userSpaceOnUse" x1="${fmt(first.x)}" y1="${fmt(first.y)}" x2="${fmt(last.x)}" y2="${fmt(last.y)}"><stop offset="0" stop-color="${journey(trail.hue[0])}"/><stop offset="1" stop-color="${journey(trail.hue[1])}"/></linearGradient>`,
      );
      stroke = `url(#t${n})`;
    }
    const opacity = { usual: 0.55, said: 1, shadow: 0.75, opening: 0.4, fibre: 0.22 }[trail.state];
    const dash = trail.state === "shadow" ? ' stroke-dasharray="5 6"' : "";
    // Split into short runs so that a trail can narrow with distance (Horizon).
    const run = direction.id === "horizon" ? 6 : pts.length;
    for (let i = 0; i < pts.length - 1; i += run) {
      const part = pts.slice(i, Math.min(pts.length, i + run + 1));
      const mid = part[Math.floor(part.length / 2)] ?? first;
      const u = (i + run / 2) / Math.max(1, pts.length - 1);
      const w = Math.max(0.7, (trail.width[0] + (trail.width[1] - trail.width[0]) * Math.min(1, u)) * mid.scale);
      const d = `M${part.map((p) => `${fmt(p.x)} ${fmt(p.y)}`).join("L")}`;
      lines.push(
        `<path d="${d}" stroke="${stroke}" stroke-width="${fmt(w * (said ? 1.15 : 1))}" stroke-opacity="${opacity}" fill="none" stroke-linecap="round"${dash}/>`,
      );
      if (trail.state !== "fibre" && trail.state !== "shadow")
        glow.push(
          `<path d="${d}" stroke="${stroke}" stroke-width="${fmt(w * 4 + 4)}" stroke-opacity="${said || trail.chosen ? 0.3 : 0.13}" fill="none" stroke-linecap="round"/>`,
        );
    }
  }

  function drawNode(node: SceneNode): void {
    const p = project(node.p);
    if (!p.visible) return;
    const r = Math.max(node.kind === "opening" ? 1.6 : 2.6, node.size * p.scale);
    const x = fmt(p.x);
    const y = fmt(p.y);
    const halo = (color: string, size: number, opacity: number) =>
      `<circle cx="${x}" cy="${y}" r="${fmt(size)}" fill="${color}" opacity="${opacity}" filter="url(#soft)"/>`;
    const square = direction.id === "circuit";
    const shape = (size: number, attrs: string, diamond = false) =>
      square
        ? `<rect x="${fmt(p.x - size)}" y="${fmt(p.y - size)}" width="${fmt(size * 2)}" height="${fmt(size * 2)}" rx="${fmt(size * 0.3)}" ${attrs}${diamond ? ` transform="rotate(45 ${x} ${y})"` : ""}/>`
        : `<circle cx="${x}" cy="${y}" r="${fmt(size)}" ${attrs}/>`;
    switch (node.kind) {
      case "origin":
        marks.push(halo("#9cc4ff", r * 4.5, node.state === "said" ? 0.55 : 0.3));
        marks.push(shape(r * (square ? 0.9 : 1), `fill="${PALETTE.white}"`));
        if (square)
          marks.push(shape(r * 1.8, `fill="none" stroke="#9cc4ff" stroke-width="1.5" stroke-opacity="0.8"`));
        break;
      case "skill":
        if (node.state === "said") {
          marks.push(halo(journey(0.35), r * 3.2, 0.6));
          marks.push(shape(r, `fill="#cfe0ff"`));
        } else {
          marks.push(shape(r * 0.85, `fill="none" stroke="${journey(0.35)}" stroke-width="${fmt(Math.max(1.2, r * 0.32))}" stroke-opacity="0.85"`));
        }
        break;
      case "destination":
      case "revealed":
        marks.push(halo(PALETTE.orange, r * (node.kind === "revealed" ? 4.2 : 3.2), 0.55));
        if (direction.id === "horizon")
          marks.push(
            `<rect x="${fmt(p.x - r * 0.35)}" y="${fmt(p.y + r * 1.2)}" width="${fmt(r * 0.7)}" height="${fmt(r * 6)}" fill="${PALETTE.orange}" opacity="0.28" filter="url(#soft)"/>`,
          );
        marks.push(shape(r, `fill="#ffd2a1"`, true));
        if (node.selected)
          marks.push(`<circle cx="${x}" cy="${y}" r="${fmt(r * 2.3)}" fill="none" stroke="${PALETTE.teal}" stroke-width="2"/>`);
        break;
      case "unknown":
        marks.push(shape(r * 0.9, `fill="none" stroke="${PALETTE.shadow}" stroke-width="1.6" stroke-dasharray="3 3"`));
        break;
      case "opening":
        marks.push(`<circle cx="${x}" cy="${y}" r="${fmt(r)}" fill="${PALETTE.white}" opacity="0.7"/>`);
        break;
    }
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${vp.w}" height="${vp.h}" viewBox="0 0 ${vp.w} ${vp.h}">
  ${direction.stillBackdrop(vp, cam)}
  <defs><filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
  <filter id="bloom" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>${defs.join("")}</defs>
  <g filter="url(#bloom)">${glow.join("")}</g>
  <g>${lines.join("")}</g>
  <g>${marks.join("")}</g>
</svg>`;
}
