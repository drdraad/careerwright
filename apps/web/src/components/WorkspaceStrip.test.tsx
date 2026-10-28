import { render, screen } from "@testing-library/react";
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
      email="ada@nessa.test"
      calm={false}
      onCalmChange={() => {}}
      onSignOut={() => {}}
    />,
  );
  return userEvent.setup();
}

describe("[STATE-07][UI-09] the strip states what it has, including what failed to load", () => {
  it("says the profile could not be loaded, not 'Loading' or 'showing what was last loaded'", () => {
    strip({ profileFailed: true });

    expect(screen.getByText("Your answers couldn't be loaded")).toBeInTheDocument();
    // V-02: the live-update state names itself, so it never reads as the profile's state.
    expect(screen.getByRole("status")).toHaveTextContent(/^Updates: Live$/);
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

  it("says so when the list of workspaces could not be loaded", async () => {
    const user = strip({ workspacesFailed: true });
    await user.click(screen.getByRole("button", { name: /Workspace/ }));

    expect(screen.getByText("Your other workspaces couldn't be loaded.")).toBeInTheDocument();
  });
});
