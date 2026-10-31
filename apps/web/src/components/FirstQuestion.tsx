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
import type { ClosestOut, ProfileOut, TitleMatchOut, UkTitleOut } from "@/generated/api";
import { useChooseClosest, useChooseRole, useNameRole, useTitleMatches } from "@/lib/queries";
import { CLOSEST, FIRST_ANSWER, FIRST_QUESTION } from "@/lib/vocabulary";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";

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
  onAnswered,
  onSkip,
}: {
  workspaceId: string;
  profile: ProfileOut;
  /** Focus lands here when the question is shown after another step. */
  headingRef?: Ref<HTMLHeadingElement>;
  /** A line above the question (what Careerwright is for). */
  lead?: ReactNode;
  /** The person answered: the start moves on once the answer is saved (a failure stays here,
   *  saying why). */
  onAnswered?(): void;
  /** "Skip for now": the start goes on without an answer (nothing is saved). */
  onSkip(): void;
}) {
  const id = useId();
  const [typed, setTyped] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const settled = useSettled(typed, SETTLE_MS);
  const found = useTitleMatches(settled, OPTIONS_SHOWN);
  const chooseRole = useChooseRole(workspaceId);
  const nameRole = useNameRole(workspaceId);
  const text = typed.trim();
  const body = text !== "" && settled.trim() === text ? found.data : undefined;
  const partial = body?.partial === true;
  const options: Option[] =
    text === ""
      ? []
      : [
          ...(body?.matches ?? []).map(
            (m): Option =>
              m.source === "esco" ? { kind: "esco", match: m } : { kind: "uk", title: m },
          ),
          { kind: "own", text },
        ];
  const shown = open && options.length > 0;
  const at = Math.min(active, Math.max(options.length - 1, 0));
  const saving = chooseRole.isPending || nameRole.isPending;
  const failure = chooseRole.error ?? nameRole.error;

  const pick = (option: Option) => {
    if (saving) return;
    setOpen(false);
    onAnswered?.();
    const expected_version = profile.version;
    if (option.kind === "esco") {
      chooseRole.mutate({
        expected_version,
        concept_id: option.match.concept_id,
        label: option.match.matched_label,
      });
    } else {
      nameRole.mutate({
        expected_version,
        title: option.kind === "uk" ? option.title.title : option.text,
      });
    }
  };

  const keys = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      if (options.length === 0) return;
      const step = event.key === "ArrowDown" ? 1 : -1;
      setActive((at + step + options.length) % options.length);
    } else if (event.key === "Enter") {
      const option = options[at];
      if (shown && option !== undefined) {
        event.preventDefault();
        pick(option);
      }
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  };

  const listId = `${id}-titles`;
  const questionId = `${id}-partial`;
  const optionId = (n: number) => `${id}-option-${n}`;
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
          id={`${id}-field`}
          className="input"
          role="combobox"
          aria-expanded={shown}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={shown ? optionId(at) : undefined}
          autoComplete="off"
          maxLength={120}
          placeholder={FIRST_ANSWER.placeholder}
          value={typed}
          onChange={(event) => {
            setTyped(event.target.value);
            setActive(0);
            setOpen(true);
          }}
          onKeyDown={keys}
          onFocus={() => setOpen(true)}
          // Leaving the field closes the list; a press on an option keeps focus in the field.
          onBlur={() => setOpen(false)}
        />
        {shown && partial && (
          <p id={questionId} className="small">
            {FIRST_ANSWER.partial}
          </p>
        )}
        {shown && body !== undefined && body.matches.length === 0 && (
          <p className="small muted">{FIRST_ANSWER.nothing}</p>
        )}
        {shown && body === undefined && found.isFetching && (
          <p className="small muted" role="status">
            {FIRST_ANSWER.looking}
          </p>
        )}
        <div
          id={listId}
          className="title-options"
          role="listbox"
          aria-label={FIRST_ANSWER.field}
          aria-describedby={partial ? questionId : undefined}
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
              <OptionWords option={option} partial={partial} />
            </div>
          ))}
        </div>
        {found.error !== null && <RequestFailure error={found.error} />}
        {failure !== null && <RequestFailure error={failure} />}
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
}: {
  workspaceId: string;
  profile: ProfileOut;
  title: string;
  closest: ClosestOut;
  headingRef?: Ref<HTMLHeadingElement>;
  /** The person answered: the start moves on once the answer is saved. */
  onAnswered?(): void;
}) {
  const id = useId();
  const choose = useChooseClosest(workspaceId);
  const [more, setMore] = useState<ReadonlySet<string>>(new Set());
  const saving = choose.isPending ? "Saving…" : undefined;
  const answer = (concept_id: string | null) => {
    onAnswered?.();
    choose.mutate({ expected_version: profile.version, concept_id });
  };
  const firstMore = useRef<HTMLButtonElement>(null);
  return (
    <section className="question" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`} className="display" tabIndex={-1} ref={headingRef}>
        {CLOSEST.question}
      </h2>
      <p className="small mt-12 measure">{CLOSEST.found(title, closest.groups.length)}</p>
      <div className="choices">
        <Button variant="choice" onClick={() => answer(null)} disabledReason={saving}>
          {CLOSEST.noneOfThese}
        </Button>
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
                    disabledReason={saving}
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
