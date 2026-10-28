"use client";
// Form controls for one profile answer: how it is answered (its field state) and, when
// answered, the value. Native controls, labelled and described, with errors announced.
import { type ReactNode, useId } from "react";
import type { FieldState } from "@/generated/api";
import type { FieldDraft } from "@/lib/profile";
import { FIELD_STATE, FIELD_STATE_ORDER } from "@/lib/vocabulary";
import { Button } from "./Button";
import { Glyph } from "./Glyph";

type ControlProps = {
  label: string;
  draft: FieldDraft;
  error?: string;
  /** IDs of the notes that describe this control (its error, a conflict), space-separated. */
  describedBy?: string;
  onChange(next: FieldDraft): void;
};

const ids = (...values: Array<string | undefined>) =>
  values.filter((value) => value !== undefined).join(" ") || undefined;

/** `disabledReason` disables the control and says why beside it (never disabled silently). */
export function FieldStateSelect({
  label,
  draft,
  disabledReason,
  describedBy,
  onChange,
}: ControlProps & { disabledReason?: string }) {
  const id = useId();
  return (
    <div className="grid gap-4">
      <label htmlFor={id} className="small muted">
        How you answer {label.toLowerCase()}
      </label>
      <select
        id={id}
        className="select"
        value={draft.state}
        disabled={disabledReason !== undefined}
        aria-describedby={ids(
          disabledReason !== undefined ? `${id}-reason` : undefined,
          describedBy,
        )}
        onChange={(event) => onChange({ ...draft, state: event.target.value as FieldState })}
      >
        {FIELD_STATE_ORDER.map((state) => (
          <option key={state} value={state}>
            {FIELD_STATE[state]}
          </option>
        ))}
      </select>
      {disabledReason !== undefined && (
        <p id={`${id}-reason`} className="small muted">
          {disabledReason}
        </p>
      )}
    </div>
  );
}

export function FieldError({ id, children }: { id: string; children: ReactNode }) {
  return (
    <p id={id} className="field-error" role="alert">
      <Glyph name="error" />
      <span>{children}</span>
    </p>
  );
}

type ValueProps = ControlProps & { kind: "text" | "hours" | "money" };

export function ValueInput({ label, kind, draft, error, describedBy, onChange }: ValueProps) {
  const id = useId();
  const prefix = kind === "money" ? "£" : undefined;
  return (
    <div className="grid gap-4">
      <label htmlFor={id} className="small muted">
        {label}
        {kind === "hours" ? ", hours a week" : kind === "money" ? ", in pounds" : ""}
      </label>
      <div className="flex items-center gap-8">
        {prefix !== undefined && (
          <span aria-hidden="true" className="font-semibold">
            {prefix}
          </span>
        )}
        <input
          id={id}
          className="input tnum"
          inputMode={kind === "text" ? "text" : "decimal"}
          autoComplete="off"
          value={draft.text}
          aria-invalid={error !== undefined || undefined}
          aria-describedby={describedBy}
          onChange={(event) => onChange({ ...draft, text: event.target.value })}
        />
      </div>
    </div>
  );
}

type ListProps = ControlProps & { itemLabel: string; limit: number };

export function ListInput({
  label,
  itemLabel,
  limit,
  draft,
  error,
  describedBy,
  onChange,
}: ListProps) {
  const items = draft.items.length === 0 ? [""] : draft.items;
  const full = items.length >= limit;
  const set = (next: string[]) => onChange({ ...draft, items: next });
  return (
    <fieldset className="grid gap-8" aria-describedby={describedBy}>
      <legend className="small muted">{label}</legend>
      {items.map((item, index) => {
        const name = `${itemLabel} ${index + 1}`;
        return (
          // biome-ignore lint/suspicious/noArrayIndexKey: entries are positional and editable
          <div key={index} className="flex items-center gap-8">
            <input
              className="input"
              aria-label={name}
              value={item}
              aria-invalid={error !== undefined || undefined}
              onChange={(event) =>
                set(items.map((value, at) => (at === index ? event.target.value : value)))
              }
            />
            {items.length > 1 && (
              <button
                type="button"
                className="btn btn-quiet"
                aria-label={`Remove ${name}`}
                onClick={() => set(items.filter((_, at) => at !== index))}
              >
                Remove
              </button>
            )}
          </div>
        );
      })}
      <div className="flex flex-wrap items-center gap-8">
        <Button
          variant="quiet"
          disabledReason={full ? `At most ${limit} are supported.` : undefined}
          onClick={() => set([...items, ""])}
        >
          Add another {itemLabel.toLowerCase()}
        </Button>
      </div>
    </fieldset>
  );
}
