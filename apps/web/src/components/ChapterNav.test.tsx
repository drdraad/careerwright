import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChapterRail } from "./ChapterNav";

describe("[UI-09] the rail marks each chapter as current, visited or not started", () => {
  it("names the mark of every chapter, not only the current one", () => {
    render(<ChapterRail workspaceId="w1" current="roles" progress={{ you: "visited" }} />);
    const rail = within(screen.getByRole("navigation", { name: "Chapters" }));

    expect(rail.getByRole("link", { name: "You, visited" })).toHaveAttribute(
      "data-progress",
      "visited",
    );
    expect(rail.getByRole("link", { name: "Roles" })).toHaveAttribute("aria-current", "page");
    expect(rail.getByRole("link", { name: "Skills, not started" })).toHaveAttribute(
      "data-progress",
      "todo",
    );
    expect(rail.getAllByRole("link")).toHaveLength(6);
  });
});
