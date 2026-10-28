"use client";
// The conversation (spec section 4, S2.3): one useful question at a time, the person's
// choice of entry and tone, pause and resume, and the reply as it streams. A streamed reply
// is marked not checked until the validated turn replaces it; a failed turn says why, keeps
// what streamed marked as not saved, and saves nothing. The support screen has two tiers
// (ADR 0007 decision 7): a first-person statement of acute distress gets the support
// response instead of the interviewer; any other risk word is sent as usual, with a calm
// support note beside it, announced politely and dismissible.
import { useEffect, useId, useRef, useState } from "react";
import type {
  ConversationMode,
  EntryMode,
  PreferencesOut,
  ProfileOut,
  SupportNoteOut,
  SupportResponseOut,
  TurnOut,
  WorkspaceOut,
} from "@/generated/api";
import { replyView, turnFailed, turnRunning } from "@/lib/conversation";
import { type MessageSender, useSetPreferences, useTurnReply } from "@/lib/queries";
import {
  CONVERSATION_MODE,
  ENTRY_MODE,
  FAILED_REPLY_LABEL,
  FAILURE_CLASS,
  OPENING_QUESTION,
  PARTIAL_REPLY,
} from "@/lib/vocabulary";
import { Alert } from "./Alert";
import { Button } from "./Button";
import { Glyph } from "./Glyph";
import { RequestFailure } from "./PageState";

const EARLIER_SHOWN = 2;
const time = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });
const day = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric" });

type Props = {
  workspace: WorkspaceOut;
  profile: ProfileOut;
  preferences: PreferencesOut;
  turns: TurnOut[];
  sender: MessageSender;
  /** Why no message can be sent now (paused, no key, a reply on its way), if so. */
  sendBlocked: string | undefined;
  /** Which action in the chapter is the filled primary one (one per view). */
  primary: string;
  announce(text: string): void;
  onEditAnswers(): void;
};

function Reply({
  workspaceId,
  turn,
  latest,
}: {
  workspaceId: string;
  turn: TurnOut;
  latest: boolean;
}) {
  // Only a running turn, or the latest failed one (to keep what it wrote), needs its partial.
  const failed = turnFailed(turn);
  const partial = useTurnReply(workspaceId, turn.turn_id, turnRunning(turn) || (failed && latest));
  const view = replyView(turn, partial.data);
  if (view.kind === "checked") {
    return (
      <div className="turn-nessa">
        <Glyph name="mark" />
        <p>{view.text}</p>
      </div>
    );
  }
  if (view.kind === "failed") {
    if (latest && view.text === null) return null; // the failure notice below says why
    return (
      <div className="turn-nessa">
        <Glyph name="mark" />
        <div className="reply-provisional grid gap-8">
          <span className="status small" data-tone="error">
            <Glyph name="error" />
            <span>
              {latest
                ? FAILED_REPLY_LABEL
                : `No reply: ${FAILURE_CLASS[view.failure].title}. Nothing was saved.`}
            </span>
          </span>
          {latest && view.text !== null && <p>{view.text}</p>}
        </div>
      </div>
    );
  }
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

/** Beside a sent message that used a risk word (tier 2): calm, not blocking, dismissible.
 *  The message went to Nessa as usual. */
function SupportNote({ note, onDismiss }: { note: SupportNoteOut; onDismiss(): void }) {
  const titleId = useId();
  return (
    <section className="card grid gap-8 small" aria-labelledby={titleId}>
      <h3 id={titleId} className="font-semibold">
        Support is available
      </h3>
      <p>{note.message}</p>
      <ul className="plain-list">
        {note.resources.map((resource) => (
          <li key={resource.name}>
            <strong>{resource.name}:</strong> {resource.contact}. {resource.when}.
          </li>
        ))}
      </ul>
      <div>
        <Button variant="quiet" onClick={onDismiss}>
          Dismiss <span className="sr-only">the support note</span>
        </Button>
      </div>
    </section>
  );
}

function SupportNotice({
  support,
  onSendAnyway,
  blocked,
}: {
  support: SupportResponseOut;
  onSendAnyway(): void;
  blocked: string | undefined;
}) {
  const checked = support.resources[0]?.checked_on;
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
      {checked !== undefined && (
        <p className="muted mt-8">
          These services were checked on their own websites on{" "}
          {day.format(new Date(`${checked}T12:00:00Z`))}. This response is provisional until it is
          reviewed.
        </p>
      )}
      <div className="alert-actions">
        <Button variant="secondary" onClick={onSendAnyway} disabledReason={blocked}>
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
      <p className="muted mt-12 measure">Both lead to the same plan chapters.</p>
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

function repliedWords(turn: TurnOut): string {
  const count = turn.proposal?.changes.length ?? 0;
  if (count === 0) return "Nessa replied.";
  return `Nessa replied: ${count} ${count === 1 ? "change" : "changes"} to review.`;
}

export function Conversation({
  workspace,
  profile,
  preferences,
  turns,
  sender,
  sendBlocked,
  primary,
  announce,
  onEditAnswers,
}: Props) {
  const id = workspace.workspace_id;
  const setPreferences = useSetPreferences(id);
  const [message, setMessage] = useState("");
  const [showEarlier, setShowEarlier] = useState(false);
  const [focusQuestion, setFocusQuestion] = useState(false);
  const questionTitle = useRef<HTMLHeadingElement>(null);
  const replyField = useRef<HTMLTextAreaElement>(null);
  const modeId = useId();
  const demo = workspace.data_mode === "demo";
  const support = sender.support;

  const latest = turns.at(-1);
  const latestFailed = latest !== undefined && turnFailed(latest);
  const answered = [...turns].reverse().find((turn) => turn.proposal !== null);
  const question =
    answered?.proposal?.next_question ??
    (turns.length === 0 && preferences.entry_mode
      ? OPENING_QUESTION[preferences.entry_mode]
      : null);
  const entryNeeded = preferences.entry_mode === null && turns.length === 0;

  // Each new checked reply is announced once; a reply already there on load is not news.
  const announced = useRef<string | null | undefined>(undefined);
  const answeredId = answered?.turn_id ?? null;
  useEffect(() => {
    if (announced.current === undefined) {
      announced.current = answeredId;
      return;
    }
    if (answered !== undefined && answeredId !== announced.current) {
      announced.current = answeredId;
      announce(repliedWords(answered));
    }
  }, [answeredId, answered, announce]);

  // A new support note is announced politely; focus stays where the person is (I-4).
  const note = sender.note;
  const announcedNote = useRef<typeof note>(null);
  useEffect(() => {
    if (note !== null && note !== announcedNote.current) {
      announcedNote.current = note; // once per note, however often the chapter renders
      announce("Your message was sent. Support information is shown above the reply field.");
    }
  }, [note, announce]);

  // After choosing how to start, the first question takes focus (it replaced the choice).
  useEffect(() => {
    if (focusQuestion && questionTitle.current !== null) {
      questionTitle.current.focus();
      setFocusQuestion(false);
    }
  });

  const save = (
    changes: Partial<Pick<PreferencesOut, "entry_mode" | "conversation_mode" | "paused">>,
    onError?: () => void,
  ) =>
    setPreferences.mutate(
      {
        expected_version: preferences.version,
        entry_mode: preferences.entry_mode,
        conversation_mode: preferences.conversation_mode,
        paused: preferences.paused,
        ...changes,
      },
      { onError },
    );

  const send = async (text: string, sendAfterSupport = false) => {
    const sent = await sender.send({
      expected_profile_version: profile.version,
      message: text,
      send_after_support: sendAfterSupport,
    });
    if (sent && text === message.trim()) setMessage("");
  };

  const shown = showEarlier ? turns : turns.slice(-EARLIER_SHOWN);
  const hidden = turns.length - shown.length;

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
          value={preferences.conversation_mode ?? ""}
          onChange={(event) => save({ conversation_mode: event.target.value as ConversationMode })}
        >
          {preferences.conversation_mode === null && (
            <option value="" disabled>
              Choose a tone
            </option>
          )}
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
        <EntryChoice
          preferences={preferences}
          onChoose={(entry) => {
            setFocusQuestion(true);
            // A failed save leaves the choice on screen; focus must not jump later (N-M6).
            save({ entry_mode: entry }, () => setFocusQuestion(false));
          }}
        />
      ) : (
        <>
          {hidden > 0 && (
            <Button variant="quiet" onClick={() => setShowEarlier(true)}>
              Show earlier messages ({hidden})
            </Button>
          )}
          {shown.map((turn) => (
            <div key={turn.turn_id} className="grid gap-16">
              <div className="turn-you" data-processed={!turnFailed(turn)}>
                <p>{turn.message}</p>
                <span className="when">You, {time.format(new Date(turn.created_at))}</span>
              </div>
              <Reply workspaceId={id} turn={turn} latest={turn === latest} />
            </div>
          ))}

          {latestFailed && latest !== undefined && (
            <Alert
              tone={latest.run.status === "provider_unavailable" ? "stale" : "error"}
              title={FAILURE_CLASS[latest.run.failure_class ?? "unknown_failure"].title}
              actions={
                <>
                  <Button
                    variant={primary === "retry" ? "primary" : "secondary"}
                    onClick={() => void send(latest.message)}
                    disabledReason={sendBlocked}
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
                Nothing is asked and nothing can be sent until you resume. Everything you have said
                and saved is kept.
              </p>
            </section>
          ) : (
            question !== null &&
            !latestFailed &&
            support === null && (
              <section className="question" aria-labelledby="question-title">
                <h2 id="question-title" className="display" tabIndex={-1} ref={questionTitle}>
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
          support={support.response}
          blocked={sendBlocked}
          onSendAnyway={() => void send(support.message, true)}
        />
      )}
      {note !== null && (
        <SupportNote
          note={note}
          onDismiss={() => {
            sender.dismissNote();
            replyField.current?.focus(); // the button goes; focus is never lost (M-1)
          }}
        />
      )}
      {sender.error !== null && <RequestFailure error={sender.error} />}

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
            ref={replyField}
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
