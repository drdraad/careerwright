import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChapterRail } from "./ChapterNav";

describe("chapter navigation", () => {
  it("shows saved progress and keeps unavailable destinations out of the links", () => {
    render(
      <ChapterRail
        workspaceId="w1"
        current="you"
        progress={{
          you: "complete",
          roles: "available",
          skills: "available",
          options: "available",
          routes: "locked",
          plan: "locked",
        }}
      />,
    );
    const rail = within(screen.getByRole("navigation", { name: "Chapters" }));
    expect(rail.getByRole("link", { name: "You, direction chosen" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(rail.getByRole("link", { name: "Roles, available" })).toBeVisible();
    expect(rail.getAllByText("Locked")[0]?.closest("[data-progress]")).toHaveAttribute(
      "aria-disabled",
      "true",
    );
    expect(rail.queryByRole("link", { name: "Plan, locked" })).toBeNull();
  });

  it("names a found route without claiming the whole journey is finished", () => {
    render(
      <ChapterRail
        workspaceId="w1"
        current="routes"
        progress={{ routes: "complete", plan: "available" }}
      />,
    );
    expect(screen.getByRole("link", { name: "Routes, route found" })).toBeVisible();
  });
});
