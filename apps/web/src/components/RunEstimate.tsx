"use client";
// What a paid run may cost, shown before the person starts it (spec section 16: "display
// estimated incremental cost before deep research"; MODEL-08). One way for every place a person
// starts research (Tasks 6e, 7e and 8): the API computes both maxima and whether the spending
// limits leave room; this only words them, in US dollars as Meta bills. A limit that would
// refuse the run says where to raise it.
import type { RunKind } from "@/generated/api";
import { useRunEstimate } from "@/lib/queries";
import { formatUsd } from "@/lib/usd";
import { RUN_ESTIMATE } from "@/lib/vocabulary";
import { RequestFailure } from "./PageState";

export function RunEstimate({ workspaceId, kind }: { workspaceId: string; kind: RunKind }) {
  const estimate = useRunEstimate(workspaceId, kind);
  const shown = estimate.data;
  if (shown === undefined) {
    return estimate.error ? <RequestFailure error={estimate.error} /> : null;
  }
  if (shown.model_mode === "fixture") {
    return <p className="small muted">{RUN_ESTIMATE.free}</p>;
  }
  return (
    <div className="grid gap-4">
      <p className="small">
        {RUN_ESTIMATE.costs(formatUsd(shown.per_run_nano_usd))}
        {shown.hard_maximum_nano_usd > shown.per_run_nano_usd &&
          ` ${RUN_ESTIMATE.restart(formatUsd(shown.hard_maximum_nano_usd))}`}
      </p>
      {shown.refused_scope !== null && (
        <p className="small">{RUN_ESTIMATE.refused[shown.refused_scope]}</p>
      )}
    </div>
  );
}
