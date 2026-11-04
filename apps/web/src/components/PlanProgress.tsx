"use client";
import { useState } from "react";
import type { PlanSnapshot, ProgressUpdate } from "@/generated/api";
import { formatDay, londonToday } from "@/lib/dates";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";

export function PlanProgress({
  plan,
  onUpdate,
  busy,
  error,
}: {
  plan: PlanSnapshot;
  onUpdate(update: ProgressUpdate): void;
  busy: boolean;
  error: unknown;
}) {
  const [restUntil, setRestUntil] = useState("");
  const [reviewOn, setReviewOn] = useState(plan.progress?.review_on ?? "");
  const completed = plan.progress?.completed_steps ?? [];
  const completedHere = plan.route.steps.filter((step) =>
    completed.includes(step.variant_id),
  ).length;
  const commitments = plan.commitments ?? [];
  const update = (body: Omit<ProgressUpdate, "expected_version">) =>
    onUpdate({ expected_version: plan.version, ...body });
  const today = londonToday();

  return (
    <section className="grid gap-16 plan-actions" aria-label="Planning progress">
      <div className="grid gap-4">
        <h2 className="section-title">Planning progress</h2>
        {plan.route.steps.length === 0 ? (
          <p className="small">This route has no training steps to track.</p>
        ) : (
          <>
            <p className="small">
              You reported {completedHere} of {plan.route.steps.length} steps complete. These
              reports track your plan; they do not verify a skill, qualification or real-world
              outcome.
            </p>
            <progress
              aria-label="Steps reported complete"
              max={plan.route.steps.length}
              value={completedHere}
            >
              {completedHere} of {plan.route.steps.length}
            </progress>
          </>
        )}
      </div>
      <ul className="grid gap-12">
        {plan.route.steps.map((step) => {
          const title = step.title ?? "This step";
          return (
            <li key={step.variant_id} className="card-on-reading grid gap-8 p-16">
              <h3 className="font-semibold">{title}</h3>
              <p className="small">
                {completed.includes(step.variant_id)
                  ? "You reported this step complete."
                  : "Completion has not been reported."}{" "}
                {commitments.includes(step.variant_id)
                  ? "You recorded a commitment to this step."
                  : "No commitment recorded."}
              </p>
              <div className="flex flex-wrap gap-8">
                {!commitments.includes(step.variant_id) && (
                  <Button
                    variant="secondary"
                    disabledReason={busy ? "Saving…" : undefined}
                    onClick={() =>
                      update({ kind: "commitment_accepted", variant_id: step.variant_id })
                    }
                  >
                    Record my commitment
                  </Button>
                )}
                {commitments.includes(step.variant_id) && (
                  <Button
                    variant="quiet"
                    disabledReason={busy ? "Saving…" : undefined}
                    onClick={() =>
                      update({ kind: "commitment_retracted", variant_id: step.variant_id })
                    }
                  >
                    Correct commitment report
                  </Button>
                )}
                {!completed.includes(step.variant_id) && (
                  <Button
                    variant="secondary"
                    disabledReason={busy ? "Saving…" : undefined}
                    onClick={() => update({ kind: "step_completed", variant_id: step.variant_id })}
                  >
                    Report step complete
                  </Button>
                )}
                {completed.includes(step.variant_id) && (
                  <Button
                    variant="quiet"
                    disabledReason={busy ? "Saving…" : undefined}
                    onClick={() => update({ kind: "step_retracted", variant_id: step.variant_id })}
                  >
                    Correct completion report
                  </Button>
                )}
              </div>
            </li>
          );
        })}
      </ul>
      <div className="grid gap-8">
        {plan.progress?.rest_until && (
          <p className="small">Rest recorded through {formatDay(plan.progress.rest_until)}.</p>
        )}
        <div className="flex flex-wrap items-end gap-8">
          <label className="grid gap-4" htmlFor="plan-rest-until">
            Rest from planning until
            <input
              id="plan-rest-until"
              className="input"
              type="date"
              min={today}
              value={restUntil}
              onChange={(event) => setRestUntil(event.target.value)}
            />
          </label>
          <Button
            variant="secondary"
            disabledReason={
              busy ? "Saving…" : restUntil < today ? "Choose today or later" : undefined
            }
            onClick={() => update({ kind: "rest", until: restUntil })}
          >
            Record rest
          </Button>
          {plan.progress?.rest_until && (
            <Button
              variant="secondary"
              disabledReason={busy ? "Saving…" : undefined}
              onClick={() => update({ kind: "resume" })}
            >
              Resume planning
            </Button>
          )}
        </div>
        <p className="small muted">
          Rest changes what Plan suggests next; it does not move route dates.
        </p>
      </div>
      <div className="flex flex-wrap items-end gap-8">
        <label className="grid gap-4" htmlFor="plan-review-on">
          Review this plan on
          <input
            id="plan-review-on"
            className="input"
            type="date"
            min={today}
            value={reviewOn}
            onChange={(event) => setReviewOn(event.target.value)}
          />
        </label>
        <Button
          variant="secondary"
          disabledReason={busy ? "Saving…" : reviewOn < today ? "Choose today or later" : undefined}
          onClick={() => update({ kind: "review_rescheduled", until: reviewOn })}
        >
          Set review date
        </Button>
      </div>
      {plan.progress?.activity && plan.progress.activity.length > 0 && (
        <details className="details small">
          <summary>Activity you reported</summary>
          <ol className="grid gap-4 pt-12">
            {plan.progress.activity.map((item) => (
              <li key={`${item.recorded_at}-${item.kind}-${item.variant_id}-${item.until}`}>
                {formatDay(item.recorded_at)}: {item.kind.replaceAll("_", " ")}
                {item.variant_id ? ` — ${item.step_title ?? item.variant_id}` : ""}
                {item.until ? ` until ${formatDay(item.until)}` : ""}.
              </li>
            ))}
          </ol>
        </details>
      )}
      {error != null && <RequestFailure error={error} />}
    </section>
  );
}
