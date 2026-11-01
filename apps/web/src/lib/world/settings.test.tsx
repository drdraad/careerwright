// The world is still while any support panel shows (plan section 4: distress stills the
// world). The first question's panel stays until dismissed (Task 6d slice B fix round 2,
// re-review R-M2), so it can show beside a message's or What we know's: dismissing one leaves
// the world still while the other shows.
import { act, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import { SupportShown, useSupportPanels, useSupportShown } from "./settings";

function Panel() {
  useSupportShown();
  return null;
}

let toggle: (name: "first" | "second") => void = () => {};

function Shell() {
  const [still, report] = useSupportPanels();
  const [shown, setShown] = useState({ first: true, second: true });
  toggle = (name) => setShown((current) => ({ ...current, [name]: !current[name] }));
  return (
    <SupportShown.Provider value={report}>
      <p>{still ? "still" : "moving"}</p>
      {shown.first && <Panel />}
      {shown.second && <Panel />}
    </SupportShown.Provider>
  );
}

describe("[WLD-08] the world stays still while any support panel shows", () => {
  it("stays still until the last panel is dismissed", () => {
    render(<Shell />);
    expect(screen.getByText("still")).toBeInTheDocument();

    act(() => toggle("first"));
    expect(screen.getByText("still")).toBeInTheDocument();

    act(() => toggle("second"));
    expect(screen.getByText("moving")).toBeInTheDocument();
  });
});
