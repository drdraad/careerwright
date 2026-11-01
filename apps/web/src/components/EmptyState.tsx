import type { ReactNode } from "react";
import type { WorkState } from "@/generated/api";
import type { DISPLAY_STATE } from "@/lib/vocabulary";
import { StatusBadge } from "./Status";

type Props = {
  state: WorkState | keyof typeof DISPLAY_STATE;
  title: string;
  /** Why it is empty, in words: never a blank area and never a zero standing in for unknown. */
  children: ReactNode;
  /** What the person can do next. */
  next?: ReactNode;
};

export function EmptyState({ state, title, children, next }: Props) {
  return (
    <section className="empty" aria-label={title}>
      <StatusBadge state={state} />
      <h2 className="display text-25">{title}</h2>
      <div className="measure grid gap-8">{children}</div>
      {next !== undefined && <div className="flex flex-wrap gap-8 pt-8">{next}</div>}
    </section>
  );
}
