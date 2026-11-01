"use client";
// The spending line (MODEL-10; the audit's person path, F10): what this workspace's model calls
// have spent this month on the person's key, its monthly limit and the most one run can use,
// and Change, through the API's spend endpoints. In US dollars, as Meta bills; no pounds figure,
// because Careerwright has no pinned exchange rate. Unknown costs count at their full
// reservation in "spent", and the line says how many there are. A demo workspace never calls a
// model, so it shows that instead. Saving is the expected-version command.
import { useId, useState } from "react";
import type { SpendOut } from "@/generated/api";
import { useSetSpendLimits, useSpend } from "@/lib/queries";
import { formatUsd, parseUsdInput, usdAmount } from "@/lib/usd";
import { SPENDING, USD_INPUT_PROBLEM } from "@/lib/vocabulary";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";

function LimitsForm({
  spend,
  onSaved,
  onCancel,
  workspaceId,
}: {
  spend: SpendOut;
  onSaved(): void;
  onCancel(): void;
  workspaceId: string;
}) {
  const id = useId();
  const save = useSetSpendLimits(workspaceId);
  const [month, setMonth] = useState(usdAmount(spend.period_limit_nano_usd));
  const [run, setRun] = useState(usdAmount(spend.run_limit_nano_usd));
  const parsedMonth = parseUsdInput(month);
  const parsedRun = parseUsdInput(run);
  return (
    <form
      className="grid gap-8"
      onSubmit={(event) => {
        event.preventDefault();
        if (parsedMonth.ok && parsedRun.ok) {
          save.mutate(
            {
              expected_version: spend.version,
              period_limit_nano_usd: parsedMonth.nanoUsd,
              run_limit_nano_usd: parsedRun.nanoUsd,
            },
            { onSuccess: onSaved },
          );
        }
      }}
    >
      {(
        [
          ["month", SPENDING.monthLabel, month, setMonth, parsedMonth],
          ["run", SPENDING.runLabel, run, setRun, parsedRun],
        ] as const
      ).map(([name, label, value, set, parsed]) => (
        <div key={name} className="grid gap-4">
          <label htmlFor={`${id}-${name}`} className="small">
            {label}
          </label>
          <input
            id={`${id}-${name}`}
            className="input"
            inputMode="decimal"
            value={value}
            aria-invalid={!parsed.ok}
            aria-describedby={parsed.ok ? undefined : `${id}-${name}-problem`}
            onChange={(event) => set(event.target.value)}
          />
          {!parsed.ok && (
            <p id={`${id}-${name}-problem`} className="small">
              {USD_INPUT_PROBLEM[parsed.reason]}
            </p>
          )}
        </div>
      ))}
      <div className="flex gap-8">
        <Button
          type="submit"
          variant="primary"
          disabledReason={
            save.isPending
              ? "Saving…"
              : !parsedMonth.ok || !parsedRun.ok
                ? "Correct the amounts first."
                : undefined
          }
        >
          {SPENDING.save}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          {SPENDING.cancel}
        </Button>
      </div>
      {save.error !== null && <RequestFailure error={save.error} />}
    </form>
  );
}

export function ModelSpending({ workspaceId, demo }: { workspaceId: string; demo: boolean }) {
  const id = useId();
  const spend = useSpend(workspaceId, !demo);
  const [changing, setChanging] = useState(false);
  const [saved, setSaved] = useState(false);
  const title = (
    <h3 id={`${id}-title`} className="small font-semibold">
      {SPENDING.heading}
    </h3>
  );
  if (demo) {
    return (
      <section className="grid gap-4" aria-labelledby={`${id}-title`}>
        {title}
        <p className="small muted">{SPENDING.demo}</p>
      </section>
    );
  }
  const current = spend.data;
  if (current === undefined) {
    return spend.error ? <RequestFailure error={spend.error} /> : null;
  }
  return (
    <section className="grid gap-4" aria-labelledby={`${id}-title`}>
      {title}
      <p className="small">
        {SPENDING.spent(
          formatUsd(current.period_committed_nano_usd),
          formatUsd(current.period_limit_nano_usd),
        )}
      </p>
      <p className="small muted">{SPENDING.perRun(formatUsd(current.run_limit_nano_usd))}</p>
      {current.unknown_cost_attempts > 0 && (
        <p className="small muted">{SPENDING.unknown(current.unknown_cost_attempts)}</p>
      )}
      <p className="small muted">{SPENDING.dollars}</p>
      {changing ? (
        <LimitsForm
          spend={current}
          workspaceId={workspaceId}
          onSaved={() => {
            setChanging(false);
            setSaved(true);
          }}
          onCancel={() => setChanging(false)}
        />
      ) : (
        <div>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setSaved(false);
              setChanging(true);
            }}
          >
            {SPENDING.change}
          </Button>
        </div>
      )}
      <p role="status" className="small muted">
        {saved && SPENDING.saved}
      </p>
    </section>
  );
}
