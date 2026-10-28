"use client";
// The conversation (spec section 4, S2.3): one useful question at a time, the person's
// choice of entry and tone, pause and resume, and the reply as it streams. A streamed reply
// is marked not checked until the validated turn replaces it; a failed turn says why and
// saves nothing. A message that explicitly expresses acute distress gets the support
// response instead of the interviewer (ADR 0007 decision 7).
import { useEffect, useId, useState } from "react";
import type {
  ConversationMode,
  EntryMode,
  PreferencesOut,
  ProfileOut,
  SupportResponseOut,
  TurnOut,
  WorkspaceOut,
} from "@/generated/api";
import { replyView } from "@/lib/conversation";
import { useSetPreferences, useSubmitTurn, useTurnReply } from "@/lib/queries";
import {
  CONVERSATION_MODE,
  ENTRY_MODE,
  FAILURE_CLASS,
  OPENING_QUESTION,
  PARTIAL_REPLY,
} from "@/lib/vocabulary";
import { Alert } from "./Alert";
import { Button } from "./Button";
import { Glyph } from "./Glyph";
import { RequestFailure } from "./PageState";

const EARLIER_SHOWN = 2;
const TERMINAL = new Set(["complete", "failed", "provider_unavailable", "cancelled"]);
const time = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });

type Props = {
  workspace: WorkspaceOut;
  profile: ProfileOut;
  preferences: PreferencesOut;
  turns: TurnOut[];
  /** Why the interviewer can't be reached yet (no key stored), if it can't. */
  unavailable?: string | undefined;
  /** Which action in the chapter is the filled primary one (one per view). */
  primary: string;
  onEditAnswers(): void;
};

function Reply({ workspaceId, turn }: { workspaceId: string; turn: TurnOut }) {
  const live = !TERMINAL.has(turn.run.status) || turn.proposal === null;
  const partial = useTurnReply(workspaceId, turn.turn_id, live);
  const view = replyView(turn, partial.data);
  if (view.kind === "checked") {
    return (
      <div className="turn-nessa">
        <Glyph name="mark" />
        <p>{view.text}</p>
      </div>
    );
  }
  if (view.kind === "failed") return null; // the failure notice below says what happened
  const words =
    view.kind === "waiting" ? PARTIAL_REPLY.none.label : PARTIAL_REPLY[view.completeness].label;
  return (
    <div className="turn-nessa">
      <Glyph name="mark" />
      <div className="reply-provisional grid gap-8">
        <span
          className="status small"
          data-tone={view.kind === "streaming" ? undefined : "unknown"}
        >
          <Glyph name="running" />
          <span>{words}</span>
        </span>
        {view.kind === "streaming" && <p aria-hidden="true">{view.text}</p>}
      </div>
    </div>
  );
}

function SupportNotice({
  support,
  onSendAnyway,
  sending,
}: {
  support: SupportResponseOut;
  onSendAnyway(): void;
  sending: boolean;
}) {
  return (
    <Alert tone="neutral" title="Support is available now" announce>
      <p>{support.message}</p>
      <ul className="plain-list mt-8">
        {support.resources.map((resource) => (
          <li key={resource.name}>
            <strong>{resource.name}:</strong> {resource.contact}. {resource.when}.
          </li>
        ))}
      </ul>
      <p className="muted mt-8">
        These services were checked on their own websites on {support.resources[0]?.checked_on}.
        This response is provisional until it is reviewed.
      </p>
      <div className="alert-actions">
        <Button
          variant="secondary"
          onClick={onSendAnyway}
          disabledReason={sending ? "Sending…" : undefined}
        >
          Send my message to Nessa anyway
        </Button>
      </div>
    </Alert>
  );
}

function EntryChoice({
  preferences,
  onChoose,
}: {
  preferences: PreferencesOut;
  onChoose(entry: EntryMode): void;
}) {
  return (
    <section className="question" aria-labelledby="entry-title">
      <h2 id="entry-title" className="display">
        How would you like to start?
      </h2>
      <p className="muted mt-12 measure">
        You can change this later, and both lead to the same plan chapters.
      </p>
      <div className="choices">
        {(Object.keys(ENTRY_MODE) as EntryMode[]).map((entry) => (
          <Button
            key={entry}
            variant="secondary"
            aria-describedby={`entry-${entry}`}
            aria-pressed={preferences.entry_mode === entry}
            onClick={() => onChoose(entry)}
          >
            {ENTRY_MODE[entry].label}
          </Button>
        ))}
      </div>
      <ul className="plain-list mt-12">
        {(Object.keys(ENTRY_MODE) as EntryMode[]).map((entry) => (
          <li key={entry} id={`entry-${entry}`}>
            {ENTRY_MODE[entry].label}: {ENTRY_MODE[entry].detail}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function Conversation({
  workspace,
  profile,
  preferences,
  turns,
  unavailable,
  primary,
  onEditAnswers,
}: Props) {
  const id = workspace.workspace_id;
  const submit = useSubmitTurn(id);
  const setPreferences = useSetPreferences(id);
  const [message, setMessage] = useState("");
  const [support, setSupport] = useState<SupportResponseOut | null>(null);
  const [showEarlier, setShowEarlier] = useState(false);
  const [announced, setAnnounced] = useState("");
  const modeId = useId();
  const demo = workspace.data_mode === "demo";

  const latest = turns.at(-1);
  const inFlight = latest !== undefined && !TERMINAL.has(latest.run.status);
  const latestFailed =
    latest !== undefined && latest.proposal === null && TERMINAL.has(latest.run.status);
  const question =
    [...turns].reverse().find((turn) => turn.proposal !== null)?.proposal?.next_question ??
    (turns.length === 0 && preferences.entry_mode
      ? OPENING_QUESTION[preferences.entry_mode]
      : null);
  const entryNeeded = preferences.entry_mode === null && turns.length === 0;

  // Announce a checked reply once, not every streamed piece.
  const lastChecked = latest?.proposal?.reply;
  useEffect(() => {
    if (lastChecked) setAnnounced("Nessa replied.");
  }, [lastChecked]);

  const save = (
    changes: Partial<Pick<PreferencesOut, "entry_mode" | "conversation_mode" | "paused">>,
  ) =>
    setPreferences.mutate({
      expected_version: preferences.version,
      entry_mode: preferences.entry_mode,
      conversation_mode: preferences.conversation_mode,
      paused: preferences.paused,
      ...changes,
    });

  const send = async (text: string, sendAfterSupport = false) => {
    const sent = await submit
      .mutateAsync({
        expected_profile_version: profile.version,
        message: text,
        send_after_support: sendAfterSupport,
      })
      .catch(() => null);
    if (sent === null) return;
    if (sent.kind === "support") {
      setSupport(sent.support);
      return;
    }
    setSupport(null);
    setMessage("");
  };

  const shown = showEarlier ? turns : turns.slice(-EARLIER_SHOWN);
  const hidden = turns.length - shown.length;
  const sendBlocked = preferences.paused
    ? "Paused: resume to send."
    : unavailable
      ? unavailable
      : inFlight
        ? "Nessa is still replying."
        : submit.isPending
          ? "Sending…"
          : undefined;

  return (
    <section className="grid gap-24" aria-labelledby="conversation-title">
      <h2 id="conversation-title" className="sr-only">
        Conversation with Nessa
      </h2>
      <div className="thread-meta">
        <label htmlFor={modeId}>How Nessa talks with you</label>
        <select
          id={modeId}
          className="select"
          value={preferences.conversation_mode ?? "practical"}
          onChange={(event) => save({ conversation_mode: event.target.value as ConversationMode })}
        >
          {(Object.keys(CONVERSATION_MODE) as ConversationMode[]).map((mode) => (
            <option key={mode} value={mode}>
              {CONVERSATION_MODE[mode]}
            </option>
          ))}
        </select>
        {!entryNeeded && (
          <Button variant="secondary" onClick={() => save({ paused: !preferences.paused })}>
            {preferences.paused ? "Resume" : "Pause"}
          </Button>
        )}
        {demo && (
          <span className="small">
            Demo interviewer: synthetic answers from fixed patterns, not a model.
          </span>
        )}
      </div>
      {setPreferences.error !== null && <RequestFailure error={setPreferences.error} />}

      {entryNeeded ? (
        <EntryChoice preferences={preferences} onChoose={(entry) => save({ entry_mode: entry })} />
      ) : (
        <>
          {hidden > 0 && (
            <Button variant="quiet" onClick={() => setShowEarlier(true)}>
              Show earlier messages ({hidden})
            </Button>
          )}
          {shown.map((turn) => (
            <div key={turn.turn_id} className="grid gap-16">
              <div
                className="turn-you"
                data-processed={turn.proposal !== null || !TERMINAL.has(turn.run.status)}
              >
                <p>{turn.message}</p>
                <span className="when">You, {time.format(new Date(turn.created_at))}</span>
              </div>
              <Reply workspaceId={id} turn={turn} />
            </div>
          ))}
          <p role="status" className="sr-only">
            {announced}
          </p>

          {latestFailed && latest !== undefined && (
            <Alert
              tone={latest.run.status === "provider_unavailable" ? "stale" : "error"}
              title={FAILURE_CLASS[latest.run.failure_class ?? "unknown_failure"].title}
              actions={
                <>
                  <Button
                    variant={primary === "retry" ? "primary" : "secondary"}
                    onClick={() => void send(latest.message)}
                    disabledReason={unavailable ?? (submit.isPending ? "Sending…" : undefined)}
                  >
                    Try again
                  </Button>
                  <Button variant="secondary" onClick={onEditAnswers}>
                    Add the details yourself
                  </Button>
                </>
              }
            >
              <p>
                {FAILURE_CLASS[latest.run.failure_class ?? "unknown_failure"].action} What we know
                is unchanged at version {profile.version}. Your message is kept above.
              </p>
            </Alert>
          )}

          {preferences.paused ? (
            <section className="question" aria-labelledby="paused-title">
              <h2 id="paused-title" className="display">
                Paused
              </h2>
              <p className="muted mt-12 measure">
                Nothing is asked until you resume. Everything you have said and saved is kept.
              </p>
            </section>
          ) : (
            question !== null &&
            !latestFailed && (
              <section className="question" aria-labelledby="question-title">
                <h2 id="question-title" className="display">
                  {question}
                </h2>
                <p className="muted mt-12 measure">
                  Answer in your own words, or say Skip, Unknown or Prefer not to say.
                </p>
              </section>
            )
          )}
        </>
      )}

      {support !== null && (
        <SupportNotice
          support={support}
          sending={submit.isPending}
          onSendAnyway={() => void send(message, true)}
        />
      )}
      {submit.error !== null && <RequestFailure error={submit.error} />}

      {!entryNeeded && (
        <form
          className="composer"
          aria-label="Your reply"
          onSubmit={(event) => {
            event.preventDefault();
            if (sendBlocked === undefined && message.trim() !== "") void send(message.trim());
          }}
        >
          <label className="sr-only" htmlFor={`${modeId}-reply`}>
            Reply to Nessa
          </label>
          <textarea
            id={`${modeId}-reply`}
            rows={2}
            maxLength={2000}
            placeholder="Reply in your own words"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
          />
          <div className="grid justify-items-end gap-4">
            <Button
              type="submit"
              variant={primary === "send" ? "primary" : "secondary"}
              disabledReason={sendBlocked}
            >
              Send
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}
