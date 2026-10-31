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
//
// Task W2E: before the entry choice, one plain line says what Careerwright is for; until the
// first answer, one says Careerwright covers England for now (BND1-02); and the entry choice
// is the bright action, never Send on an empty field (F17).
// Each demo question offers one-tap example replies the demo interviewer reads (STATE-09), and
// the role-or-explore question offers two ways on that open existing views.
import { type ReactNode, type Ref, useEffect, useId, useRef, useState } from "react";
import type { EntryMode, PreferencesOut, ProfileOut, TurnOut, WorkspaceOut } from "@/generated/api";
import {
  asksRoleOrExplore,
  questionAsks,
  replyView,
  turnFailed,
  turnRunning,
} from "@/lib/conversation";
import { type MessageSender, useOrigin, useSetPreferences, useTurnReply } from "@/lib/queries";
import {
  ENGLAND_ONLY,
  ENTRY_MODE,
  EXAMPLE_REPLIES,
  FAILED_REPLY_LABEL,
  FAILURE_CLASS,
  OPENING_QUESTION,
  PARTIAL_REPLY,
  PURPOSE,
  ROLE_KEPT,
  ROLE_OR_EXPLORE,
} from "@/lib/vocabulary";
import { Alert } from "./Alert";
import { Button } from "./Button";
import { ClosestQuestion, FirstQuestion } from "./FirstQuestion";
import { Glyph } from "./Glyph";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";
import { SupportNote } from "./SupportNote";

const EARLIER_SHOWN = 2;
const time = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" });

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
  /** "Show me suggestions": opens the suggestions and asks for some (STATE-09). */
  onShowSuggestions(): void;
  /** "Name a role": opens the answer form at the target roles (STATE-09). */
  onNameRole(): void;
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

function EntryChoice({
  preferences,
  onChoose,
  headingRef,
  lead,
}: {
  preferences: PreferencesOut;
  onChoose(entry: EntryMode): void;
  headingRef?: Ref<HTMLHeadingElement>;
  /** What Careerwright did with the first answer, when there is something to say. */
  lead?: ReactNode;
}) {
  return (
    <section className="question" aria-labelledby="entry-title">
      {/* What Careerwright is for, before the choice (session 2: "not sure" what the start
          page was for). One line, and no helper text beyond it. */}
      <p className="measure mb-12">{PURPOSE}</p>
      {lead}
      <h2 id="entry-title" className="display" tabIndex={-1} ref={headingRef}>
        How would you like to start?
      </h2>
      <div className="choices">
        {/* The two choices name themselves; their glosses were helper text that didn't help
            (session 2: "too much helper text"). Together they are the start's bright action,
            never Send on an empty field (F17). */}
        {(Object.keys(ENTRY_MODE) as EntryMode[]).map((entry) => (
          <Button
            key={entry}
            variant="choice"
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

type StartStep = "first" | "loading" | "closest" | "entry";

/** The start, one decision at a time (plan section 4, "The first ten seconds"; Task 6d slice
 *  B): the first question, then "Which of these is closest?" for a UK job title, then how to
 *  start. The first answer lights the world at once and needs no key; "Skip for now" goes
 *  straight to how to start, saving nothing. "Change my job title" goes back from the closest
 *  question to the first, its title in the field to fix. Focus follows the decision to the next
 *  step, and never moves after a save that failed. */
function Start({
  workspace,
  profile,
  preferences,
  onChoose,
}: {
  workspace: WorkspaceOut;
  profile: ProfileOut;
  preferences: PreferencesOut;
  onChoose(entry: EntryMode): void;
}) {
  const id = workspace.workspace_id;
  const [skipped, setSkipped] = useState(false);
  const [leaving, setLeaving] = useState<StartStep | null>(null);
  // The title the person went back from the closest question to fix, while it is the role.
  const [backFrom, setBackFrom] = useState<string | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const role = profile.document.current_role;
  const answered = role.state === "provided";
  const origin = useOrigin(id, answered);
  const shown = origin.data?.role;
  // The origin answers for the role it was computed from; until it matches, it is loading.
  const current = shown !== undefined && shown.text === role.value ? shown : undefined;
  const fixing = backFrom !== null && backFrom === role.value;
  const step: StartStep =
    (role.state === "unasked" && !skipped) || fixing
      ? "first"
      : !answered || origin.error !== null
        ? "entry"
        : current === undefined
          ? "loading"
          : current.closest?.decision === "not_yet"
            ? "closest"
            : "entry";
  useEffect(() => {
    // A new role (the fixed title, or one saved elsewhere) ends going back.
    if (backFrom !== null && role.value !== backFrom) setBackFrom(null);
  }, [backFrom, role.value]);
  useEffect(() => {
    if (leaving !== null && step !== leaving && step !== "loading" && heading.current) {
      heading.current.focus();
      setLeaving(null);
    }
  });
  // A failed save keeps the step on screen, saying why; focus must not jump later (N-M6).
  const failed = () => setLeaving(null);
  if (step === "first") {
    return (
      <FirstQuestion
        workspaceId={id}
        profile={profile}
        headingRef={heading}
        lead={<p className="measure mb-12">{PURPOSE}</p>}
        initial={fixing ? backFrom : ""}
        onAnswered={() => setLeaving("first")}
        // The same title again changes nothing: back to its closest question.
        onSaved={() => setBackFrom(null)}
        onFailed={failed}
        onSkip={() => {
          setLeaving("first");
          if (fixing) setBackFrom(null);
          else setSkipped(true);
        }}
      />
    );
  }
  if (step === "loading") return <LoadingState stage="Looking at your answer" lines={2} />;
  if (step === "closest" && current?.closest && current.text !== null) {
    const title = current.text;
    return (
      <ClosestQuestion
        workspaceId={id}
        profile={profile}
        title={title}
        closest={current.closest}
        headingRef={heading}
        onAnswered={() => setLeaving("closest")}
        onFailed={failed}
        onBack={() => {
          setLeaving("closest");
          setBackFrom(title);
        }}
      />
    );
  }
  const kept =
    current !== undefined &&
    current.text !== null &&
    current.kind !== null &&
    current.state === "not_in_esco" &&
    (current.closest === null || current.closest.decision === "none_of_these")
      ? ROLE_KEPT[current.kind](current.text)
      : null;
  return (
    <>
      <EntryChoice
        preferences={preferences}
        onChoose={onChoose}
        headingRef={heading}
        lead={kept !== null && <p className="measure mb-12">{kept}</p>}
      />
      {origin.error !== null && (
        <RequestFailure
          error={origin.error}
          actions={
            <Button variant="secondary" onClick={() => void origin.refetch()}>
              Try again
            </Button>
          }
        />
      )}
    </>
  );
}

/** Under a demo question: replies the demo interviewer reads, each sent in one tap. */
function ExampleReplies({
  replies,
  onSend,
}: {
  replies: readonly string[];
  onSend(text: string): void;
}) {
  if (replies.length === 0) return null;
  return (
    <fieldset className="example-replies mt-12">
      <legend className="sr-only">Example replies</legend>
      {replies.map((reply) => (
        <Button key={reply} variant="secondary" onClick={() => onSend(reply)}>
          {reply}
        </Button>
      ))}
    </fieldset>
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
  onShowSuggestions,
  onNameRole,
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
  const asks = questionAsks(answered, preferences.entry_mode);
  const roleOrExplore = asksRoleOrExplore(asks, demo, preferences.entry_mode, profile.document);

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
        <Start
          workspace={workspace}
          profile={profile}
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
                {roleOrExplore ? (
                  // Two ways on that open existing views; neither commits anything (STATE-09).
                  <div className="choices">
                    <Button variant="choice" onClick={onShowSuggestions}>
                      {ROLE_OR_EXPLORE.explore}
                    </Button>
                    <Button variant="choice" onClick={onNameRole}>
                      {ROLE_OR_EXPLORE.name}
                    </Button>
                  </div>
                ) : (
                  demo &&
                  asks !== null &&
                  sendBlocked === undefined && (
                    <ExampleReplies
                      replies={EXAMPLE_REPLIES[asks]}
                      onSend={(text) => {
                        // The examples go while it is sent; focus goes to the reply field,
                        // which stays, never to the page (app review I2).
                        replyField.current?.focus();
                        void send(text);
                      }}
                    />
                  )
                )}
              </section>
            )
          )}
        </>
      )}
      {/* Before detailed collection (BND1-02). */}
      {turns.length === 0 && <p className="small muted">{ENGLAND_ONLY}</p>}
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
          {/* Bright only with something to send: never Send on an empty field (F17). */}
          <Button
            type="submit"
            variant={primary === "send" && message.trim() !== "" ? "primary" : "secondary"}
            disabledReason={sendBlocked}
          >
            Send
          </Button>
        </div>
      </form>

      {(!entryNeeded || demo) && (
        <div className="thread-meta">
          {!entryNeeded && !preferences.paused && (
            // Named for what it pauses; the world's own control is "Hold the world still" (F17).
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
