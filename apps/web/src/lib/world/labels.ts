// Where each light's words go: beside its own light, inside the window, clear of the panels over
// the world, of every name already placed and of every other light. A name sits centred over its
// light, or slides along its row (still over its light); a crowded one steps out a row at a time,
// with a line back to its light, then tries the other side. That line never crosses another
// light or name, and no name sits on a line already drawn. A name left without a spot chooses
// first next time. A light that is out of view or under a panel has no name in sight, and nor
// does one with no clear spot: its words stay in the list. The design references place names by
// the same rules (docs/design/compositions/world.js).
import type { Projected } from "./geometry";

export type Box = { x: number; y: number; w: number; h: number };

export type LabelRequest = {
  id: string;
  /** Where its light is on screen. */
  at: Projected;
  size: { w: number; h: number };
  /** The side it prefers; the other side is tried next. */
  side: "above" | "below";
};

/** Space between a light and its words, and the margin kept inside the window (CSS pixels). */
const GAP = 14;
const EDGE = 8;
/** Breathing room kept between two names, and between a name and the row beyond it. */
const APART = 4;
const ROW = 6;
/** How many rows out a name may step on each side, with a leader line back to its light. */
const ROWS = 8;
/** A light's centre, kept uncovered by every name but its own. */
const CENTRE = 4;
/** When a name slides along its row, it still reaches this far over its light... */
const OVER = 16;
/** ...and, failing that, this far: its light at its very end. */
const END = 8;
/** A name further than this from its light (CSS pixels) is joined to it by a line. */
export const LEADER_FROM = 20;
/** How many times names left without a spot choose first and the placing is tried again. */
const RETRIES = 6;

const meets = (a: Box, b: Box, pad: number) =>
  a.x < b.x + b.w + pad && b.x < a.x + a.w + pad && a.y < b.y + b.h + pad && b.y < a.y + a.h + pad;

const holds = (b: Box, p: { x: number; y: number }) =>
  p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h;

/** Whether a light can be seen: in front of the eye, inside the window and under no panel. */
export function inView(at: Projected, covers: readonly Box[], vp: { w: number; h: number }) {
  return (
    at.visible && holds({ x: 0, y: 0, w: vp.w, h: vp.h }, at) && !covers.some((c) => holds(c, at))
  );
}

export function layoutLabels(
  requests: readonly LabelRequest[],
  covers: readonly Box[],
  vp: { w: number; h: number },
  /** Boxes names must also stay clear of, placed first (the key to the lights). */
  taken: readonly Box[] = [],
): Map<string, Box | null> {
  const inside = (b: Box) =>
    b.x >= EDGE && b.y >= EDGE && b.x + b.w <= vp.w - EDGE && b.y + b.h <= vp.h - EDGE;
  const lights = requests
    .filter((r) => r.at.visible)
    .map((r) => ({
      id: r.id,
      box: { x: r.at.x - CENTRE, y: r.at.y - CENTRE, w: CENTRE * 2, h: CENTRE * 2 },
    }));

  const place = (order: readonly LabelRequest[]): Map<string, Box | null> => {
    const placed: Box[] = [...taken];
    const lines: Box[] = [];
    const spots = new Map<string, Box | null>();
    for (const { id, at, size, side } of order) {
      if (!inView(at, covers, vp)) {
        spots.set(id, null);
        continue;
      }
      const other = side === "above" ? "below" : "above";
      const across = (x: number) => Math.min(Math.max(x, EDGE), vp.w - EDGE - size.w);
      const along = [
        at.x - size.w / 2,
        at.x - size.w + OVER,
        at.x - OVER,
        at.x - size.w + END,
        at.x - END,
      ];
      const tries: Box[] = [];
      for (const s of [side, other]) {
        for (let row = 0; row < ROWS; row++) {
          const out = GAP + row * (size.h + ROW);
          const y = s === "above" ? at.y - out - size.h : at.y + out;
          for (const x of along) tries.push({ x: across(x), y, w: size.w, h: size.h });
        }
      }
      // The line from a light to its name: it never passes under a panel (a name never hops
      // one), and, where it is drawn, it never crosses another light or name, or the key.
      const leader = (b: Box): Box => {
        const top = Math.min(at.y, b.y + b.h);
        return { x: at.x, y: top, w: 1, h: Math.max(at.y, b.y) - top };
      };
      const lineTo = (b: Box): Box | null => (leader(b).h > LEADER_FROM ? leader(b) : null);
      const clearLine = (line: Box | null) =>
        line === null ||
        (!placed.some((o) => meets(line, o, 0)) &&
          !lights.some((l) => l.id !== id && meets(line, l.box, 0)));
      const spot = tries.find(
        (b) =>
          inside(b) &&
          !covers.some((c) => meets(b, c, 0) || meets(leader(b), c, 0)) &&
          !placed.some((o) => meets(b, o, APART)) &&
          !lines.some((line) => meets(b, line, 0)) &&
          !lights.some((l) => l.id !== id && meets(b, l.box, 0)) &&
          clearLine(lineTo(b)),
      );
      spots.set(id, spot ?? null);
      if (spot === undefined) continue;
      placed.push(spot);
      const line = lineTo(spot);
      if (line !== null) lines.push(line);
    }
    return spots;
  };

  // A name left without a spot while its light is in view chooses first next time, so the
  // hardest names choose first; the placing that leaves the fewest such names is kept.
  const unnamed = (spots: Map<string, Box | null>) =>
    requests.filter((r) => spots.get(r.id) === null && inView(r.at, covers, vp));
  let order = requests;
  let latest = place(order);
  let best = latest;
  for (let attempt = 0; attempt < RETRIES && unnamed(latest).length > 0; attempt++) {
    const left = unnamed(latest);
    order = [...left, ...order.filter((r) => !left.includes(r))];
    latest = place(order);
    if (unnamed(latest).length < unnamed(best).length) best = latest;
  }
  return best;
}
