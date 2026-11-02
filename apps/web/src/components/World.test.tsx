// The world behind every chapter (plan section 4): the canvas holds nothing unique, so every
// light it draws has its words in the DOM; the still world carries the same states; changing
// chapter moves the view to that chapter's place. jsdom has no WebGL, so the moving world's
// renderer is replaced by a stand-in here; the real one is covered in the browser suites.
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { WorldInput } from "@/lib/world/model";
import type { Sound } from "@/lib/world/sound";
import { World } from "./World";

const gl = vi.hoisted(() => ({ available: false, refuses: false }));

vi.mock("@/lib/world/gl", () => ({
  webgl2Available: () => gl.available,
  GLWorld: class {
    constructor() {
      if (gl.refuses) throw new Error("Error creating WebGL context.");
    }
    resize() {}
    setScene() {}
    render() {}
    dispose() {}
    measureGpu() {
      return false;
    }
    takeGpuSamples() {
      return [];
    }
    rendererName() {
      return "stand-in";
    }
    canvasSize() {
      return [1, 1];
    }
  },
}));

const input: WorldInput = {
  lit: true,
  destinations: [
    { id: "d", title: "Data quality analyst", shared: [] },
    { id: "s", title: "Statistician", shared: [] },
  ],
  skills: [],
  openings: 0,
};

function motion({ reduce, webgl2 }: { reduce: boolean; webgl2: boolean }) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: reduce && query.includes("reduce"),
    addEventListener: () => {},
    removeEventListener: () => {},
  }));
  gl.available = webgl2;
}

const world = () => document.querySelector<HTMLElement>(".world");
const names = () =>
  within(screen.getByRole("complementary", { name: "Your world" }))
    .getAllByRole("listitem")
    .map((item) => item.textContent);

describe("[WLD-01][WLD-02][WLD-03][WLD-07][UI-07][UI-05] the world behind every chapter", () => {
  beforeEach(() => {
    gl.refuses = false;
    motion({ reduce: false, webgl2: false });
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("draws the still world without WebGL2, with every light's words in the DOM", () => {
    render(<World place="roles" input={input} calm={false} paused={false} />);

    expect(world()).toHaveAttribute("data-world-mode", "still");
    expect(screen.getByTestId("still-world")).toBeInTheDocument();
    const words = screen.getByRole("complementary", { name: "Your world" });
    const items = within(words).getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("You: Your light, lit by your answers");
    expect(within(words).getByText("Data quality analyst")).toBeInTheDocument();
    expect(within(words).getByText("Statistician")).toBeInTheDocument();
    const legend = screen.getByRole("list", { name: "What the lights mean" });
    expect(legend).toHaveTextContent("Warm lights: places you chose to head for");
    expect(legend).toHaveTextContent("Grey trails: not known yet");
  });

  it("names every skill and counts the openings in the DOM, so the canvas holds nothing unique", () => {
    // W2A app review M3: skills and openings must be named before the world draws them.
    render(
      <World
        place="you"
        input={{
          ...input,
          skills: [
            { id: "k1", label: "Keep accurate records", state: "usual" },
            { id: "k2", label: "Check data for errors", state: "said" },
          ],
          openings: 7,
        }}
        calm={false}
        paused={false}
      />,
    );

    const words = screen.getByRole("complementary", { name: "Your world" });
    expect(within(words).getByText("Keep accurate records").closest("li")).toHaveTextContent(
      "Keep accurate records: ESCO lists it, not confirmed yet",
    );
    expect(within(words).getByText("Check data for errors").closest("li")).toHaveTextContent(
      "Check data for errors: you said you've done it",
    );
    // One count line for the openings, never a hundred names.
    expect(within(words).getByText("7 openings").closest("li")).toHaveTextContent(
      "7 openings: small lights around the places you chose",
    );
    expect(within(words).getAllByRole("listitem")).toHaveLength(1 + 2 + 2 + 1);
    // The key explains every light but the person's, and lists only the kinds drawn.
    const keyed = [...words.querySelectorAll<HTMLElement>("[data-keyed='true']")].map(
      (item) => item.dataset.kind,
    );
    expect(keyed.sort()).toEqual(["destination", "destination", "openings", "skill", "skill"]);
    expect(words.querySelector("[data-kind='origin']")).toHaveAttribute("data-keyed", "false");
    const legend = screen.getByRole("list", { name: "What the lights mean" });
    expect(legend).toHaveTextContent("Bright: you said you've done it");
    expect(legend).toHaveTextContent(
      "Faint ring: ESCO lists it for this kind of work, not confirmed yet",
    );
    expect(words).not.toHaveTextContent(/usual/);
    expect(legend).toHaveTextContent("Small lights: openings");
  });

  it("waits with one light until the first answer, and explains nothing it cannot show", () => {
    render(
      <World
        place="you"
        input={{ lit: false, destinations: [], skills: [], openings: 0 }}
        calm={false}
        paused={false}
      />,
    );

    expect(screen.getByText(/Your light comes on with your first answer/)).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "What the lights mean" })).toBeNull();
  });

  it("travels to the chapter's place", () => {
    const { rerender } = render(<World place="you" input={input} calm={false} paused={false} />);
    expect(world()).toHaveAttribute("data-place", "you");
    rerender(<World place="skills" input={input} calm={false} paused={false} />);
    expect(world()).toHaveAttribute("data-place", "skills");
  });

  it.each([
    ["calm mode", { reduce: false, calm: true, distress: false }],
    ["reduced motion", { reduce: true, calm: false, distress: false }],
    ["the calm support panel", { reduce: false, calm: false, distress: true }],
  ])("is drawn still under %s even where WebGL2 works", (_, { reduce, calm, distress }) => {
    motion({ reduce, webgl2: true });
    render(<World place="you" input={input} calm={calm} paused={false} distress={distress} />);

    expect(world()).toHaveAttribute("data-world-mode", "still");
    expect(screen.queryByTestId("moving-world")).toBeNull();
    expect(screen.getByTestId("still-world")).toBeInTheDocument();
  });

  it("moves again when the support panel closes", () => {
    motion({ reduce: false, webgl2: true });
    const { rerender } = render(
      <World place="you" input={input} calm={false} paused={false} distress />,
    );
    expect(world()).toHaveAttribute("data-distress", "true");
    expect(world()).toHaveAttribute("data-world-mode", "still");
    rerender(<World place="you" input={input} calm={false} paused={false} />);
    expect(world()).toHaveAttribute("data-world-mode", "moving");
  });

  it("falls back to the still world, with the same names, when the WebGL context is lost", () => {
    motion({ reduce: false, webgl2: true });
    render(<World place="roles" input={input} calm={false} paused={false} />);
    expect(world()).toHaveAttribute("data-world-mode", "moving");
    const before = names();

    act(() => {
      screen.getByTestId("moving-world").dispatchEvent(new Event("webglcontextlost"));
    });

    expect(world()).toHaveAttribute("data-world-mode", "still");
    expect(screen.getByTestId("still-world")).toBeInTheDocument();
    expect(names()).toEqual(before);
  });

  it("falls back to the still world, and keeps the page, when the renderer cannot start", () => {
    motion({ reduce: false, webgl2: true });
    gl.refuses = true;
    render(<World place="roles" input={input} calm={false} paused={false} />);

    expect(world()).toHaveAttribute("data-world-mode", "still");
    expect(screen.getByTestId("still-world")).toBeInTheDocument();
    expect(names()).toHaveLength(3);
  });

  it("holds ambient motion while the person types, then moves again on its own", async () => {
    vi.useFakeTimers({
      toFake: [
        "requestAnimationFrame",
        "cancelAnimationFrame",
        "performance",
        "setTimeout",
        "clearTimeout",
      ],
    });
    motion({ reduce: false, webgl2: true });
    render(
      <>
        <input aria-label="Reply" />
        <World place="roles" input={input} calm={false} paused={false} />
      </>,
    );
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });
    expect(world()).toHaveAttribute("data-motion", "running");

    fireEvent.keyDown(screen.getByRole("textbox", { name: "Reply" }), { key: "a" });
    await act(async () => {
      vi.advanceTimersByTime(1400);
    });
    expect(world()).toHaveAttribute("data-motion", "still");

    // Nothing else happens: no pointer, no change, no chapter. The hold ends by itself.
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });
    expect(world()).toHaveAttribute("data-motion", "running");
  });

  it("[WLD-05] moves again when the person lets go, however soon the next frame comes", async () => {
    vi.useFakeTimers({
      toFake: ["requestAnimationFrame", "cancelAnimationFrame", "performance"],
    });
    motion({ reduce: false, webgl2: true });
    const { rerender } = render(<World place="roles" input={input} calm={false} paused />);
    await act(async () => {
      vi.advanceTimersByTime(4000);
    });
    expect(world()).toHaveAttribute("data-motion", "still");
    // Two more frames (on the 16 ms grid), so the frames are stopped at rest.
    await act(async () => {
      vi.advanceTimersByTime(32);
    });

    // Let go about a millisecond before the next frame is due: that first frame's step is
    // tiny, and must still count as moving (the click was once lost this way).
    await act(async () => {
      vi.advanceTimersByTime(15.5);
    });
    rerender(<World place="roles" input={input} calm={false} paused={false} />);
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });
    expect(world()).toHaveAttribute("data-motion", "running");
  });

  it("measures the panels again when a view is shown or hidden, with nothing added or removed (re-review N1)", async () => {
    // The You chapter's views stay mounted and switch by `hidden`: with no child or text
    // change, the world must still notice that the panel over it moved.
    vi.useFakeTimers({ toFake: ["requestAnimationFrame", "cancelAnimationFrame"] });
    motion({ reduce: true, webgl2: false });
    const panel = document.createElement("div");
    panel.setAttribute("data-world-panel", "");
    const view = document.createElement("div");
    panel.append(view);
    document.body.append(panel);
    const measured = vi.spyOn(panel, "getBoundingClientRect");
    render(<World place="you" input={input} calm={false} paused={false} />);
    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    for (const change of [
      () => view.setAttribute("hidden", ""),
      () => view.removeAttribute("hidden"),
    ]) {
      const before = measured.mock.calls.length;
      change();
      await act(async () => {
        await Promise.resolve(); // the observer's records arrive as a microtask
        vi.advanceTimersByTime(100);
      });
      expect(measured.mock.calls.length).toBeGreaterThan(before);
    }
    panel.remove();
  });

  it("swells when the person's light comes on, never for what was there on arrival", () => {
    const play = vi.fn();
    const sound = { play } as unknown as Sound;
    const dark: WorldInput = { lit: false, destinations: [], skills: [], openings: 0 };
    const { rerender } = render(
      <World place="you" input={null} calm={false} paused={false} sound={sound} />,
    );
    rerender(<World place="you" input={dark} calm={false} paused={false} sound={sound} />);
    expect(play).not.toHaveBeenCalled();
    rerender(<World place="you" input={input} calm={false} paused={false} sound={sound} />);
    expect(play).toHaveBeenCalledExactlyOnceWith("swell");

    const arrivedLit = vi.fn();
    render(
      <World
        place="you"
        input={input}
        calm={false}
        paused={false}
        sound={{ play: arrivedLit } as unknown as Sound}
      />,
    );
    expect(arrivedLit).not.toHaveBeenCalled();
  });
});
