import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useWorldSettings } from "@/lib/world/settings";
import { Sound } from "@/lib/world/sound";
import { DecisionAtmosphere } from "./DecisionAtmosphere";
import { CalmMode, WorldControls } from "./WorldControls";

let preference: EventTarget & { matches: boolean };

beforeEach(() => {
  window.localStorage.clear();
  preference = Object.assign(new EventTarget(), { matches: false });
  vi.stubGlobal("matchMedia", () => preference);
});

function Harness({
  distress = false,
  controls = false,
  lit = null,
}: {
  distress?: boolean;
  controls?: boolean;
  lit?: boolean | null;
}) {
  const settings = useWorldSettings();
  return (
    <>
      <DecisionAtmosphere
        settings={settings}
        distress={distress}
        showControl={!controls}
        lit={lit}
      />
      {controls && <WorldControls settings={settings} />}
      {controls && <CalmMode settings={settings} />}
    </>
  );
}

function setReduced(reduced: boolean) {
  act(() => {
    preference.matches = reduced;
    preference.dispatchEvent(new Event("change"));
  });
}

describe("[WLD-05][WLD-08] Decision atmosphere", () => {
  it("lets the keyboard pause and resume the atmosphere", async () => {
    const user = userEvent.setup();
    const { container } = render(<Harness />);
    const atmosphere = container.querySelector(".decision-atmosphere");
    const button = screen.getByRole("button", { name: "Hold the world still" });
    expect(atmosphere).toHaveAttribute("data-still", "false");
    expect(button).toHaveAttribute("aria-pressed", "false");

    await user.tab();
    expect(button).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(button).toHaveAccessibleName("Let the world move");
    expect(button).toHaveAttribute("aria-pressed", "true");
    expect(atmosphere).toHaveAttribute("data-still", "true");

    await user.keyboard(" ");
    expect(button).toHaveAccessibleName("Hold the world still");
    expect(button).toHaveAttribute("aria-pressed", "false");
    expect(atmosphere).toHaveAttribute("data-still", "false");
  });

  it("honours reduced motion live and preserves the viewer's pause choice", async () => {
    preference.matches = true;
    const user = userEvent.setup();
    const { container } = render(<Harness />);
    const atmosphere = container.querySelector(".decision-atmosphere");
    const button = screen.getByRole("button", { name: "Still · reduced motion" });
    expect(button).toBeDisabled();
    expect(atmosphere).toHaveAttribute("data-still", "true");

    setReduced(false);
    expect(button).toBeEnabled();
    expect(button).toHaveAccessibleName("Hold the world still");
    expect(atmosphere).toHaveAttribute("data-still", "false");
    await user.click(button);

    setReduced(true);
    expect(button).toHaveAccessibleName("Still · reduced motion");
    expect(button).toBeDisabled();
    expect(atmosphere).toHaveAttribute("data-still", "true");

    setReduced(false);
    expect(button).toHaveAccessibleName("Let the world move");
    expect(button).toBeEnabled();
    expect(button).toHaveAttribute("aria-pressed", "true");
    expect(atmosphere).toHaveAttribute("data-still", "true");
  });

  it("shares production pause and calm settings and stills while support is shown", async () => {
    const user = userEvent.setup();
    const { container, rerender } = render(<Harness controls />);
    const atmosphere = container.querySelector(".decision-atmosphere");
    expect(atmosphere).toHaveAttribute("data-still", "false");
    await user.click(screen.getByRole("button", { name: "Hold the world still" }));
    expect(atmosphere).toHaveAttribute("data-still", "true");
    await user.click(screen.getByRole("button", { name: "Hold the world still" }));
    await user.click(screen.getByRole("button", { name: "Calm mode" }));
    expect(atmosphere).toHaveAttribute("data-still", "true");
    await user.click(screen.getByRole("button", { name: "Calm mode" }));
    expect(atmosphere).toHaveAttribute("data-still", "false");
    rerender(<Harness controls distress />);
    expect(atmosphere).toHaveAttribute("data-still", "true");
    expect(atmosphere).toHaveAttribute("data-distress", "true");
    rerender(<Harness controls />);
    expect(atmosphere).toHaveAttribute("data-still", "false");
  });

  it("sounds the first saved answer during the visit and keeps an already lit arrival quiet", () => {
    const play = vi.spyOn(Sound.prototype, "play");
    const { unmount } = render(<Harness lit />);
    expect(play).not.toHaveBeenCalled();
    unmount();
    const next = render(<Harness />);
    next.rerender(<Harness lit={false} />);
    expect(play).not.toHaveBeenCalled();
    next.rerender(<Harness lit />);
    expect(play).toHaveBeenCalledExactlyOnceWith("swell");
    next.rerender(<Harness lit />);
    expect(play).toHaveBeenCalledTimes(1);
    play.mockRestore();
  });

  it("removes the motion preference listener when the atmosphere unmounts", () => {
    const add = vi.spyOn(preference, "addEventListener");
    const remove = vi.spyOn(preference, "removeEventListener");
    const { unmount } = render(<Harness />);
    expect(add).toHaveBeenCalledWith("change", expect.any(Function));
    const listener = add.mock.calls[0]?.[1];

    unmount();
    expect(remove).toHaveBeenCalledWith("change", listener);
  });
});
