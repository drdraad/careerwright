"use client";
// The first question and "Which of these is closest?" (Task 6d slice B; S2.8; plan section 4,
// "The first ten seconds"; ADR 0015). As the person types, job titles come from the pinned ESCO
// release and the pinned UK job-title index (ONS's SOC 2020 coding index), with no model call,
// so it works without a key and in the demo; a title the index lists is marked "UK job title
// (ONS)". "Use my own words" is always the last option and keeps the title exactly as typed:
// nothing typed is refused. Where neither list holds every word typed, the options are ESCO's
// closest titles, asked as the card's question, and "None of these is my job" keeps the
// person's own words. The answer lights the person's light in the world at once (any answer
// does), and a UK title is followed by "Which of these is closest?": the ESCO occupations in
// every group ONS codes it to, none picked, and "None of these is my job", which leaves the
// role with no ESCO occupation and never asks for another.
//
// The field is an ARIA combobox: the arrow keys move through the options, Enter picks the one
// in focus, Escape closes the list; each option is also picked by a click or a tap.
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
  | { kind: "own"; text: string };

function optionKey(option: Option): string {
  return option.kind === "esco"
    ? `esco:${option.match.concept_id}`
    : option.kind === "uk"
      ? `uk:${option.title.title}`
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
  // partial match they didn't choose is never saved (design review I-1).
  const [active, setActive] = useState(-1);
  // The calm panel, from the type-ahead's screen or a refused save; kept until dismissed.
  const [support, setSupport] = useState<SupportNoteOut | null>(null);
  const settled = useSettled(typed, SETTLE_MS);
  const found = useTitleMatches(settled, OPTIONS_SHOWN);
  const chooseRole = useChooseRole(workspaceId);
  const nameRole = useNameRole(workspaceId);
  const text = typed.trim();
  // Only the answer for these very words: an earlier search's never stands for new text.
  const body = text !== "" && settled.trim() === text ? found.data : undefined;
  const screened = body?.support_note ?? null;
  useEffect(() => {
    if (screened !== null) setSupport(screened);
  }, [screened]);
  const partial = body?.partial === true;
  const titles: Option[] = (body?.matches ?? []).map((m) =>
    m.source === "esco" ? { kind: "esco", match: m } : { kind: "uk", title: m },
  );
  // Words the support screen answered are offered nothing, and never repeated back.
  const options: Option[] =
    text === "" || screened !== null ? [] : [...titles, { kind: "own", text }];
  const shown = open && options.length > 0;
  const at = active < options.length ? active : -1;
  const looking =
    text !== "" && body === undefined && (settled.trim() !== text || found.isFetching);
  const saving = chooseRole.isPending || nameRole.isPending;
  const failure = chooseRole.error ?? nameRole.error;
  const settle = {
    onSuccess: () => onSaved?.(),
    onError: (error: Error) => {
      if (error instanceof ApiError && error.supportNote !== null) setSupport(error.supportNote);
      onFailed?.();
    },
  };

  const pick = (option: Option, refused: boolean) => {
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
    nameRole.mutate({ expected_version, title, ...(refused && { none_of_these: true }) }, settle);
  };
  const chosen = (option: Option) => pick(option, option.kind === "own" && partial);

  const keys = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      if (options.length === 0) return;
      const down = event.key === "ArrowDown";
      const from = at === -1 ? (down ? -1 : 0) : at;
      setActive((from + (down ? 1 : -1) + options.length) % options.length);
    } else if (event.key === "Enter") {
      event.preventDefault();
      const option = shown && at !== -1 ? options[at] : undefined;
      if (option !== undefined) chosen(option);
      // Nothing chosen: Enter keeps the words as typed (never a refusal they didn't make).
      else if (text !== "" && screened === null) pick({ kind: "own", text }, false);
    } else if (event.key === "Escape") {
      setOpen(false);
      setActive(-1);
    }
  };

  const listId = `${id}-titles`;
  const questionId = `${id}-partial`;
  const optionId = (n: number) => `${id}-option-${n}`;
  const answered = shown && body !== undefined;
  return (
    <section className="question" aria-labelledby={`${id}-title`}>
      {lead}
      <h2 id={`${id}-title`} className="display" tabIndex={-1} ref={headingRef}>
        {FIRST_QUESTION}
      </h2>
      <div className="title-field">
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
            setActive(-1);
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
              onClick={() => chosen(option)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  chosen(option);
                }
              }}
            >
              <OptionWords option={option} partial={partial} />
            </div>
          ))}
        </div>
        {found.error !== null && <RequestFailure error={found.error} />}
        {failure !== null && support === null && <RequestFailure error={failure} />}
        {support !== null && (
          <SupportNote
            note={support}
            onDismiss={() => {
              setSupport(null);
              field.current?.focus(); // the button goes; focus is never lost
            }}
          />
        )}
      </div>
      <div className="mt-12">
        <Button variant="quiet" onClick={onSkip} disabledReason={saving ? "Saving…" : undefined}>
          {FIRST_ANSWER.skip}
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

function OptionWords({ option, partial }: { option: Option; partial: boolean }) {
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
  return partial ? (
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
