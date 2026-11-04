"use client";

import { useEffect, useRef } from "react";
import type { WorldSettings } from "@/lib/world/settings";

export function DecisionAtmosphere({
  settings,
  distress = false,
  showControl = true,
  lit = null,
}: {
  settings: WorldSettings;
  distress?: boolean;
  showControl?: boolean;
  lit?: boolean | null;
}) {
  const { reduced, calm, paused, setPaused, sound } = settings;
  const previousLight = useRef<boolean | null>(null);
  useEffect(() => {
    if (lit === null) return;
    if (lit && previousLight.current === false) sound.play("swell");
    previousLight.current = lit;
  }, [lit, sound]);
  const fixed = reduced || calm || distress;
  return (
    <div className="decision-atmosphere" data-still={paused || fixed} data-distress={distress}>
      <span className="decision-atmosphere-light" aria-hidden="true">
        <span className="decision-atmosphere-motes" />
      </span>
      {showControl && (
        <button
          type="button"
          className="decision-world-motion"
          aria-pressed={paused || fixed}
          disabled={fixed}
          onClick={() => setPaused(!paused)}
        >
          {reduced
            ? "Still · reduced motion"
            : calm
              ? "Still · calm mode"
              : distress
                ? "Still while support is shown"
                : paused
                  ? "Let the world move"
                  : "Hold the world still"}
        </button>
      )}
    </div>
  );
}
