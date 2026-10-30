// The world's visible controls (plan section 4; WCAG 2.2.2): pause ambient motion at any time,
// calm mode kept between visits, and sound, off until the person turns it on (session W1).
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useWorldSettings } from "@/lib/world/settings";
import { WorldControls } from "./WorldControls";

function Harness() {
  return <WorldControls settings={useWorldSettings()} />;
}

function reducedMotion(reduce: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: reduce && query.includes("reduce"),
    addEventListener: () => {},
    removeEventListener: () => {},
  }));
}

class FakeAudioContext {
  resume = vi.fn(async () => {});
  suspend = vi.fn(async () => {});
  destination = {};
  createGain = () => ({ gain: { value: 1 }, connect: (next: unknown) => next });
  createDelay = () => ({ delayTime: { value: 0 }, connect: (next: unknown) => next });
}

const toggle = (name: string) => screen.getByRole("button", { name: new RegExp(`^${name}`) });

describe("[UI-05][UI-06] the world's controls", () => {
  beforeEach(() => {
    window.localStorage.clear();
    reducedMotion(false);
    vi.stubGlobal("AudioContext", FakeAudioContext);
  });
  afterEach(() => vi.unstubAllGlobals());

  it("starts moving, with sound off, and pauses ambient motion at any time", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    expect(toggle("Pause motion")).toHaveAttribute("aria-pressed", "false");
    expect(toggle("Calm mode")).toHaveAttribute("aria-pressed", "false");
    expect(toggle("Sound")).toHaveAttribute("aria-pressed", "false");

    await user.click(toggle("Pause motion"));
    expect(toggle("Pause motion")).toHaveAttribute("aria-pressed", "true");
    await user.click(toggle("Pause motion"));
    expect(toggle("Pause motion")).toHaveAttribute("aria-pressed", "false");
  });

  it("keeps calm mode between visits, and calm stills everything, so pause is already on", async () => {
    const user = userEvent.setup();
    const { unmount } = render(<Harness />);
    await user.click(toggle("Calm mode"));

    expect(toggle("Calm mode")).toHaveAttribute("aria-pressed", "true");
    expect(toggle("Pause motion")).toHaveAttribute("aria-pressed", "true");
    expect(toggle("Pause motion")).toHaveAttribute("aria-disabled", "true");
    expect(toggle("Pause motion")).toHaveAccessibleName(/the world is already drawn still/);
    // Still focusable, and pressing it changes nothing while calm mode holds the world still.
    await user.click(toggle("Pause motion"));
    expect(toggle("Pause motion")).toHaveAttribute("aria-pressed", "true");
    expect(document.documentElement.dataset.calm).toBe("true");
    unmount();

    render(<Harness />);
    expect(toggle("Calm mode")).toHaveAttribute("aria-pressed", "true");
  });

  it("follows the device's reduced-motion setting and says why calm mode is fixed on", () => {
    reducedMotion(true);
    render(<Harness />);

    expect(toggle("Calm mode")).toHaveAttribute("aria-pressed", "true");
    expect(toggle("Calm mode")).toHaveAttribute("aria-disabled", "true");
    expect(toggle("Calm mode")).toHaveAccessibleName(/your device asks for less motion/);
  });

  it("turns sound on only when the person asks", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(toggle("Sound"));
    expect(toggle("Sound")).toHaveAttribute("aria-pressed", "true");
    await user.click(toggle("Sound"));
    expect(toggle("Sound")).toHaveAttribute("aria-pressed", "false");
  });
});
