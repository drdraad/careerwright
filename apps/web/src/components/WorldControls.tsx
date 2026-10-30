"use client";
// The world's three visible controls (plan section 4; WCAG 2.2.2): pause the ambient motion at
// any time, calm mode (the world drawn still, kept between visits) and sound (off until the
// person turns it on). Each is a toggle button whose pressed state is its setting.
import type { WorldSettings } from "@/lib/world/settings";
import { Glyph, type GlyphName } from "./Glyph";

function Toggle({
  glyph,
  label,
  pressed,
  fixed,
  onToggle,
}: {
  glyph: GlyphName;
  label: string;
  pressed: boolean;
  /**
   * Why the control cannot change now. It stays focusable (aria-disabled, as every disabled
   * control here) and its name says why; its switch shows the setting in force.
   */
  fixed?: string;
  onToggle(): void;
}) {
  return (
    <button
      type="button"
      className="world-toggle"
      aria-pressed={pressed}
      aria-disabled={fixed !== undefined || undefined}
      onClick={fixed === undefined ? onToggle : undefined}
    >
      <Glyph name={glyph} />
      <span className="world-toggle-label">{label}</span>
      <span className="world-switch" aria-hidden="true" />
      {fixed !== undefined && <span className="sr-only">: {fixed}</span>}
    </button>
  );
}

export function WorldControls({ settings }: { settings: WorldSettings }) {
  const { reduced, calm, paused, soundOn } = settings;
  const still = reduced || calm;
  return (
    <fieldset className="world-controls">
      <legend className="sr-only">The world</legend>
      <Toggle
        glyph="pause"
        label="Pause motion"
        pressed={paused || still}
        fixed={still ? "the world is already drawn still" : undefined}
        onToggle={() => settings.setPaused(!paused)}
      />
      <Toggle
        glyph="calm"
        label="Calm mode"
        pressed={calm || reduced}
        fixed={
          reduced ? "your device asks for less motion, so the world is always still" : undefined
        }
        onToggle={() => settings.setCalm(!calm)}
      />
      <Toggle
        glyph="sound"
        label="Sound"
        pressed={soundOn}
        onToggle={() => settings.setSoundOn(!soundOn)}
      />
    </fieldset>
  );
}
