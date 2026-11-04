import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { OptionResearchOut } from "@/generated/api";
import { optionEstimate, optionResearch, optionRun } from "@/test/optionResearchData";
import { OptionResearchView } from "./OptionResearchView";

function shown(research: OptionResearchOut | null = null, refused = false) {
  const onStart = vi.fn();
  const onRead = vi.fn();
  const onCancel = vi.fn();
  render(
    <OptionResearchView
      target="Data quality analyst"
      cities={["Leeds", "York"]}
      city="Leeds"
      onCity={vi.fn()}
      keyReady
      canWrite
      estimate={{ ...optionEstimate, refused_scope: refused ? "run" : null }}
      estimateLoading={false}
      estimateError={null}
      research={research}
      researchLoading={false}
      researchError={null}
      starting={false}
      reading={false}
      cancelling={false}
      startError={null}
      readError={null}
      cancelError={null}
      onStart={onStart}
      onRead={onRead}
      onCancel={onCancel}
    />,
  );
  return { onStart, onRead, onCancel };
}

describe("[OPTN-12][MODEL-08] option research view", () => {
  it("shows the combined ceiling before a search and sends only a target and city in its explanation", async () => {
    const { onStart } = shown();
    expect(screen.getByText(/Estimated model spending: up to \$0\.14/)).toBeVisible();
    expect(screen.getByText(/Worker restarts could reach \$0\.25/)).toBeVisible();
    expect(
      screen.getByText(/It sends only this target title and one of your cities/),
    ).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Find options for this role" }));
    expect(onStart).toHaveBeenCalledOnce();
  });

  it("does not state a clipped run limit as the cost when the estimate refuses start", async () => {
    const { onStart } = shown(null, true);
    expect(screen.queryByText(/\$0\.14/)).toBeNull();
    const start = screen.getByRole("button", { name: "Find options for this role" });
    expect(start).toHaveAttribute("aria-disabled", "true");
    await userEvent.click(start);
    expect(onStart).not.toHaveBeenCalled();
  });

  it("shows bounded progress and lets the person stop the active reading run", async () => {
    const reading = optionRun("reading-id", "running", "acquisition");
    const { onCancel } = shown({
      ...optionResearch,
      status: "reading",
      coverage: "partial",
      pages_attempted: 1,
      pages_read: 0,
      pages_blocked: 1,
      reading,
      records: [],
    });
    expect(screen.getByText(/1 attempted; 0 read, 1 blocked/)).toBeVisible();
    expect(screen.getByRole("progressbar")).toHaveValue(1);
    await userEvent.click(screen.getByRole("button", { name: "Stop research" }));
    expect(onCancel).toHaveBeenCalledWith("reading-id");
  });

  it("shows verified records as they arrive while other pages are still being read", () => {
    shown({
      ...optionResearch,
      status: "reading",
      coverage: "partial",
      reading: optionRun("reading-id", "running", "acquisition"),
      pages_attempted: 1,
      pages_read: 1,
    });
    expect(screen.getByText("Evening data course")).toBeVisible();
    expect(screen.getByText(/Not reviewed yet/)).toBeVisible();
    expect(screen.queryByText(/No course or funding details were verified/)).toBeNull();
  });

  it("separates stopped and unread pages from no options, while showing proposed cited records", async () => {
    shown({
      ...optionResearch,
      status: "reading_stopped",
      coverage: "partial",
      pages_blocked: 1,
      pages_failed: 1,
      reading: {
        ...optionRun("reading-id", "failed", "acquisition"),
        failure_class: "retrieval_failed",
      },
    });
    expect(screen.getByText(/The result is incomplete/)).toBeVisible();
    expect(screen.getByText(/Unread pages are not counted as no options/)).toBeVisible();
    expect(screen.queryByText(/vacancies/)).toBeNull();
    const record = screen.getByRole("listitem", { name: "" });
    expect(within(record).getByText("Evening data course")).toBeVisible();
    expect(within(record).getByText(/Not reviewed yet/)).toBeVisible();
    expect(within(record).getByRole("link", { name: "Open source page" })).toHaveAttribute(
      "href",
      "https://college.example/course",
    );
    await userEvent.click(screen.getByText("Words checked on the source page"));
    expect(screen.getByText("“Evening data course”")).toBeVisible();
  });

  it("words a search with no usable pages without claiming no option exists", () => {
    shown({
      ...optionResearch,
      status: "no_pages",
      coverage: "none_read",
      empty_reason: "all_excluded",
      reading: null,
      records: [],
    });
    expect(screen.getByText(/Every proposed page was excluded/)).toBeVisible();
    expect(screen.getByText(/This does not mean there are no options/)).toBeVisible();
    expect(screen.queryByText(/Records added to Options/)).toBeNull();
  });
});
