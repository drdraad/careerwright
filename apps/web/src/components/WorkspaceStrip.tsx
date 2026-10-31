"use client";
// The compact strip (spec section 3): active targets, work areas, the current budget and the
// saved state, plus the synthetic label, the world's controls and account. Each value is the
// API's own; an unanswered one reads as its state (STATE-08), never as zero. In plain words
// (Task W2C): the saved state says whether answers are saved, never a version number, and live
// updates say nothing while they work; when they don't, the strip says so (an announced
// status). Settings such as calm mode and how Careerwright talks with you live in the account
// menu, never on the first screen (plan section 4). The synthetic label shows at every width.
// A tablet's strip is two rows: the synthetic label, the target, the work area and the budget
// (each ending in an ellipsis if it must: the person's facts come first, the audit's F14), then
// the states and the account menu; below a desktop's width the world's controls are in the
// account menu (`menu`), beside calm mode. On a phone the strip keeps the saved state, any update
// state and the account menu (which also leads to the workspaces), on one row while updates
// connect or reconnect; a stopped state and a failed refresh take a row of their own, so their
// words are read whole: the top bar carries the chapter and the synthetic label, and the world
// names the target.
import * as Popover from "@radix-ui/react-popover";
import Link from "next/link";
import type { ReactNode } from "react";
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
  /** The world's visible controls on a desktop: holding it still and sound. */
  controls?: ReactNode;
  /** Why the world is still, while the calm support panel shows (on a phone, the top bar's). */
  status?: ReactNode;
  /** Settings shown in the account menu (how Careerwright talks with you, calm mode, and
   *  below a desktop's width the world's controls). */
  settings?: ReactNode;
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

const EVENTS_TEXT: Record<Exclude<StreamStatus["state"], "live">, string> = {
  connecting: "Connecting",
  reconnecting: "Reconnecting",
  stopped: "Stopped",
};

const STOP_REASON: Record<Extract<StreamStatus, { state: "stopped" }>["reason"], string> = {
  signed_out: ": sign in again",
  reauthentication_failed: ": sign in again",
  access_ended: ": access to this workspace ended",
  closed: "",
};

/**
 * Shown on every screen size when updates aren't live: on a phone it is the only sign that
 * they stopped. While they are live it says nothing (the region stays, so a change is heard).
 */
function LiveUpdates({ status, onReconnect }: { status: StreamStatus; onReconnect(): void }) {
  const live = status.state === "live";
  const glyph = status.state === "stopped" ? "error" : "running";
  const tone = status.state === "stopped" && status.reason !== "closed" ? "error" : "neutral";
  return (
    <span
      className={live ? "sr-only" : "strip-item strip-updates flex items-center gap-8"}
      data-state={status.state}
    >
      <span className="status" data-tone={tone} role="status" aria-live="polite">
        {/* Named in words, so it is never read as the state of what the page loaded (V-02). */}
        {!live && (
          <>
            <Glyph name={glyph} />
            <span>
              Updates: {EVENTS_TEXT[status.state]}
              {status.state === "stopped" && STOP_REASON[status.reason]}
            </span>
          </>
        )}
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
  controls,
  status,
  settings,
  onSignOut,
}: Props) {
  return (
    // `data-events` and `data-version` hold the update state and the saved version for tests;
    // the words say them plainly.
    <header className="strip on-space" data-covers-world data-events={events.state}>
      {workspace.synthetic && (
        <span className="strip-optional">
          <SyntheticLabel />
        </span>
      )}
      <Popover.Root>
        {/* Wide screens only: the account menu names the workspace and leads to the others. */}
        <Popover.Trigger className="strip-switch strip-wide">
          <span className="strip-optional">Workspace</span>
          <strong>{workspace.name}</strong>
          <Glyph name="collapse" />
        </Popover.Trigger>
        {/* Menus open through a portal, so they stand over everything, the key included. */}
        <Popover.Portal>
          <Popover.Content className="popover on-space" align="start" sideOffset={8}>
            <nav aria-label="Workspaces">
              <ul>
                {workspaces.map((item) => (
                  <li key={item.workspace_id}>
                    <Link
                      className="menu-chapter"
                      href={`/w/${item.workspace_id}/you`}
                      aria-current={
                        item.workspace_id === workspace.workspace_id ? "page" : undefined
                      }
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
        </Popover.Portal>
      </Popover.Root>
      {profile !== undefined && (
        <>
          <span className="strip-item strip-optional strip-target">
            Target <strong>{describeField(profile.document.target_titles)}</strong>
          </span>
          <span className="strip-item strip-optional strip-fact">
            Work area <strong>{describeField(profile.document.cities)}</strong>
          </span>
          <span className="strip-item strip-optional strip-fact">
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
          <span className="strip-item" data-version={profile?.version}>
            {profile === undefined
              ? "Loading"
              : profile.version === 0
                ? "Nothing saved yet"
                : "Answers saved"}
          </span>
        )}
        {refreshFailed && (
          <span className="status strip-refresh-failed" data-tone="error" role="alert">
            <Glyph name="unavailable" />
            <span>Couldn't refresh: showing what was last loaded</span>
          </span>
        )}
        <LiveUpdates status={events} onReconnect={onReconnect} />
        {status}
        {controls}
        <Popover.Root>
          <Popover.Trigger className="strip-switch" aria-label="Account and settings">
            <Glyph name="menu" />
          </Popover.Trigger>
          <Popover.Portal>
            <Popover.Content className="popover on-space grid gap-8" align="end" sideOffset={8}>
              <p className="small">
                Signed in as <strong>{email ?? "an emulator account"}</strong>
              </p>
              <p className="small muted">
                {workspace.name}: {DATA_MODE[workspace.data_mode].toLowerCase()} workspace
              </p>
              <Link className="menu-chapter" href="/">
                All workspaces
              </Link>
              {settings}
              <button type="button" className="btn btn-secondary" onClick={onSignOut}>
                <Glyph name="signOut" />
                Sign out
              </button>
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>
      </span>
    </header>
  );
}
