import { type FormEvent, useId, useState } from "react";
import type {
  CommitmentInput,
  DebtInput,
  Need,
  PlanningInputsDocument,
  PlanningInputsIn,
} from "@/generated/api";
import { formatMoney, parseMoneyInput } from "@/lib/money";
import {
  BASELINE_KIND,
  NEED_EFFECT,
  NEEDED_INPUT,
  notWorkingWords,
  OBJECTIVE_BASIS,
  WORK_RIGHTS,
} from "@/lib/optionWords";
import { problemText } from "@/lib/profile";
import { Button } from "./Button";
import { FieldError } from "./fields";

type Save = (update: (inputs: PlanningInputsIn) => PlanningInputsIn) => Promise<boolean>;
type Listed<T> = { id: string; value: T };

export function PlanningQuestion({
  need,
  current,
  editing = false,
  saving,
  onSave,
  onCancel,
}: {
  need: Need;
  current?: PlanningInputsDocument;
  editing?: boolean;
  saving: boolean;
  onSave: Save;
  onCancel?: () => void;
}) {
  const id = useId();
  const [choice, setChoice] = useState(() => {
    if (need.input === "objective_basis") return current?.objective_basis ?? "";
    if (need.input === "baseline") return current?.baseline?.kind ?? "";
    if (need.input === "work_rights") return current?.work_rights ?? "";
    return "";
  });
  const [amount, setAmount] = useState(() => {
    const value =
      need.input === "baseline"
        ? current?.baseline?.net_income
        : need.input === "continuation"
          ? current?.continuation?.net_income
          : need.input === "opening_cash" ||
              need.input === "living_costs" ||
              need.input === "reserve"
            ? current?.[need.input]
            : null;
    return value ? formatMoney(value).slice(1) : "";
  });
  const [hours, setHours] = useState(() => {
    const value =
      need.input === "continuation"
        ? current?.continuation?.hours_per_week
        : need.input === "weekly_availability" || need.input === "scenario_delay_months"
          ? current?.[need.input]
          : null;
    return value === null || value === undefined ? "" : String(value);
  });
  const [none, setNone] = useState(
    () =>
      (need.input === "commitments" && current?.commitments?.length === 0) ||
      (need.input === "existing_debts" && current?.existing_debts?.length === 0),
  );
  const [notWorking, setNotWorking] = useState(
    () =>
      need.input === "continuation" &&
      current?.continuation?.hours_per_week === 0 &&
      current.continuation.net_income.minor_units === 0,
  );
  const [commitments, setCommitments] = useState<Listed<CommitmentInput>[]>(() =>
    (need.input === "commitments" ? (current?.commitments ?? []) : []).map((value) => ({
      id: crypto.randomUUID(),
      value,
    })),
  );
  const [debts, setDebts] = useState<Listed<DebtInput>[]>(() =>
    (need.input === "existing_debts" ? (current?.existing_debts ?? []) : []).map((value) => ({
      id: crypto.randomUUID(),
      value,
    })),
  );
  const [problem, setProblem] = useState<string | null>(null);
  const fact = NEEDED_INPUT[need.input];

  const money = () => {
    const result = parseMoneyInput(amount, "GBP");
    if (result.ok) return result.money;
    setProblem(problemText({ kind: "money", reason: result.reason }));
    return null;
  };
  const whole = (text: string, min: number, max: number) => {
    const value = Number(text);
    if (/^\d+$/.test(text) && value >= min && value <= max) return value;
    setProblem(`Enter a whole number from ${min} to ${max}.`);
    return null;
  };
  const pendingCommitment = (): CommitmentInput | null => {
    if (!choice || !hours) {
      setProblem("Choose the commitment and its weekly hours.");
      return null;
    }
    const value = whole(hours, 0, 168);
    return value === null
      ? null
      : { kind: choice as CommitmentInput["kind"], hours_per_week: value };
  };
  const pendingDebt = (): DebtInput | null => {
    if (!amount) {
      setProblem("Enter a monthly repayment.");
      return null;
    }
    const value = money();
    return value === null ? null : { monthly_repayment: value };
  };
  const addAnother = () => {
    if ((need.input === "commitments" ? commitments : debts).length >= 49) {
      setProblem("You can list up to 50 here.");
      return;
    }
    if (need.input === "commitments") {
      const value = pendingCommitment();
      if (value === null) return;
      setCommitments((current) => [...current, { id: crypto.randomUUID(), value }]);
      setChoice("");
      setHours("");
    } else {
      const value = pendingDebt();
      if (value === null) return;
      setDebts((current) => [...current, { id: crypto.randomUUID(), value }]);
      setAmount("");
    }
    setProblem(null);
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (saving) return;
    let update: ((inputs: PlanningInputsIn) => PlanningInputsIn) | null = null;
    switch (need.input) {
      case "objective_basis":
        if (choice === "economic" || choice === "direct_spending") {
          update = (inputs) => ({ ...inputs, objective_basis: choice });
        }
        break;
      case "continuation": {
        const weekly = notWorking ? 0 : whole(hours, 0, 168);
        const pay = notWorking ? { minor_units: 0, currency: "GBP" as const } : money();
        if (weekly !== null && pay !== null) {
          update = (inputs) => ({
            ...inputs,
            continuation: { hours_per_week: weekly, net_income: pay },
          });
        }
        break;
      }
      case "baseline": {
        const pay = money();
        if (choice in BASELINE_KIND && pay !== null) {
          update = (inputs) => ({
            ...inputs,
            baseline: { kind: choice as keyof typeof BASELINE_KIND, net_income: pay },
          });
        }
        break;
      }
      case "opening_cash":
      case "living_costs":
      case "reserve": {
        const value = money();
        if (value !== null) update = (inputs) => ({ ...inputs, [need.input]: value });
        break;
      }
      case "weekly_availability":
      case "scenario_delay_months": {
        const value = whole(
          hours,
          need.input === "scenario_delay_months" ? 1 : 0,
          need.input === "scenario_delay_months" ? 24 : 168,
        );
        if (value !== null) update = (inputs) => ({ ...inputs, [need.input]: value });
        break;
      }
      case "commitments": {
        if (none) update = (inputs) => ({ ...inputs, commitments: [] });
        else {
          const hasPending = Boolean(choice || hours);
          const value = hasPending ? pendingCommitment() : null;
          if ((value !== null || !hasPending) && (value !== null || commitments.length > 0))
            update = (inputs) => ({
              ...inputs,
              commitments: [
                ...commitments.map((item) => item.value),
                ...(value === null ? [] : [value]),
              ],
            });
        }
        break;
      }
      case "existing_debts": {
        if (none) update = (inputs) => ({ ...inputs, existing_debts: [] });
        else {
          const hasPending = Boolean(amount);
          const value = hasPending ? pendingDebt() : null;
          if ((value !== null || !hasPending) && (value !== null || debts.length > 0))
            update = (inputs) => ({
              ...inputs,
              existing_debts: [
                ...debts.map((item) => item.value),
                ...(value === null ? [] : [value]),
              ],
            });
        }
        break;
      }
      case "work_rights":
        if (choice in WORK_RIGHTS)
          update = (inputs) => ({
            ...inputs,
            work_rights: choice as "held" | "not_held" | "unknown",
          });
        break;
      case "direct_spend_cap":
      case "monthly_payment_cap":
        return;
    }
    if (update === null) {
      setProblem((current) => current ?? "Choose an answer first.");
      return;
    }
    setProblem(null);
    void onSave(update);
  };

  const moneyBox = (
    <label className="grid gap-4" htmlFor={`${id}-amount`}>
      <span className="small">Pounds</span>
      <input
        id={`${id}-amount`}
        className="input tnum"
        inputMode="decimal"
        value={amount}
        onChange={(event) => setAmount(event.target.value)}
      />
    </label>
  );
  const hoursBox = (label: string) => (
    <label className="grid gap-4" htmlFor={`${id}-hours`}>
      <span className="small">{label}</span>
      <input
        id={`${id}-hours`}
        className="input tnum"
        inputMode="numeric"
        value={hours}
        onChange={(event) => setHours(event.target.value)}
      />
    </label>
  );
  const choices = (values: Record<string, string>) => (
    <label className="grid gap-4" htmlFor={`${id}-choice`}>
      <span className="small">Choose one</span>
      <select
        id={`${id}-choice`}
        className="input"
        value={choice}
        onChange={(event) => setChoice(event.target.value)}
      >
        <option value="">Choose…</option>
        {Object.entries(values).map(([value, words]) => (
          <option key={value} value={value}>
            {words}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <form className="grid gap-12" onSubmit={submit} noValidate>
      <h3 className="section-title">{editing ? `Change ${fact.name.toLowerCase()}` : fact.name}</h3>
      <p className="small">
        {fact.meaning} {!editing && NEED_EFFECT[need.effect]}
      </p>
      {need.input === "objective_basis" && choices(OBJECTIVE_BASIS)}
      {need.input === "work_rights" && choices(WORK_RIGHTS)}
      {need.input === "baseline" && (
        <>
          {choices(BASELINE_KIND)}
          {moneyBox}
        </>
      )}
      {need.input === "continuation" && (
        <>
          <label className="flex items-center gap-8">
            <input
              type="checkbox"
              checked={notWorking}
              onChange={(event) => setNotWorking(event.target.checked)}
            />
            {notWorkingWords}
          </label>
          {!notWorking && (
            <>
              {hoursBox("Hours a week you work now")}
              {moneyBox}
            </>
          )}
        </>
      )}
      {(["opening_cash", "living_costs", "reserve"] as const).includes(
        need.input as "opening_cash",
      ) && moneyBox}
      {need.input === "weekly_availability" && hoursBox("Hours a week")}
      {need.input === "scenario_delay_months" && hoursBox("Months late to plan for")}
      {(need.input === "commitments" || need.input === "existing_debts") && (
        <>
          <label className="flex items-center gap-8">
            <input
              type="checkbox"
              checked={none}
              onChange={(event) => setNone(event.target.checked)}
            />
            I have none
          </label>
          {!none &&
            (need.input === "commitments" ? (
              <>
                {commitments.length > 0 && (
                  <ul className="fact-list">
                    {commitments.map((item) => (
                      <li key={item.id}>
                        {item.value.hours_per_week} hours a week:{" "}
                        {item.value.kind.replaceAll("_", " ")}
                        <Button
                          type="button"
                          aria-label={`Remove ${item.value.hours_per_week} hours of ${item.value.kind.replaceAll("_", " ")}`}
                          onClick={() =>
                            setCommitments((current) => current.filter((row) => row.id !== item.id))
                          }
                        >
                          Remove
                        </Button>
                      </li>
                    ))}
                  </ul>
                )}
                {choices({
                  care: "Caring",
                  commute: "Travel",
                  second_job: "A second job",
                  other: "Something else",
                })}
                {hoursBox("Hours a week")}
              </>
            ) : (
              <>
                {debts.length > 0 && (
                  <ul className="fact-list">
                    {debts.map((item) => (
                      <li key={item.id}>
                        {formatMoney(item.value.monthly_repayment)} a month
                        <Button
                          type="button"
                          aria-label={`Remove ${formatMoney(item.value.monthly_repayment)} monthly debt repayment`}
                          onClick={() =>
                            setDebts((current) => current.filter((row) => row.id !== item.id))
                          }
                        >
                          Remove
                        </Button>
                      </li>
                    ))}
                  </ul>
                )}
                {moneyBox}
              </>
            ))}
          {!none && (
            <Button type="button" onClick={addAnother}>
              Add another {need.input === "commitments" ? "commitment" : "debt"}
            </Button>
          )}
        </>
      )}
      {problem && <FieldError id={`${id}-error`}>{problem}</FieldError>}
      <div>
        <Button type="submit" variant="primary" disabledReason={saving ? "Saving…" : undefined}>
          Save this answer
        </Button>
        {onCancel && (
          <Button type="button" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}
