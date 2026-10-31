"use client";
// The calm support panel (ADR 0007 decision 7; `careerwright.profile.safety`): beside a sent
// message that holds a risk stem, and beside the first question's title field when what is
// typed there does. Calm, not blocking, dismissible; its words and services are the API's.
import { useId } from "react";
import type { SupportNoteOut } from "@/generated/api";
import { useSupportShown } from "@/lib/world/settings";
import { Button } from "./Button";

const day = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric" });

export function SupportNote({ note, onDismiss }: { note: SupportNoteOut; onDismiss(): void }) {
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
