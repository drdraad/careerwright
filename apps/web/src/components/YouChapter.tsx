"use client";
// The You chapter (spec sections 3-4, S2.3-S2.5; plan section 4, Sprint W SW.4): the origin's
// console, a glass panel beside the person's light, with session 2's findings applied as the
// product owner recorded them. One idea per view ("need minimum ideas per page"): the
// conversation first, then what we know and the suggestions, each a view of its own ("The
// suggested jobs should ... be on a separate tab"). Chat is immediate: the reply field is
// there from the first screen. How Careerwright talks with you is a preference in the account
// menu ("this should be in preferences"). Each view has one bright primary action ("Needs to be
// a bright colour"); accept and undo are colour coded ("could be easier with colour coded
// buttons"); the limits say what they mean ("what do these mean??").
//
// The conversation's one filled primary action: connecting a key when none is stored, else
// Resume while the interview is paused, else Try again after a failed reply, else saving the
// review tray when it has proposals, else Send. What we know has one while its answer form is
// open (Save changes), and the suggestions while asking for them or choosing one
// (`Directions`).
//
// The three views stay mounted, the inactive ones hidden, so moving between them never loses
// what the person typed or chose: a reply, the tray's choices, the answer form's edits, the
// slate's view controls (Task W2C fix round 1).
//
// Screen readers hear what changed (UI-06): each new checked reply, a save and an undo, in one
// live region that stays mounted; after a decision or an undo, focus moves to the notice that
// says what it did, in the view the person is in. "Add the details yourself" opens the answer
// form in What we know and moves focus to its heading. Moving between views keeps focus on the
// view's tab.
import { type KeyboardEvent, type ReactNode, useEffect, useRef, useState } from "react";
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
import { SaveNotice, type SaveOutcome, WhatWeKnow } from "./WhatWeKnow";

const NO_KEY = "Connect a Meta key first.";

export type YouView = "conversation" | "known" | "suggestions";

const VIEWS: readonly { id: YouView; label: string }[] = [
  { id: "conversation", label: "Conversation" },
  { id: "known", label: "What we know" },
  { id: "suggestions", label: "Suggestions" },
];

const ANNOUNCED: Record<SaveOutcome["kind"], string> = {
  saved: "Saved to What we know.",
  kept_none: "Nothing was saved.",
  undone: "Save undone: your answers are back as they were before it.",
};

/** The chapter's views as tabs: arrow keys, Home and End move between them (ARIA tabs). */
function ViewTabs({ view, onChange }: { view: YouView; onChange(next: YouView): void }) {
  const tabs = useRef(new Map<YouView, HTMLButtonElement>());
  const move = (event: KeyboardEvent<HTMLDivElement>) => {
    const at = VIEWS.findIndex((v) => v.id === view);
    const to =
      event.key === "ArrowRight"
        ? (at + 1) % VIEWS.length
        : event.key === "ArrowLeft"
          ? (at - 1 + VIEWS.length) % VIEWS.length
          : event.key === "Home"
            ? 0
            : event.key === "End"
              ? VIEWS.length - 1
              : null;
    if (to === null) return;
    event.preventDefault();
    const next = VIEWS[to]?.id ?? view;
    onChange(next);
    tabs.current.get(next)?.focus();
  };
  return (
    <div className="you-views" role="tablist" aria-label="You" onKeyDown={move}>
      {VIEWS.map(({ id, label }) => (
        <button
          key={id}
          ref={(element) => {
            if (element) tabs.current.set(id, element);
          }}
          type="button"
          role="tab"
          id={`you-tab-${id}`}
          aria-selected={view === id}
          aria-controls={`you-view-${id}`}
          tabIndex={view === id ? 0 : -1}
          className="you-tab"
          onClick={() => onChange(id)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

export function YouChapter({
  workspace,
  profile,
  initialView = "conversation",
}: {
  workspace: WorkspaceOut;
  profile: ProfileOut;
  /** Where the chapter opens (stories and tests); a person always starts in the conversation. */
  initialView?: YouView;
}) {
  const id = workspace.workspace_id;
  const demo = workspace.data_mode === "demo";
  const preferences = usePreferences(id);
  const setPreferences = useSetPreferences(id);
  const turns = useTurns(id);
  const credentials = useCredentials(id, !demo);
  const discovery = useLatestDiscovery(id);
  const sender = useSendMessage(id);
  const [view, setView] = useState<YouView>(initialView);
  const [editing, setEditing] = useState(false);
  // The last decision's outcome, with how many turns there were when it was made.
  const [outcome, setOutcome] = useState<{ value: SaveOutcome; turns: number } | null>(null);
  const [announcement, setAnnouncement] = useState("");
  // Where focus goes once it is in the page: the notice in the view the person is in, or the
  // answer form's heading.
  const [focusTo, setFocusTo] = useState<"notice" | "form" | null>(null);
  // Both views that show the save notice have their own copy, each with its own heading.
  const conversationNotice = useRef<HTMLHeadingElement>(null);
  const knownNotice = useRef<HTMLHeadingElement>(null);
  const formTitle = useRef<HTMLHeadingElement>(null);

  // A repeated announcement still changes the region's text, so it is read again.
  const announce = (text: string) =>
    setAnnouncement((current) => (current === text ? `${text} ` : text));
  const decided = (next: SaveOutcome) => {
    setOutcome({ value: next, turns: turns.data?.length ?? 0 });
    announce(ANNOUNCED[next.kind]);
    setFocusTo("notice");
  };

  // The notice mounts with the outcome, the form when it opens; focus moves once it is there.
  useEffect(() => {
    if (focusTo === null) return;
    const target =
      focusTo === "form"
        ? formTitle.current
        : (view === "known" ? knownNotice : conversationNotice).current;
    if (target !== null) {
      target.focus();
      setFocusTo(null);
    }
  });

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
        ? "Careerwright is still replying."
        : sender.pending
          ? "Sending…"
          : undefined));
  const primary = !keyStored
    ? "key"
    : preferences.data.paused
      ? "resume"
      : latestFailed
        ? "retry"
        : pending !== null && !pending.stale
          ? "review"
          : "send";
  const current = preferences.data;
  const sure = current.entry_mode === "sure";
  const edit = () => {
    setView("known");
    setEditing(true);
    setFocusTo("form");
  };

  // A save stays undoable until something newer is saved; "nothing saved" and "undone" are
  // said once, until the next message.
  const shownOutcome =
    outcome !== null && (outcome.value.kind === "saved" || outcome.turns === turns.data.length)
      ? outcome.value
      : null;
  const saveNotice = (headingRef: typeof conversationNotice) => (
    <SaveNotice
      workspaceId={id}
      profile={profile}
      outcome={shownOutcome}
      headingRef={headingRef}
      onUndone={(restored) => decided({ kind: "undone", version: restored.version })}
    />
  );
  // Every view stays mounted; only the one shown is visible.
  const panel = (of: YouView, body: ReactNode) => (
    <div
      className="you-view"
      role="tabpanel"
      id={`you-view-${of}`}
      aria-labelledby={`you-tab-${of}`}
      hidden={view !== of}
    >
      {body}
    </div>
  );
  const tray = pending !== null && (
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
      onSaved={(after) =>
        decided(
          after.version !== profile.version
            ? { kind: "saved", version: after.version }
            : { kind: "kept_none" },
        )
      }
    />
  );

  return (
    <>
      <h1 className="page-title">You</h1>
      <p role="status" className="sr-only" data-testid="you-announcer">
        {announcement}
      </p>
      <ViewTabs view={view} onChange={setView} />
      {panel(
        "conversation",
        <>
          {!demo && !keyStored && (
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
            onEditAnswers={edit}
            review={
              <>
                {saveNotice(conversationNotice)}
                {tray}
              </>
            }
            after={
              !demo &&
              keyStored && (
                <KeySetup
                  workspace={workspace}
                  credentials={credentials.data ?? []}
                  primary={false}
                />
              )
            }
          />
        </>,
      )}
      {panel(
        "known",
        <section className="known" aria-labelledby="known-title">
          <h2 id="known-title" className="display text-25">
            What we know
          </h2>
          {saveNotice(knownNotice)}
          <WhatWeKnow
            profile={profile}
            editing={editing}
            onEdit={() => setEditing((open) => !open)}
          />
          {editing && (
            <div id="edit-answers">
              <ProfileEditor key={id} workspaceId={id} profile={profile} headingRef={formTitle} />
            </div>
          )}
          {/* A second idea (a route sketch for the target), so one step away (D-M6). */}
          <details className="details">
            <summary>The early sketch for your target</summary>
            <div className="mt-12">
              <SketchCard workspaceId={id} profile={profile} />
            </div>
          </details>
        </section>,
      )}
      {panel(
        "suggestions",
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
            <Directions
              workspaceId={id}
              profile={profile}
              discovery={discovery.data}
              unavailable={unavailable}
              shown={view === "suggestions"}
            />
          )}
          {setPreferences.error !== null && <RequestFailure error={setPreferences.error} />}
        </div>,
      )}
    </>
  );
}
