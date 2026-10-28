"use client";
// The compact strip (spec section 3): active targets, work areas, the current budget and the
// saved state, plus the synthetic label, live-update state and account. Each value is the
// API's own; an unanswered one reads as its state (STATE-08), never as zero.
import * as Popover from "@radix-ui/react-popover";
import Link from "next/link";
import type { ProfileOut, WorkspaceOut } from "@/generated/api";
import type { StreamStatus } from "@/lib/events";
import { describeField } from "@/lib/profile";
import { DATA_MODE } from "@/lib/vocabulary";
import { Glyph } from "./Glyph";
import { SyntheticLabel } from "./Status";

type Props = {
  workspace: WorkspaceOut;
  profile: ProfileOut | undefined;
  /** The profile's first load failed: nothing about it is shown. */
  profileFailed: boolean;
  workspaces: WorkspaceOut[];
  workspacesFailed: boolean;
  events: StreamStatus;
  onReconnect(): void;
  /** A refresh failed after a successful load: what is shown is what was last loaded. */
  refreshFailed: boolean;
  email: string | null;
  calm: boolean;
  onCalmChange(calm: boolean): void;
  onSignOut(): void;
};

function budget(profile: ProfileOut): string {
  const total = profile.document.direct_spend_cap;
  const monthly = profile.document.monthly_payment_cap;
  if (total.state !== "provided" && monthly.state !== "provided") return "Not confirmed";
  const totalText =
    total.state === "provided"
      ? `Up to ${describeField(total)}`
      : `Total ${describeField(total).toLowerCase()}`;
  const monthlyText =
    monthly.state === "provided"
      ? `at most ${describeField(monthly)} a month`
      : `monthly ${describeField(monthly).toLowerCase()}`;
  return `${totalText}, ${monthlyText}`;
}

const EVENTS_TEXT: Record<StreamStatus["state"], string> = {
  connecting: "Connecting",
  live: "Live",
  reconnecting: "Reconnecting",
  stopped: "Stopped",
};

const STOP_REASON: Record<Extract<StreamStatus, { state: "stopped" }>["reason"], string> = {
  signed_out: ": sign in again",
  reauthentication_failed: ": sign in again",
  access_ended: ": access to this workspace ended",
  closed: "",
};

/** Shown on every screen size: on a phone it is the only sign that updates stopped. */
function LiveUpdates({ status, onReconnect }: { status: StreamStatus; onReconnect(): void }) {
  const glyph = status.state === "live" ? "live" : status.state === "stopped" ? "error" : "running";
  const tone = status.state === "stopped" && status.reason !== "closed" ? "error" : "neutral";
  return (
    <span className="flex items-center gap-8">
      <span className="status" data-tone={tone} role="status" aria-live="polite">
        <Glyph name={glyph} />
        {/* Named in words, so it is never read as the state of what the page loaded (V-02). */}
        <span>
          Updates: {EVENTS_TEXT[status.state]}
          {status.state === "stopped" && STOP_REASON[status.reason]}
        </span>
      </span>
      {/* Only a failed re-authentication can be cured by trying again from here; signed out
          needs sign-in, ended access cannot come back, and closed is a normal restart. */}
      {status.state === "stopped" && status.reason === "reauthentication_failed" && (
        <button type="button" className="strip-switch" onClick={onReconnect}>
          Reconnect <span className="sr-only">live updates</span>
        </button>
      )}
    </span>
  );
}

export function WorkspaceStrip({
  workspace,
  profile,
  profileFailed,
  workspaces,
  workspacesFailed,
  events,
  onReconnect,
  refreshFailed,
  email,
  calm,
  onCalmChange,
  onSignOut,
}: Props) {
  return (
    <header className="strip on-space">
      {workspace.synthetic && (
        <span className="strip-optional">
          <SyntheticLabel />
        </span>
      )}
      <Popover.Root>
        <Popover.Trigger className="strip-switch">
          <span className="strip-optional">Workspace</span>
          <strong>{workspace.name}</strong>
          <Glyph name="collapse" />
        </Popover.Trigger>
        <Popover.Content className="popover on-space" align="start" sideOffset={8}>
          <nav aria-label="Workspaces">
            <ul>
              {workspaces.map((item) => (
                <li key={item.workspace_id}>
                  <Link
                    className="menu-chapter"
                    href={`/w/${item.workspace_id}/you`}
                    aria-current={item.workspace_id === workspace.workspace_id ? "page" : undefined}
                  >
                    {item.name}
                    <span className="small muted">{DATA_MODE[item.data_mode]}</span>
                  </Link>
                </li>
              ))}
              <li>
                <Link className="menu-chapter" href="/">
                  All workspaces
                </Link>
              </li>
            </ul>
            {workspacesFailed && (
              <p className="small px-12 py-8" role="alert">
                Your other workspaces couldn't be loaded.
              </p>
            )}
          </nav>
        </Popover.Content>
      </Popover.Root>
      {profile !== undefined && (
        <>
          <span className="strip-item">
            Target <strong>{describeField(profile.document.target_titles)}</strong>
          </span>
          <span className="strip-item strip-optional">
            Work area <strong>{describeField(profile.document.cities)}</strong>
          </span>
          <span className="strip-item strip-optional">
            Budget <strong className="tnum">{budget(profile)}</strong>
          </span>
        </>
      )}
      <span className="strip-end flex flex-wrap items-center gap-16">
        {profileFailed && profile === undefined ? (
          // Not announced: the chapter announces this failure with its cause.
          <span className="status" data-tone="error">
            <Glyph name="unavailable" />
            <span>Your answers couldn't be loaded</span>
          </span>
        ) : (
          <span className="strip-item">
            {profile === undefined
              ? "Loading"
              : profile.version === 0
                ? "Nothing saved yet"
                : `Saved, version ${profile.version}`}
          </span>
        )}
        {refreshFailed && (
          <span className="status" data-tone="error" role="alert">
            <Glyph name="unavailable" />
            <span>Couldn't refresh: showing what was last loaded</span>
          </span>
        )}
        <span className="strip-item">
          <LiveUpdates status={events} onReconnect={onReconnect} />
        </span>
        <Popover.Root>
          <Popover.Trigger className="strip-switch" aria-label="Account and settings">
            <Glyph name="menu" />
          </Popover.Trigger>
          <Popover.Content className="popover on-space grid gap-8" align="end" sideOffset={8}>
            <p className="small">
              Signed in as <strong>{email ?? "an emulator account"}</strong>
            </p>
            <p className="small muted">{DATA_MODE[workspace.data_mode]} workspace</p>
            <label className="flex items-center gap-8 small">
              <input
                type="checkbox"
                checked={calm}
                onChange={(event) => onCalmChange(event.target.checked)}
              />
              Calm mode: no motion
            </label>
            <button type="button" className="btn btn-secondary" onClick={onSignOut}>
              <Glyph name="signOut" />
              Sign out
            </button>
          </Popover.Content>
        </Popover.Root>
      </span>
    </header>
  );
}
