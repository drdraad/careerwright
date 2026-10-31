import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChapterRail } from "./ChapterNav";

describe("[UI-09] the rail marks each chapter as current, visited, not started or not built yet", () => {
  it("names the mark of every chapter, not only the current one", () => {
    render(<ChapterRail workspaceId="w1" current="you" progress={{ you: "visited" }} />);
    const rail = within(screen.getByRole("navigation", { name: "Chapters" }));

    expect(rail.getByRole("link", { name: "You" })).toHaveAttribute("aria-current", "page");
    expect(rail.getAllByRole("link")).toHaveLength(6);
  });

  it("marks every chapter not built yet in sight, before it is clicked (the audit's F2)", () => {
    render(<ChapterRail workspaceId="w1" current="roles" progress={{ you: "visited" }} />);
    const rail = within(screen.getByRole("navigation", { name: "Chapters" }));

    expect(rail.getByRole("link", { name: "You, visited" })).toHaveAttribute(
      "data-progress",
      "visited",
    );
    for (const chapter of ["Skills", "Options", "Routes", "Plan"]) {
      const link = rail.getByRole("link", { name: `${chapter}, not built yet, not started` });
      // Said in sight, not only to assistive tech.
      expect(within(link).getByText("not built yet")).toBeVisible();
    }
    expect(rail.getByRole("link", { name: "Roles, not built yet" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(rail.queryByText("not built yet", { selector: "a[href$='/you'] *" })).toBeNull();
  });
});
