"use client";
// The world's controls (plan section 4; WCAG 2.2.2). In the strip: pause the ambient motion at
// any time, and sound (off until the person turns it on). In the account menu: calm mode (the
// world drawn still, kept between visits), a setting kept off the first screen. Each is a toggle
// button whose pressed state is its setting. While the calm support panel shows, the world is
// still on its own: Pause keeps showing the person's own choice, and a status says why (in the
// strip, or on a phone in the top bar, where it adds no row; the other copy is not displayed).
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

export function WorldControls({
  settings,
  supportShown = false,
}: {
  settings: WorldSettings;
  /** The calm support panel is showing, so the world is still whatever Pause says. */
  supportShown?: boolean;
}) {
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
      {supportShown && <StillWhileSupport />}
      <Toggle
        glyph="sound"
        label="Sound"
        pressed={soundOn}
        onToggle={() => settings.setSoundOn(!soundOn)}
      />
    </fieldset>
  );
}

/** Why the world is still while the calm support panel shows. */
export function StillWhileSupport() {
  return (
    <span className="status world-still-status" role="status">
      <Glyph name="support" />
      <span>Still while support is shown</span>
    </span>
  );
}

/** Calm mode, in the account menu: the same setting, words and device override as ever. */
export function CalmMode({ settings }: { settings: WorldSettings }) {
  const { reduced, calm } = settings;
  return (
    <Toggle
      glyph="calm"
      label="Calm mode"
      pressed={calm || reduced}
      fixed={reduced ? "your device asks for less motion, so the world is always still" : undefined}
      onToggle={() => settings.setCalm(!calm)}
    />
  );
}
