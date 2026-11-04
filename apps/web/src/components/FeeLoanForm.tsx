import { type FormEvent, useId, useState } from "react";
import type { TuitionFeeLoan, TuitionFeeLoanInput } from "@/generated/api";
import { formatMoney, parseMoneyInput } from "@/lib/money";
import { AWARD_STATE, ELIGIBILITY_STATUS, FEE_LOAN_KIND, LOAN_TO_REPAY } from "@/lib/optionWords";
import { problemText } from "@/lib/profile";
import { Button } from "./Button";
import { FieldError } from "./fields";

export function FeeLoanForm({
  current,
  saving,
  onSave,
  onCancel,
}: {
  current: TuitionFeeLoan | null | undefined;
  saving: boolean;
  onSave(loan: TuitionFeeLoanInput): void;
  onCancel(): void;
}) {
  const id = useId();
  const [kind, setKind] = useState(current ? (current.kind ?? "tuition_fee_loan") : "");
  const [amount, setAmount] = useState(current?.amount ? formatMoney(current.amount).slice(1) : "");
  const [eligibility, setEligibility] = useState(current?.eligibility ?? "");
  const [application, setApplication] = useState(current?.application ?? "");
  const [problem, setProblem] = useState<string | null>(null);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (saving) return;
    if (!kind || !eligibility || !application) {
      setProblem("Choose the loan and its status first.");
      return;
    }
    if (application === "approved" && eligibility !== "confirmed") {
      setProblem("An approved loan needs a confirmed eligibility answer.");
      return;
    }
    const parsed = amount.trim() === "" ? null : parseMoneyInput(amount, "GBP");
    if (parsed !== null && !parsed.ok) {
      setProblem(problemText({ kind: "money", reason: parsed.reason }));
      return;
    }
    setProblem(null);
    onSave({
      kind: kind as TuitionFeeLoanInput["kind"],
      amount: parsed?.money ?? null,
      eligibility: eligibility as TuitionFeeLoanInput["eligibility"],
      application: application as TuitionFeeLoanInput["application"],
    });
  };
  return (
    <form className="grid gap-12" onSubmit={submit} noValidate>
      <h3 className="section-title">Fee loan</h3>
      <p className="small">{LOAN_TO_REPAY}</p>
      <label className="grid gap-4" htmlFor={`${id}-kind`}>
        <span className="small">Which loan?</span>
        <select
          id={`${id}-kind`}
          className="input"
          value={kind}
          onChange={(event) => setKind(event.target.value)}
        >
          <option value="">Choose…</option>
          {Object.entries(FEE_LOAN_KIND).map(([value, words]) => (
            <option key={value} value={value}>
              {words}
            </option>
          ))}
        </select>
      </label>
      <label className="grid gap-4" htmlFor={`${id}-amount`}>
        <span className="small">Amount in pounds, if you know it</span>
        <input
          id={`${id}-amount`}
          className="input tnum"
          inputMode="decimal"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
        />
      </label>
      <label className="grid gap-4" htmlFor={`${id}-eligibility`}>
        <span className="small">Do the conditions apply to you?</span>
        <select
          id={`${id}-eligibility`}
          className="input"
          value={eligibility}
          onChange={(event) => setEligibility(event.target.value)}
        >
          <option value="">Choose…</option>
          {Object.entries(ELIGIBILITY_STATUS).map(([value, words]) => (
            <option key={value} value={value}>
              {words}
            </option>
          ))}
        </select>
      </label>
      <label className="grid gap-4" htmlFor={`${id}-application`}>
        <span className="small">What happened when you applied?</span>
        <select
          id={`${id}-application`}
          className="input"
          value={application}
          onChange={(event) => setApplication(event.target.value)}
        >
          <option value="">Choose…</option>
          {Object.entries(AWARD_STATE).map(([value, words]) => (
            <option key={value} value={value}>
              {words}
            </option>
          ))}
        </select>
      </label>
      {problem && <FieldError id={`${id}-error`}>{problem}</FieldError>}
      <div className="flex flex-wrap gap-8">
        <Button type="submit" variant="primary" disabledReason={saving ? "Saving…" : undefined}>
          Save loan answer
        </Button>
        <Button type="button" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
