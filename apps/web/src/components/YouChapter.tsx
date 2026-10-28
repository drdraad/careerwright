"use client";
// The You chapter (spec sections 3-4, S2.3-S2.5; docs/design/compositions/conversation.html):
// the conversation beside "What we know". It leads with the first task (how to start, then
// one question at a time); the review tray, the answers, the early sketch and the form to
// edit answers directly sit beside it, and directions to explore below it. On narrower
// screens the two columns stack, so "What we know" is always reachable.
//
// One filled primary action per view (docs/design/README.md): the answer form's Save while
// it is open, else connecting a key when none is stored, else Try again after a failed reply,
// else saving the review tray when it has proposals, else Send. The entry choice has none:
// its two choices are equal.
//
// Screen readers hear what changed (UI-06): each new checked reply, a save and an undo, in
// one live region that stays mounted; after a save or an undo focus moves to "What we know".
import { useRef, useState } from "react";
import type { ProfileOut, WorkspaceOut } from "@/generated/api";
import { reviewable, turnFailed, turnRunning } from "@/lib/conversation";
import {
  useCredentials,
  useLatestDiscovery,
  usePreferences,
  useSendMessage,
  useSetPreferences,
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
  const setPreferences = useSetPreferences(id);
  const turns = useTurns(id);
  const credentials = useCredentials(id, !demo);
  const discovery = useLatestDiscovery(id);
  const sender = useSendMessage(id);
  const [editing, setEditing] = useState(false);
  const [lastSave, setLastSave] = useState<LastSave | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const knownTitle = useRef<HTMLHeadingElement>(null);

  // A repeated announcement still changes the region's text, so it is read again.
  const announce = (text: string) =>
    setAnnouncement((current) => (current === text ? `${text} ` : text));
  const settle = (text: string) => {
    announce(text);
    knownTitle.current?.focus();
  };

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
  const latestFailed = latest !== undefined && turnFailed(latest);
  // Every way of sending a message says why it can't (never disabled silently).
  const sendBlocked = preferences.data.paused
    ? "Paused: resume to send."
    : (unavailable ??
      (latest !== undefined && turnRunning(latest)
        ? "Nessa is still replying."
        : sender.pending
          ? "Sending…"
          : undefined));
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
  const current = preferences.data;

  return (
    <>
      <h1 className="page-title">You</h1>
      <p role="status" className="sr-only" data-testid="you-announcer">
        {announcement}
      </p>
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
            preferences={current}
            turns={turns.data}
            sender={sender}
            sendBlocked={sendBlocked}
            primary={primary}
            announce={announce}
            onEditAnswers={() => setEditing(true)}
          />
          {editing && (
            <div id="edit-answers">
              <ProfileEditor key={id} workspaceId={id} profile={profile} />
            </div>
          )}
        </div>
        <aside className="known" aria-labelledby="known-title">
          <h2 id="known-title" className="display text-25" tabIndex={-1} ref={knownTitle}>
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
              resendBlocked={sendBlocked}
              onResend={(message) =>
                void sender.send({ expected_profile_version: profile.version, message })
              }
              onSaved={(after) => {
                if (after.version !== profile.version) setLastSave({ version: after.version });
                settle(
                  after.version !== profile.version
                    ? `Saved as version ${after.version}.`
                    : "Nothing was saved.",
                );
              }}
            />
          )}
          <WhatWeKnow
            workspaceId={id}
            profile={profile}
            lastSave={lastSave}
            onUndone={(restored) => {
              setLastSave(null);
              settle(`Undone: version ${restored.version} has your answers from before the save.`);
            }}
            editing={editing}
            onEdit={() => setEditing((open) => !open)}
          />
          <SketchCard workspaceId={id} profile={profile} />
        </aside>
        <div className="directions">
          {sure ? (
            <p className="small">
              You know your direction, so suggestions are optional.{" "}
              <Button
                variant="quiet"
                onClick={() =>
                  setPreferences.mutate({
                    expected_version: current.version,
                    entry_mode: "unsure",
                    conversation_mode: current.conversation_mode,
                    paused: current.paused,
                  })
                }
                disabledReason={setPreferences.isPending ? "Saving…" : undefined}
              >
                Help me explore instead
              </Button>
            </p>
          ) : (
            current.entry_mode !== null && (
              <Directions
                workspaceId={id}
                profile={profile}
                discovery={discovery.data}
                unavailable={unavailable}
              />
            )
          )}
          {setPreferences.error !== null && <RequestFailure error={setPreferences.error} />}
        </div>
      </div>
    </>
  );
}
