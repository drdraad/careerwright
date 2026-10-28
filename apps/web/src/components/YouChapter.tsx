"use client";
// The You chapter (spec sections 3-4, S2.3-S2.5; docs/design/compositions/conversation.html):
// the conversation beside "What we know". It leads with the first task (how to start, then
// one question at a time); the review tray, the answers, the early sketch and the form to
// edit answers directly sit beside it, and directions to explore below it. On narrower
// screens the two columns stack, so "What we know" is always reachable.
//
// One filled primary action per view (docs/design/README.md): the answer form's Save while
// it is open, else connecting a key when none is stored, else Try again after a failed reply,
// else saving the review tray when it has proposals, else Send.
import { useState } from "react";
import type { ProfileDocument, ProfileOut, WorkspaceOut } from "@/generated/api";
import { reviewable } from "@/lib/conversation";
import {
  useCredentials,
  useLatestDiscovery,
  usePreferences,
  useSubmitTurn,
  useTurns,
} from "@/lib/queries";
import { Button } from "./Button";
import { Conversation } from "./Conversation";
import { Directions } from "./Directions";
import { KeySetup } from "./KeySetup";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";
import { ProfileEditor } from "./ProfileEditor";
import { ReviewTray } from "./ReviewTray";
import { SketchCard } from "./SketchCard";
import { type LastSave, WhatWeKnow } from "./WhatWeKnow";

const NO_KEY = "Connect a Meta key first.";

export function YouChapter({
  workspace,
  profile,
}: {
  workspace: WorkspaceOut;
  profile: ProfileOut;
}) {
  const id = workspace.workspace_id;
  const demo = workspace.data_mode === "demo";
  const preferences = usePreferences(id);
  const turns = useTurns(id);
  const credentials = useCredentials(id, !demo);
  const discovery = useLatestDiscovery(id);
  const resend = useSubmitTurn(id);
  const [editing, setEditing] = useState(false);
  const [lastSave, setLastSave] = useState<LastSave | null>(null);
  const [exploring, setExploring] = useState(false);

  const loads = [preferences, turns, discovery, ...(demo ? [] : [credentials])];
  const failed = loads.find((load) => load.data === undefined && load.error);
  if (failed !== undefined) {
    return (
      <>
        <h1 className="page-title">You</h1>
        <RequestFailure
          error={failed.error}
          actions={
            <Button
              variant="secondary"
              onClick={() => void Promise.all(loads.map((load) => load.refetch()))}
            >
              Try again
            </Button>
          }
        />
      </>
    );
  }
  if (
    preferences.data === undefined ||
    turns.data === undefined ||
    discovery.data === undefined ||
    (!demo && credentials.data === undefined)
  ) {
    return (
      <>
        <h1 className="page-title">You</h1>
        <LoadingState stage="Loading the conversation" />
      </>
    );
  }

  const keyStored = demo || (credentials.data ?? []).some((credential) => credential.active);
  const unavailable = keyStored ? undefined : NO_KEY;
  const pending = reviewable(turns.data, profile.version);
  const latest = turns.data.at(-1);
  const latestFailed =
    latest !== undefined &&
    latest.proposal === null &&
    ["failed", "provider_unavailable", "cancelled"].includes(latest.run.status);
  const primary = editing
    ? "edit"
    : !keyStored
      ? "key"
      : latestFailed
        ? "retry"
        : pending !== null && !pending.stale
          ? "review"
          : "send";
  const sure = preferences.data.entry_mode === "sure";
  const saved = (before: ProfileDocument, after: ProfileOut) =>
    setLastSave(after.version !== profile.version ? { before, version: after.version } : null);

  return (
    <>
      <h1 className="page-title">You</h1>
      <div className="you">
        <div className="thread">
          {/* Stacked screens: "What we know" follows the conversation; this says what waits
              there and goes to it, before anything else (S0-V01). */}
          <a className="known-summary" href="#known-title">
            <span>
              <strong>What we know</strong>
              {pending !== null && !pending.stale
                ? `, ${pending.turn.proposal?.changes.length ?? 0} to review`
                : `, version ${profile.version}`}
            </span>
            <span className="btn btn-secondary">Open</span>
          </a>
          {!demo && (
            <KeySetup
              workspace={workspace}
              credentials={credentials.data ?? []}
              primary={primary === "key"}
            />
          )}
          <Conversation
            workspace={workspace}
            profile={profile}
            preferences={preferences.data}
            turns={turns.data}
            unavailable={unavailable}
            primary={primary}
            onEditAnswers={() => setEditing(true)}
          />
          {editing && (
            <div id="edit-answers">
              <ProfileEditor key={id} workspaceId={id} profile={profile} />
            </div>
          )}
        </div>
        <aside className="known" aria-labelledby="known-title">
          <h2 id="known-title" className="display text-25">
            What we know
          </h2>
          {pending !== null && (
            <ReviewTray
              key={pending.turn.turn_id}
              workspaceId={id}
              profile={profile}
              turn={pending.turn}
              stale={pending.stale}
              primary={primary === "review"}
              onResend={(message) =>
                resend.mutate({ expected_profile_version: profile.version, message })
              }
              onSaved={saved}
            />
          )}
          <WhatWeKnow
            workspaceId={id}
            profile={profile}
            lastSave={lastSave}
            onUndone={() => setLastSave(null)}
            editing={editing}
            onEdit={() => setEditing((open) => !open)}
          />
          <SketchCard workspaceId={id} profile={profile} />
        </aside>
        <div className="directions">
          {sure && !exploring ? (
            <p className="small">
              You know your direction, so suggestions are optional.{" "}
              <Button variant="quiet" onClick={() => setExploring(true)}>
                Help me explore instead
              </Button>
            </p>
          ) : (
            preferences.data.entry_mode !== null && (
              <Directions
                workspaceId={id}
                profile={profile}
                discovery={discovery.data}
                unavailable={unavailable}
              />
            )
          )}
        </div>
      </div>
    </>
  );
}
