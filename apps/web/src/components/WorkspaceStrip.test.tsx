import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ProfileOut, WorkspaceOut } from "@/generated/api";
import type { StreamStatus } from "@/lib/events";
import { WorkspaceStrip } from "./WorkspaceStrip";

const workspace: WorkspaceOut = {
  workspace_id: "w1",
  name: "P01 demo (synthetic)",
  data_mode: "demo",
  synthetic: true,
  fixture: true,
  version: 1,
  last_event_seq: 3,
  created_at: "2027-01-01T00:00:00Z",
  updated_at: "2027-01-01T00:00:00Z",
};

type Overrides = Partial<{
  profile: ProfileOut | undefined;
  profileFailed: boolean;
  refreshFailed: boolean;
  workspacesFailed: boolean;
  events: StreamStatus;
  onReconnect: () => void;
}>;

function strip(overrides: Overrides = {}) {
  render(
    <WorkspaceStrip
      workspace={workspace}
      profile={overrides.profile}
      profileFailed={overrides.profileFailed ?? false}
      workspaces={[workspace]}
      workspacesFailed={overrides.workspacesFailed ?? false}
      events={overrides.events ?? { state: "live" }}
      onReconnect={overrides.onReconnect ?? (() => {})}
      refreshFailed={overrides.refreshFailed ?? false}
      email="ada@careerwright.test"
      onSignOut={() => {}}
    />,
  );
  return userEvent.setup();
}

describe("[STATE-07][UI-09] the strip states what it has, including what failed to load", () => {
  it("says the profile could not be loaded, not 'Loading' or 'showing what was last loaded'", () => {
    strip({ profileFailed: true });

    expect(screen.getByText("Your answers couldn't be loaded")).toBeInTheDocument();
    // Live updates that work say nothing (Task W2C, plain words); the region stays to be heard.
    expect(screen.getByRole("status")).toHaveTextContent(/^$/);
    expect(screen.queryByText("Loading")).not.toBeInTheDocument();
    expect(screen.queryByText(/showing what was last loaded/)).not.toBeInTheDocument();
    // The chapter announces the failure with its cause; the strip does not announce it again.
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it.each([
    ["access_ended", "Stopped: access to this workspace ended"],
    ["closed", "Stopped"],
    ["signed_out", "Stopped: sign in again"],
  ] as const)("offers no Reconnect where it cannot help (%s)", (reason, words) => {
    strip({ events: { state: "stopped", reason } });

    expect(screen.getByRole("status")).toHaveTextContent(`Updates: ${words}`);
    expect(screen.queryByRole("button", { name: /Reconnect/ })).not.toBeInTheDocument();
  });

  it("offers to reconnect when live updates stopped, on every screen size", async () => {
    const onReconnect = vi.fn();
    const user = strip({
      events: { state: "stopped", reason: "reauthentication_failed" },
      onReconnect,
    });

    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("Updates: Stopped: sign in again");
    expect(status.closest(".strip-optional")).toBeNull();
    await user.click(screen.getByRole("button", { name: "Reconnect live updates" }));
    expect(onReconnect).toHaveBeenCalledOnce();
  });

  it("[UI-09] says what is saved in plain words, never a version number", () => {
    // W2A design review M2: "Saved, version 3" and "Updates: Live" were internal-sounding.
    const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
    const saved = (version: number): ProfileOut => ({
      workspace_id: "w1",
      version,
      created_by: null,
      created_at: "2027-01-01T00:00:00Z",
      document: {
        schema_version: "4",
        work_status: unasked,
        qualifications: unasked,
        preferred_name: unasked,
        current_role: unasked,
        cities: unasked,
        target_titles: unasked,
        weekly_study_hours: unasked,
        direct_spend_cap: unasked,
        monthly_payment_cap: unasked,
        enjoyed_tasks: unasked,
        confident_tasks: unasked,
        evidenced_tasks: unasked,
        work_style: unasked,
        minimum_salary: unasked,
      },
    });
    strip({ profile: saved(3), events: { state: "reconnecting", attempt: 1, delayMs: 1000 } });

    expect(screen.getByText("Answers saved")).toHaveAttribute("data-version", "3");
    expect(screen.getByRole("banner")).not.toHaveTextContent(/version/i);
    // Not live: the state names itself (V-02), as an announced status.
    expect(screen.getByRole("status")).toHaveTextContent("Updates: Reconnecting");
    expect(screen.getByRole("banner")).toHaveAttribute("data-events", "reconnecting");
    expect(screen.getByText("Synthetic demo")).toBeInTheDocument();

    cleanup();
    strip({ profile: saved(0) });
    expect(screen.getByText("Nothing saved yet")).toHaveAttribute("data-version", "0");
  });

  it("says so when the list of workspaces could not be loaded", async () => {
    const user = strip({ workspacesFailed: true });
    await user.click(screen.getByRole("button", { name: /Workspace/ }));

    expect(screen.getByText("Your other workspaces couldn't be loaded.")).toBeInTheDocument();
  });
});
