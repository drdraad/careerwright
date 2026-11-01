"use client";
// The calm support panel (ADR 0007 decision 7; `careerwright.profile.safety`): beside a sent
// message that holds a risk stem, above the first question's title field when what is typed
// there does, and beside What we know's answers when an entry saved there does. Calm, not
// blocking, dismissible; its words and services are the API's.
import { type ReactNode, useId } from "react";
import type { SupportNoteOut, SupportResourceOut } from "@/generated/api";
import { useSupportShown } from "@/lib/world/settings";
import { Button } from "./Button";

const day = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric" });
const names = new Intl.ListFormat("en-GB", { type: "conjunction" });

/** When the services were checked: the first one's date for "these services", and any
 *  service checked on another day named with its own date (Childline, support-policy-12). */
function checkedLine(resources: SupportResourceOut[]): string | null {
  const byDate = new Map<string, string[]>();
  for (const { checked_on, name } of resources) {
    byDate.set(checked_on, [...(byDate.get(checked_on) ?? []), name]);
  }
  const [first, ...others] = [...byDate];
  if (first === undefined) return null;
  const dated = (date: string) => day.format(new Date(`${date}T12:00:00Z`));
  const later = others.map(([date, named]) => `, and ${names.format(named)} on ${dated(date)}`);
  return `These services were checked on their own websites on ${dated(first[0])}${later.join("")}.`;
}

export function SupportNote({
  note,
  onDismiss,
  actions,
}: {
  note: SupportNoteOut;
  onDismiss(): void;
  /** The way forward the panel's words name (keeping a typed title): right after the line
   *  that names it, before the services, so a phone's first screen holds it (R2-M1). */
  actions?: ReactNode;
}) {
  // While it shows, the world is still (plan section 4: distress stills the world).
  useSupportShown();
  const titleId = useId();
  const checked = checkedLine(note.resources);
  return (
    <section className="card grid gap-8 small" aria-labelledby={titleId}>
      <h3 id={titleId} className="font-semibold">
        Support is available
      </h3>
      <p>{note.message}</p>
      {actions !== undefined && actions !== null && actions !== false && (
        <div className="flex flex-wrap items-center gap-8">{actions}</div>
      )}
      <ul className="plain-list">
        {note.resources.map((resource) => (
          <li key={resource.name}>
            <strong>{resource.name}:</strong> {resource.contact}. {resource.when}.
          </li>
        ))}
      </ul>
      {checked !== null && <p className="muted">{checked}</p>}
      <div className="flex flex-wrap items-center gap-8">
        <Button variant="quiet" onClick={onDismiss}>
          Dismiss <span className="sr-only">the support note</span>
        </Button>
      </div>
    </section>
  );
}
