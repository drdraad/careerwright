// The world behind every chapter (plan section 4): the canvas holds nothing unique, so every
// light it draws has its words in the DOM; the still world carries the same states; changing
// chapter moves the view to that chapter's place. jsdom has no WebGL, so these tests see the
// still world unless WebGL2 is faked; the moving world is covered in the browser suites.
import { render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { WorldInput } from "@/lib/world/model";
import type { Sound } from "@/lib/world/sound";
import { World } from "./World";

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
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(
    () => (webgl2 ? ({} as RenderingContext) : null) as never,
  );
}

const world = () => document.querySelector<HTMLElement>(".world");

describe("[UI-07][UI-05] the world behind every chapter", () => {
  beforeEach(() => motion({ reduce: false, webgl2: false }));
  afterEach(() => vi.unstubAllGlobals());

  it("draws the still world without WebGL2, with every light's words in the DOM", () => {
    render(<World place="roles" input={input} calm={false} paused={false} />);

    expect(world()).toHaveAttribute("data-world-mode", "still");
    expect(screen.getByTestId("still-world")).toBeInTheDocument();
    const words = screen.getByRole("complementary", { name: "Your world" });
    const items = within(words).getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("You: Your light, lit by your answers");
    expect(within(words).getByText("Data quality analyst")).toBeInTheDocument();
    expect(within(words).getByText("Statistician")).toBeInTheDocument();
    const legend = within(words).getByRole("list", { name: "What the lights mean" });
    expect(legend).toHaveTextContent("Warm lights: places you chose to head for");
    expect(legend).toHaveTextContent("Slate trails: not known yet");
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
    ["calm mode", { reduce: false, calm: true }],
    ["reduced motion", { reduce: true, calm: false }],
  ])("is drawn still under %s even where WebGL2 works", (_, { reduce, calm }) => {
    motion({ reduce, webgl2: true });
    render(<World place="you" input={input} calm={calm} paused={false} />);

    expect(world()).toHaveAttribute("data-world-mode", "still");
    expect(screen.queryByTestId("moving-world")).toBeNull();
    expect(screen.getByTestId("still-world")).toBeInTheDocument();
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
