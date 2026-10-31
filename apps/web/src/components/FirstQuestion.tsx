"use client";
// The first question and "Which of these is closest?" (Task 6d slice B; S2.8; plan section 4,
// "The first ten seconds"; ADR 0015). As the person types, job titles come from the pinned ESCO
// release and the pinned UK job-title index (ONS's SOC 2020 coding index), with no model call,
// so it works without a key and in the demo; a title the index lists is marked "UK job title
// (ONS)". "Use my own words" is always the first option, in a phone's first screen however
// many titles follow, and keeps the title exactly as typed: nothing typed is refused. Where
// neither list holds every word typed, the options are ESCO's closest titles, asked as the
// card's question, and "None of these is my job" keeps the person's own words. The answer
// lights the person's light in the world at once (any answer does), and a UK title is followed
// by "Which of these is closest?": the ESCO occupations in every group ONS codes it to, none
// picked, and "None of these is my job", which leaves the role with no ESCO occupation and
// never asks for another.
//
// What is typed goes through the support screen: the calm panel shows above the field, where
// a phone's keyboard can't cover it, and the words are kept as the job title only by the
// person's choice in the panel. The start holds the panel until the person dismisses it.
//
// The field is an ARIA combobox: the arrow keys move through the options, Enter picks the one
// in focus, Escape closes the list; each option is also picked by a click or a tap. The option
// in focus is kept by its key, so one that moves as the titles arrive is never Enter's pick.
import {
  type KeyboardEvent,
  type ReactNode,
  type Ref,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import type {
  ClosestOut,
  ProfileOut,
  SupportNoteOut,
  TitleMatchOut,
  UkTitleOut,
} from "@/generated/api";
import { ApiError } from "@/lib/api";
import { useChooseClosest, useChooseRole, useNameRole, useTitleMatches } from "@/lib/queries";
import { CLOSEST, FIRST_ANSWER, FIRST_QUESTION } from "@/lib/vocabulary";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";
import { SupportNote } from "./SupportNote";

/** The titles offered at once: a short list keeps the decision in the first screen. */
const OPTIONS_SHOWN = 8;
/** Typing settles for this long before the titles are looked up (the lookup takes ~50 ms). */
const SETTLE_MS = 120;
/** The occupations shown per group before "Show more" (ESCO's largest group holds 91). */
const GROUP_SHOWN = 12;

type Option =
  | { kind: "esco"; match: TitleMatchOut }
  | { kind: "uk"; title: UkTitleOut }
  /** The words as typed; under a partial list, "None of these is my job": a refusal too. */
  | { kind: "own"; text: string; noneOfThese: boolean };

function optionKey(option: Option): string {
  return option.kind === "esco"
    ? `esco:${option.match.concept_id}`
    : option.kind === "uk"
      ? `uk:${option.title.title}`
      : // A refusal is another answer, so the own words arrowed to never become one.
        option.noneOfThese
        ? "none-of-these"
        : "own";
}

/** Settles `value` once it has stopped changing for `ms`. */
function useSettled(value: string, ms: number): string {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), ms);
    return () => clearTimeout(timer);
  }, [value, ms]);
  return settled;
}

export function FirstQuestion({
  workspaceId,
  profile,
  headingRef,
  lead,
  initial = "",
  support,
  onSupport,
  onDismissSupport,
  skipLabel = FIRST_ANSWER.skip,
  onAnswered,
  onSaved,
  onFailed,
  onSkip,
}: {
  workspaceId: string;
  profile: ProfileOut;
  /** Focus lands here when the question is shown after another step. */
  headingRef?: Ref<HTMLHeadingElement>;
  /** A line above the question (what Careerwright is for). */
  lead?: ReactNode;
  /** The words in the field to start with: the title the person came back to fix. */
  initial?: string;
  /** The calm support panel, held by the start until the person dismisses it, so it stays
   *  after a skip or another answer, as the message panel does (re-review R-M2). */
  support: SupportNoteOut | null;
  /** The support screen answered what was typed (the type-ahead or a refused save). */
  onSupport(note: SupportNoteOut): void;
  onDismissSupport(): void;
  /** The skip button's words: "Skip for now", or what it does while fixing a title. */
  skipLabel?: string;
  /** The person answered: the start moves on once the answer is saved. */
  onAnswered?(): void;
  /** The answer was saved (it may have changed nothing: the same title again). */
  onSaved?(): void;
  /** Saving the answer failed: the question stays, saying why (or with the support panel). */
  onFailed?(): void;
  /** "Skip for now": the start goes on without an answer (nothing is saved). */
  onSkip(): void;
}) {
  const id = useId();
  const field = useRef<HTMLInputElement>(null);
  const [typed, setTyped] = useState(initial);
  const [open, setOpen] = useState(false);
  // No option is active until the person moves to one, so Enter keeps their own words: a
  // partial match they didn't choose is never saved (design review I-1). The option is kept
  // by its key, never its place, so one that moves as titles arrive is not picked (R-M1).
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const settled = useSettled(typed, SETTLE_MS);
  const found = useTitleMatches(settled, OPTIONS_SHOWN);
  const chooseRole = useChooseRole(workspaceId);
  const nameRole = useNameRole(workspaceId);
  const text = typed.trim();
  // Only the answer for these very words: an earlier search's never stands for new text.
  const body = text !== "" && settled.trim() === text ? found.data : undefined;
  const screened = body?.support_note ?? null;
  useEffect(() => {
    if (screened !== null) onSupport(screened);
  }, [screened, onSupport]);
  const partial = body?.partial === true;
  const titles: Option[] = (body?.matches ?? []).map((m) =>
    m.source === "esco" ? { kind: "esco", match: m } : { kind: "uk", title: m },
  );
  // Words the support screen answered are offered nothing, and never repeated back. The
  // person's own words come first, in a phone's first screen (design re-review R-I2).
  const options: Option[] =
    text === "" || screened !== null
      ? []
      : [{ kind: "own", text, noneOfThese: partial }, ...titles];
  const shown = open && options.length > 0;
  const at = activeKey === null ? -1 : options.findIndex((o) => optionKey(o) === activeKey);
  const looking =
    text !== "" && body === undefined && (settled.trim() !== text || found.isFetching);
  const saving = chooseRole.isPending || nameRole.isPending;
  const failure = chooseRole.error ?? nameRole.error;
  // The support screen's own refusal is answered by the panel alone; any other says why.
  const calm =
    failure instanceof ApiError &&
    failure.supportNote !== null &&
    failure.body?.details?.reason === "support_screen";
  // The words the screen answered, while they are in the field: the person may keep them.
  const refusedWords =
    nameRole.error instanceof ApiError && nameRole.error.supportNote !== null
      ? nameRole.variables?.title
      : undefined;
  const keepable = text !== "" && (screened !== null || refusedWords === text);
  const settle = {
    onSuccess: () => onSaved?.(),
    onError: (error: Error) => {
      if (error instanceof ApiError && error.supportNote !== null) onSupport(error.supportNote);
      onFailed?.();
    },
  };

  const pick = (option: Option, keep = false) => {
    if (saving) return;
    setOpen(false);
    onAnswered?.();
    const expected_version = profile.version;
    if (option.kind === "esco") {
      chooseRole.mutate(
        {
          expected_version,
          concept_id: option.match.concept_id,
          label: option.match.matched_label,
        },
        settle,
      );
      return;
    }
    const title = option.kind === "uk" ? option.title.title : option.text;
    // Under a partial list the own-words option is "None of these is my job": the person's
    // refusal of ESCO's closest titles, recorded so nothing later asks for another job.
    // Words the support screen answered are kept only by the person's choice (`keep`).
    const refused = option.kind === "own" && option.noneOfThese;
    nameRole.mutate(
      {
        expected_version,
        title,
        ...(refused && { none_of_these: true }),
        ...(keep && { keep_as_typed: true }),
      },
      settle,
    );
  };

  const keys = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      if (options.length === 0) return;
      const down = event.key === "ArrowDown";
      const from = at === -1 ? (down ? -1 : 0) : at;
      const next = options[(from + (down ? 1 : -1) + options.length) % options.length];
      if (next !== undefined) setActiveKey(optionKey(next));
    } else if (event.key === "Enter") {
      event.preventDefault();
      const option = shown && at !== -1 ? options[at] : undefined;
      if (option !== undefined) pick(option);
      // Nothing chosen: Enter keeps the words as typed (never a refusal they didn't make).
      else if (text !== "" && screened === null) pick({ kind: "own", text, noneOfThese: false });
    } else if (event.key === "Escape") {
      setOpen(false);
      setActiveKey(null);
    }
  };

  const listId = `${id}-titles`;
  const questionId = `${id}-partial`;
  const optionId = (n: number) => `${id}-option-${n}`;
  const answered = shown && body !== undefined;
  // The person's explicit choice to keep the words the screen answered (re-review R-M3).
  const keep = keepable && (
    <Button
      variant="secondary"
      onClick={() => pick({ kind: "own", text, noneOfThese: false }, true)}
      disabledReason={saving ? "Saving…" : undefined}
    >
      {FIRST_ANSWER.keep}
    </Button>
  );
  return (
    <section className="question" aria-labelledby={`${id}-title`}>
      {lead}
      <h2 id={`${id}-title`} className="display" tabIndex={-1} ref={headingRef}>
        {FIRST_QUESTION}
      </h2>
      <div className="title-field">
        {/* Above the field, as the message panel sits above the reply field: below it, a
            phone's keyboard would cover it while the person types (design re-review R-I1). */}
        {support !== null && (
          <SupportNote
            note={support}
            onDismiss={() => {
              onDismissSupport();
              field.current?.focus(); // the button goes; focus is never lost
            }}
            actions={keep}
          />
        )}
        <label className="sr-only" htmlFor={`${id}-field`}>
          {FIRST_ANSWER.field}
        </label>
        <input
          ref={field}
          id={`${id}-field`}
          className="input"
          role="combobox"
          aria-expanded={shown}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={shown && at !== -1 ? optionId(at) : undefined}
          // The partial question describes the field itself, which is where focus stays.
          aria-describedby={shown && partial ? questionId : undefined}
          autoComplete="off"
          maxLength={120}
          placeholder={FIRST_ANSWER.placeholder}
          value={typed}
          onChange={(event) => {
            setTyped(event.target.value);
            setActiveKey(null);
            setOpen(true);
          }}
          onKeyDown={keys}
          onFocus={() => setOpen(true)}
          // Leaving the field closes the list; a press on an option keeps focus in the field.
          onBlur={() => setOpen(false)}
        />
        {/* One polite status region (WCAG 2.2 4.1.3): the partial question, none found, the
            count, looking, and that the support panel is shown. */}
        <div role="status">
          {shown && partial && (
            <p id={questionId} className="small">
              {FIRST_ANSWER.partial}
            </p>
          )}
          {shown && looking && <p className="small muted">{FIRST_ANSWER.looking}</p>}
          {answered && titles.length === 0 && <p className="small muted">{FIRST_ANSWER.nothing}</p>}
          {answered && titles.length > 0 && (
            <p className="sr-only">{FIRST_ANSWER.count(titles.length)}</p>
          )}
          {support !== null && <p className="sr-only">{FIRST_ANSWER.supportShown}</p>}
        </div>
        <div
          id={listId}
          className="title-options"
          role="listbox"
          aria-label={FIRST_ANSWER.field}
          hidden={!shown}
        >
          {options.map((option, n) => (
            <div
              key={optionKey(option)}
              id={optionId(n)}
              className="title-option"
              role="option"
              tabIndex={-1}
              aria-selected={n === at}
              // A press picks before the field's blur can close the list.
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => pick(option)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  pick(option);
                }
              }}
            >
              <OptionWords option={option} />
            </div>
          ))}
        </div>
        {/* Dismissed, the panel leaves the choice with the words, under the field. */}
        {support === null && keep && <div>{keep}</div>}
        {found.error !== null && <RequestFailure error={found.error} />}
        {/* The support screen's own refusal shows the panel, never a failure notice. */}
        {failure !== null && !calm && <RequestFailure error={failure} />}
      </div>
      <div className="mt-12">
        <Button variant="quiet" onClick={onSkip} disabledReason={saving ? "Saving…" : undefined}>
          {skipLabel}
        </Button>
      </div>
    </section>
  );
}

/** A title's second line, read after a pause ("Registered nurse, UK job title (ONS)"). */
function Mark({ children }: { children: ReactNode }) {
  return (
    <span className="mark">
      <span className="sr-only">, </span>
      {children}
    </span>
  );
}

function OptionWords({ option }: { option: Option }) {
  if (option.kind === "esco") {
    const { matched_label, title } = option.match;
    return (
      <>
        <span>{matched_label}</span>
        {matched_label !== title && <Mark>{FIRST_ANSWER.escoTitle(title)}</Mark>}
      </>
    );
  }
  if (option.kind === "uk") {
    return (
      <>
        <span>{option.title.title}</span>
        <Mark>{FIRST_ANSWER.ukTitle}</Mark>
      </>
    );
  }
  return option.noneOfThese ? (
    <>
      <span>{FIRST_ANSWER.noneOfThese}</span>
      <Mark>{FIRST_ANSWER.ownWords(option.text)}</Mark>
    </>
  ) : (
    <span>{FIRST_ANSWER.ownWords(option.text)}</span>
  );
}

/** "Which of these is closest?" for the role just named: every group ONS codes its title to,
 *  each with its ESCO occupations, none picked, and "None of these is my job". */
export function ClosestQuestion({
  workspaceId,
  profile,
  title,
  closest,
  headingRef,
  onAnswered,
  onFailed,
  onBack,
}: {
  workspaceId: string;
  profile: ProfileOut;
  title: string;
  closest: ClosestOut;
  headingRef?: Ref<HTMLHeadingElement>;
  /** The person answered: the start moves on once the answer is saved. */
  onAnswered?(): void;
  /** Saving the answer failed: the question stays, saying why. */
  onFailed?(): void;
  /** "Change my job title": back to the first question, to fix a wrongly picked title. */
  onBack?(): void;
}) {
  const id = useId();
  const choose = useChooseClosest(workspaceId);
  const [more, setMore] = useState<ReadonlySet<string>>(new Set());
  // The answer being saved (null: "None of these is my job"): only its button says Saving…,
  // and no other answer is sent until it is done (design review M-8).
  const [choosing, setChoosing] = useState<string | null>(null);
  const saving = (concept_id: string | null) =>
    choose.isPending && choosing === concept_id ? "Saving…" : undefined;
  const answer = (concept_id: string | null) => {
    if (choose.isPending) return;
    setChoosing(concept_id);
    onAnswered?.();
    choose.mutate(
      { expected_version: profile.version, concept_id },
      { onError: () => onFailed?.() },
    );
  };
  const firstMore = useRef<HTMLButtonElement>(null);
  return (
    <section className="question" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`} className="display" tabIndex={-1} ref={headingRef}>
        {CLOSEST.question}
      </h2>
      <p className="small mt-12 measure">{CLOSEST.found(title, closest.groups.length)}</p>
      <div className="choices">
        <Button variant="choice" onClick={() => answer(null)} disabledReason={saving(null)}>
          {CLOSEST.noneOfThese}
        </Button>
        {onBack !== undefined && (
          <Button variant="quiet" onClick={onBack}>
            {CLOSEST.back}
          </Button>
        )}
      </div>
      {closest.groups.map(({ group, occupations }) => {
        const all = more.has(group.code);
        const listed = all ? occupations : occupations.slice(0, GROUP_SHOWN);
        return (
          <section
            key={group.code}
            className="closest-group"
            aria-labelledby={`${id}-${group.code}`}
          >
            <h3 id={`${id}-${group.code}`} className="section-title">
              {CLOSEST.group(group)}
            </h3>
            {occupations.length === 0 ? (
              <p className="small muted">{CLOSEST.empty}</p>
            ) : (
              <div className="flex flex-wrap gap-8">
                {listed.map((occupation, n) => (
                  <Button
                    key={occupation.concept_id}
                    ref={n === GROUP_SHOWN ? firstMore : undefined}
                    variant="secondary"
                    onClick={() => answer(occupation.concept_id)}
                    disabledReason={saving(occupation.concept_id)}
                  >
                    {occupation.title}
                  </Button>
                ))}
                {!all && occupations.length > GROUP_SHOWN && (
                  <Button
                    variant="quiet"
                    onClick={() => {
                      setMore((open) => new Set([...open, group.code]));
                      // The button goes; focus moves to the first occupation it showed.
                      setTimeout(() => firstMore.current?.focus(), 0);
                    }}
                  >
                    {CLOSEST.more(occupations.length - GROUP_SHOWN)}
                  </Button>
                )}
              </div>
            )}
          </section>
        );
      })}
      {choose.error !== null && <RequestFailure error={choose.error} />}
    </section>
  );
}
