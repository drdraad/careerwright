"use client";
// The missing-fact line with its box (Task 12b, OPTN-13; shared with Routes): one fact the route
// search lacks for an option, named plainly, and one place to type the person's own figure for
// it, labelled as theirs and not checked. A start may instead be one of the intake months the
// page states. The parent saves the figure through the planning inputs' command; this box only
// reads what was typed, exactly, or says why it can't.
import { type FormEvent, type ReactNode, useId, useState } from "react";
import type { StartBasis } from "@/generated/api";
import { formatMonth } from "@/lib/dates";
import { type Figure, type FigureFact, readFigure } from "@/lib/figures";
import { MISSING_FACT, suppliedLabel } from "@/lib/optionWords";
import { Button } from "./Button";
import { FieldError } from "./fields";
import { Glyph } from "./Glyph";

const ANOTHER_DAY = "another";

type Props = {
  fact: FigureFact;
  /** The intake months the page states (a start only): chosen, they need no typing. */
  statedIntakes?: readonly string[];
  /** The view's one bright action. */
  primary: boolean;
  saving: boolean;
  current?: Figure;
  /** The save's failure, worded by the parent (a refusal names its reason). */
  failure?: ReactNode;
  onSave(figure: Figure): void;
};

const capitalised = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

export function MissingFactBox({
  fact,
  statedIntakes = [],
  primary,
  saving,
  current,
  failure,
  onSave,
}: Props) {
  const id = useId();
  const [typed, setTyped] = useState(() => {
    if (!current) return "";
    if (current.fact === "start_date" || current.fact === "finish_date") return current.on;
    if (current.fact === "weekly_hours") return String(current.hours);
    return (current.money.minor_units / 100).toFixed(2);
  });
  const [intake, setIntake] = useState<string>(() =>
    current?.fact === "start_date"
      ? current.basis === "stated_intake" && statedIntakes.includes(current.on)
        ? current.on
        : ANOTHER_DAY
      : "",
  );
  const [problem, setProblem] = useState<string | null>(null);
  const words = MISSING_FACT[fact];
  const choosing = fact === "start_date" && statedIntakes.length > 0;
  const typing = !choosing || intake === ANOTHER_DAY;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (saving) return;
    const basis: StartBasis = typing ? "own_figure" : "stated_intake";
    const read = readFigure(fact, typing ? typed : intake, basis);
    if (!read.ok) {
      setProblem(read.problem);
      return;
    }
    setProblem(null);
    onSave(read.value);
  };

  const errorId = `${id}-error`;
  const box =
    fact === "start_date" || fact === "finish_date" ? (
      <input
        id={`${id}-box`}
        type="date"
        className="input tnum"
        value={typed}
        aria-invalid={problem !== null || undefined}
        aria-describedby={problem !== null ? errorId : undefined}
        onChange={(event) => setTyped(event.target.value)}
      />
    ) : (
      <span className="flex items-center gap-8">
        {fact === "cost" && (
          <span aria-hidden="true" className="font-semibold">
            £
          </span>
        )}
        <input
          id={`${id}-box`}
          className="input tnum figure-input"
          inputMode={fact === "cost" ? "decimal" : "numeric"}
          autoComplete="off"
          value={typed}
          aria-invalid={problem !== null || undefined}
          aria-describedby={problem !== null ? errorId : undefined}
          onChange={(event) => setTyped(event.target.value)}
        />
        {fact === "weekly_hours" && <span aria-hidden="true">hours a week</span>}
      </span>
    );

  return (
    <form className="figure-box" onSubmit={submit} noValidate>
      <p className="figure-missing">
        {!current && <Glyph name="unknown" />}
        {capitalised(words.name)}:{" "}
        {current?.fact === "start_date" && current.basis === "stated_intake"
          ? "your choice from its page"
          : current
            ? "your figure, not checked"
            : "not known yet"}
      </p>
      {choosing ? (
        <fieldset className="grid gap-8">
          <legend className="small">{words.ask}</legend>
          {statedIntakes.map((month) => (
            <label key={month} className="flex items-center gap-8">
              <input
                type="radio"
                name={`${id}-intake`}
                value={month}
                checked={intake === month}
                onChange={() => setIntake(month)}
              />
              {`${formatMonth(month)}, as its page states`}
            </label>
          ))}
          <label className="flex items-center gap-8">
            <input
              type="radio"
              name={`${id}-intake`}
              value={ANOTHER_DAY}
              checked={intake === ANOTHER_DAY}
              onChange={() => setIntake(ANOTHER_DAY)}
            />
            Another day ({suppliedLabel})
          </label>
          {typing && (
            <label htmlFor={`${id}-box`} className="grid gap-4">
              <span className="small muted">Your start date</span>
              {box}
            </label>
          )}
        </fieldset>
      ) : (
        <div className="grid gap-4">
          <label htmlFor={`${id}-box`} className="small">
            {words.ask} ({suppliedLabel})
          </label>
          {box}
        </div>
      )}
      {problem !== null && <FieldError id={errorId}>{problem}</FieldError>}
      {failure}
      <div>
        <Button
          type="submit"
          variant={primary ? "primary" : "secondary"}
          disabledReason={saving ? "Saving…" : undefined}
        >
          Save
        </Button>
      </div>
    </form>
  );
}
