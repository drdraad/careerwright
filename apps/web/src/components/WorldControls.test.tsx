// The world's controls (plan section 4; WCAG 2.2.2): in the strip, pause ambient motion at any
// time and sound, off until the person turns it on (session W1); in the account menu, calm
// mode, kept between visits. While the calm support panel shows, the world is still on its
// own: Pause keeps the person's own choice and a status says why.
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useWorldSettings } from "@/lib/world/settings";
import { CalmMode, WorldControls } from "./WorldControls";

function Harness({ supportShown = false }: { supportShown?: boolean }) {
  const settings = useWorldSettings();
  return (
    <>
      <WorldControls settings={settings} supportShown={supportShown} />
      <CalmMode settings={settings} />
    </>
  );
}

function reducedMotion(reduce: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: reduce && query.includes("reduce"),
    addEventListener: () => {},
    removeEventListener: () => {},
  }));
}

const contexts: FakeAudioContext[] = [];

class FakeAudioContext {
  constructor() {
    contexts.push(this);
  }
  resume = vi.fn(async () => {});
  suspend = vi.fn(async () => {});
  close = vi.fn(async () => {});
  destination = {};
  createGain = () => ({ gain: { value: 1 }, connect: (next: unknown) => next });
  createDelay = () => ({ delayTime: { value: 0 }, connect: (next: unknown) => next });
}

const toggle = (name: string) => screen.getByRole("button", { name: new RegExp(`^${name}`) });

describe("[UI-05][UI-06] the world's controls", () => {
  beforeEach(() => {
    window.localStorage.clear();
    contexts.length = 0;
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

  it("turns sound on only when the person asks, and lets the audio go with the shell", async () => {
    const user = userEvent.setup();
    const { unmount } = render(<Harness />);
    expect(contexts).toHaveLength(0);
    await user.click(toggle("Sound"));
    expect(toggle("Sound")).toHaveAttribute("aria-pressed", "true");
    expect(contexts).toHaveLength(1);
    await user.click(toggle("Sound"));
    expect(toggle("Sound")).toHaveAttribute("aria-pressed", "false");
    unmount();
    expect(contexts[0]?.close).toHaveBeenCalledOnce();
  });

  it("says the world is still while support is shown, and keeps Pause as the person left it", async () => {
    const user = userEvent.setup();
    render(<Harness supportShown />);

    expect(screen.getByRole("status")).toHaveTextContent("Still while support is shown");
    expect(toggle("Pause motion")).toHaveAttribute("aria-pressed", "false");
    expect(toggle("Pause motion")).not.toHaveAttribute("aria-disabled");
    await user.click(toggle("Pause motion"));
    expect(toggle("Pause motion")).toHaveAttribute("aria-pressed", "true");
  });
});
