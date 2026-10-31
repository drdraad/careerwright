"use client";
// The conversation (spec section 4, S2.3): one useful question at a time, the person's
// choice of entry, pause and resume, and the reply as it streams. Chat is immediate (session
// 2): the reply field is there from the first screen, and the entry choice is the first
// question's two quick answers; how Careerwright talks with you is a preference in the account
// menu (`ConversationTone`). A streamed reply is marked not checked until the validated turn
// replaces it; a failed turn says why, keeps what streamed marked as not saved, and saves
// nothing. What the reply proposes (`review`) is decided right after it, and the next question
// waits until it is decided: one decision at a time (plan section 4). While the interview is
// paused, Resume is the view's one primary action, where the question was. A message with a risk
// stem is sent as usual, and the API's calm support panel is shown beside it, or beside its
// refusal if the send is refused (ADR 0007 decision 7): announced politely, focus left where
// it is, dismissible, and the question steps aside while it is shown (no career question that
// turn).
import { type ReactNode, useEffect, useId, useRef, useState } from "react";
import type {
  EntryMode,
  PreferencesOut,
  ProfileOut,
  SupportNoteOut,
  TurnOut,
  WorkspaceOut,
} from "@/generated/api";
import { replyView, turnFailed, turnRunning } from "@/lib/conversation";
import { type MessageSender, useSetPreferences, useTurnReply } from "@/lib/queries";
import {
  ENTRY_MODE,
  FAILED_REPLY_LABEL,
  FAILURE_CLASS,
  OPENING_QUESTION,
  PARTIAL_REPLY,
} from "@/lib/vocabulary";
import { useSupportShown } from "@/lib/world/settings";
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
  /** What the latest reply proposes, or what the last decision on it did: right after it. */
  review?: ReactNode;
  /** Quiet things at the end of the view (the stored key's details). */
  after?: ReactNode;
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
      <div className="turn-careerwright">
        <Glyph name="mark" />
        <p>{view.text}</p>
      </div>
    );
  }
  if (view.kind === "failed") {
    if (latest && view.text === null) return null; // the failure notice below says why
    return (
      <div className="turn-careerwright">
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
    <div className="turn-careerwright">
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

/** Beside a sent message that holds a risk stem: calm, not blocking, dismissible. The
 *  message went to Careerwright as usual. */
function SupportNote({ note, onDismiss }: { note: SupportNoteOut; onDismiss(): void }) {
  // While it shows, the world is still (plan section 4: distress stills the world).
  useSupportShown();
  const titleId = useId();
  const checked = note.resources[0]?.checked_on;
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
      {checked !== undefined && (
        <p className="muted">
          These services were checked on their own websites on{" "}
          {day.format(new Date(`${checked}T12:00:00Z`))}.
        </p>
      )}
      <div>
        <Button variant="quiet" onClick={onDismiss}>
          Dismiss <span className="sr-only">the support note</span>
        </Button>
      </div>
    </section>
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
      <div className="choices">
        {/* The two choices name themselves; their glosses were helper text that didn't help
            (session 2: "too much helper text"). */}
        {(Object.keys(ENTRY_MODE) as EntryMode[]).map((entry) => (
          <Button
            key={entry}
            variant="secondary"
            aria-pressed={preferences.entry_mode === entry}
            onClick={() => onChoose(entry)}
          >
            {ENTRY_MODE[entry]}
          </Button>
        ))}
      </div>
    </section>
  );
}

function repliedWords(turn: TurnOut): string {
  const count = turn.proposal?.changes.length ?? 0;
  if (count === 0) return "Careerwright replied.";
  return `Careerwright replied: ${count} ${count === 1 ? "change" : "changes"} to review.`;
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
  review,
  after,
}: Props) {
  const id = workspace.workspace_id;
  const setPreferences = useSetPreferences(id);
  const [message, setMessage] = useState("");
  const [showEarlier, setShowEarlier] = useState(false);
  const [focusTo, setFocusTo] = useState<"question" | "paused" | "resumed" | null>(null);
  const questionTitle = useRef<HTMLHeadingElement>(null);
  const pausedTitle = useRef<HTMLHeadingElement>(null);
  const replyField = useRef<HTMLTextAreaElement>(null);
  const modeId = useId();
  const demo = workspace.data_mode === "demo";
  const support = sender.support;
  const note = support?.note ?? null;

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
  const announcedNote = useRef<typeof support>(null);
  useEffect(() => {
    if (support !== null && support !== announcedNote.current) {
      announcedNote.current = support; // once per note, however often the chapter renders
      announce(
        `Your message was ${support.sent ? "sent" : "not sent"}. Support information is shown ` +
          "above the reply field.",
      );
    }
  }, [support, announce]);

  // The control just used is replaced, so focus moves to what replaced it once it is there:
  // after choosing how to start, the first question; after pausing, "Paused"; after resuming,
  // the question, or the reply field while no question is shown.
  useEffect(() => {
    const target =
      focusTo === "question"
        ? questionTitle.current
        : focusTo === "paused"
          ? pausedTitle.current
          : focusTo === "resumed" && !preferences.paused
            ? (questionTitle.current ?? replyField.current)
            : null;
    if (target !== null) {
      target.focus();
      setFocusTo(null);
    }
  });

  const save = (
    changes: Partial<Pick<PreferencesOut, "entry_mode" | "paused">>,
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

  const send = async (text: string) => {
    const sent = await sender.send({ expected_profile_version: profile.version, message: text });
    if (sent && text === message.trim()) setMessage("");
  };

  const shown = showEarlier ? turns : turns.slice(-EARLIER_SHOWN);
  const hidden = turns.length - shown.length;

  return (
    <section className="thread" aria-labelledby="conversation-title">
      <h2 id="conversation-title" className="sr-only">
        Conversation with Careerwright
      </h2>

      {entryNeeded ? (
        <EntryChoice
          preferences={preferences}
          onChoose={(entry) => {
            setFocusTo("question");
            // A failed save leaves the choice on screen; focus must not jump later (N-M6).
            save({ entry_mode: entry }, () => setFocusTo(null));
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
                is unchanged. Your message is kept above.
              </p>
            </Alert>
          )}

          {review}

          {preferences.paused ? (
            <section className="question" aria-labelledby="paused-title">
              <h2 id="paused-title" className="display" tabIndex={-1} ref={pausedTitle}>
                Paused
              </h2>
              <p className="muted mt-12 measure">
                Nothing is asked and nothing can be sent until you resume. Everything you have said
                and saved is kept.
              </p>
              <div className="mt-16">
                <Button
                  variant={primary === "resume" ? "primary" : "secondary"}
                  onClick={() => {
                    setFocusTo("resumed");
                    save({ paused: false }, () => setFocusTo(null));
                  }}
                >
                  Resume the interview
                </Button>
              </div>
            </section>
          ) : (
            question !== null &&
            !latestFailed &&
            note === null &&
            // A reply's proposals are one decision; the next question waits until it is made.
            primary !== "review" && (
              <section className="question" aria-labelledby="question-title">
                <h2 id="question-title" className="display" tabIndex={-1} ref={questionTitle}>
                  {question}
                </h2>
                {/* Said once, at the start, not under every question (session 2: "too much
                    helper text"). */}
                {turns.length === 0 && (
                  <p className="muted mt-12 measure">
                    Answer in your own words, or say Skip, Unknown or Prefer not to say.
                  </p>
                )}
              </section>
            )
          )}
        </>
      )}
      {/* Saving the entry choice or a pause failed: said where the choice was made. */}
      {setPreferences.error !== null && <RequestFailure error={setPreferences.error} />}

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

      <form
        className="composer"
        aria-label="Your reply"
        onSubmit={(event) => {
          event.preventDefault();
          if (sendBlocked === undefined && message.trim() !== "") void send(message.trim());
        }}
      >
        <label className="sr-only" htmlFor={`${modeId}-reply`}>
          Reply to Careerwright
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

      {(!entryNeeded || demo) && (
        <div className="thread-meta">
          {!entryNeeded && !preferences.paused && (
            // Named for what it pauses: the world's "Pause motion" is on the same screen.
            <Button
              variant="quiet"
              onClick={() => {
                setFocusTo("paused");
                save({ paused: true }, () => setFocusTo(null));
              }}
            >
              Pause the interview
            </Button>
          )}
          {demo && (
            <span>Demo interviewer: synthetic answers from fixed patterns, not a model.</span>
          )}
        </div>
      )}
      {after}
    </section>
  );
}
