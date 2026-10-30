// The still world draws each trail at the strength the design references measure it at
// (TRAIL_OPACITY, held to the tokens by tokens.test.ts): 3:1 or more as drawn, the same as the
// moving world's core (W2A review, D-I3).
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { View } from "@/lib/world/geometry";
import { TRAIL_OPACITY } from "@/lib/world/palette";
import type { Scene, TrailState } from "@/lib/world/scene";
import { StillWorld } from "./StillWorld";

const vp = { w: 1440, h: 900 };
const view: View = { x: 0, z: 0, eye: 1, horizon: 360, centre: 720, focal: 900 };

/** One trail in the given state, running out from the person towards the horizon. */
function sceneWith(state: TrailState): Scene {
  const points = Array.from({ length: 25 }, (_, i) => [0, 0.02, 1.7 + i * 0.6] as const);
  return {
    nodes: [],
    trails: [
      {
        id: `trail:${state}`,
        points,
        state,
        birth: 0,
        duration: 0,
        width: [0.016, 0.05],
        hue: [0, 1],
        reach: 0,
      },
    ],
  };
}

describe("[UI-04][UI-05] the still world draws each trail at its measured strength", () => {
  it.each(Object.entries(TRAIL_OPACITY))("draws %s trails at %s", (state, strength) => {
    const { getByTestId } = render(
      <StillWorld scene={sceneWith(state as TrailState)} view={view} vp={vp} />,
    );
    // The trail's core: every stroke outside the soft glow beneath it.
    const cores = getByTestId("still-world").querySelectorAll(":scope > g:not([filter]) > path");
    expect(cores.length).toBeGreaterThan(0);
    for (const core of cores) {
      expect(Number(core.getAttribute("stroke-opacity"))).toBe(strength);
    }
  });
});
