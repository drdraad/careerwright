"use client";

import Link from "next/link";
import { type FormEvent, useId, useState } from "react";
import type {
  ActionConcept,
  CheckpointOut,
  ConditionFact,
  EntryRequirement,
  NeededInput,
  Offering,
  OptionFacts,
  OptionsOut,
  PlanningInputsDocument,
  PlanningInputsIn,
  Variant,
} from "@/generated/api";
import { chapterHref } from "@/lib/chapters";
import { formatDay, formatMonth } from "@/lib/dates";
import { type Figure, isFigureFact } from "@/lib/figures";
import { formatMoney } from "@/lib/money";
import {
  ACTION_KIND,
  AGE_NOT_APPLIED,
  AWARD_STATE,
  ageRuleWords,
  conditionWords,
  ELIGIBILITY_STATUS,
  FEE_LOAN_KIND,
  INSTRUMENT_KIND,
  LOAN_TO_REPAY,
  missingLine,
  NEEDED_INPUT,
  NOT_KNOWN,
  notWorkingWords,
  optionState,
  packLine,
  paymentCapMeaning,
  RECORD_STATE,
  suppliedLabel,
} from "@/lib/optionWords";
import { submitted, withExcluded, withFigure, withVariant } from "@/lib/planningInputs";
import {
  useCheckpoint,
  usePasteOptionText,
  usePlanningInputs,
  usePlanningOptions,
  useWritePlanningInputs,
} from "@/lib/queries";
import { type AddedOption, AddOptionForm } from "./AddOptionForm";
import { Button } from "./Button";
import { FeeLoanForm } from "./FeeLoanForm";
import { LoadingState } from "./LoadingState";
import { MissingFactBox } from "./MissingFactBox";
import { OptionResearch } from "./OptionResearch";
import { RequestFailure } from "./PageState";
import { PlanningAnswers } from "./PlanningAnswers";
import { PlanningQuestion } from "./PlanningQuestion";

type Action = (update: (inputs: PlanningInputsIn) => PlanningInputsIn) => Promise<boolean>;

function EntryQuestion({
  requirements,
  current,
  saving,
  onSave,
}: {
  requirements: EntryRequirement[];
  current: boolean | null;
  saving: boolean;
  onSave(answer: boolean | null): void;
}) {
  const id = useId();
  const [answer, setAnswer] = useState(current === null ? "" : current ? "yes" : "no");
  const [problem, setProblem] = useState(false);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!answer) {
      setProblem(true);
      return;
    }
    setProblem(false);
    onSave(answer === "not_sure" ? null : answer === "yes");
  };
  return (
    <form className="grid gap-8" onSubmit={submit} noValidate>
      <p className="small">The option states these entry requirements:</p>
      <ul className="grid gap-4 small">
        {requirements.map((item) => (
          <li key={`${item.field}-${JSON.stringify(item.value)}`}>
            {typeof item.value === "string" ? item.value : "An entry condition in the source"}
            {item.qualifications.some((fact) => fact.standing === "expected_not_met") &&
              " — your expected qualification is not achieved yet"}
          </li>
        ))}
      </ul>
      <label className="grid gap-4" htmlFor={`${id}-answer`}>
        <span className="small">
          Do you meet the entry requirements? Your answer is not checked.
        </span>
        <select
          id={`${id}-answer`}
          className="input"
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
        >
          <option value="">Choose…</option>
          <option value="yes">Yes, as far as I know</option>
          <option value="no">No</option>
          <option value="not_sure">Not sure</option>
        </select>
      </label>
      {problem && <p role="alert">Choose an answer first.</p>}
      {answer === "not_sure" && <p className="small">This stays unresolved in route searches.</p>}
      <div>
        <Button type="submit" variant="secondary" disabledReason={saving ? "Saving…" : undefined}>
          Save entry answer
        </Button>
      </div>
    </form>
  );
}

function EligibilityQuestion({
  condition,
  saving,
  primary = true,
  onSave,
}: {
  condition: ConditionFact;
  saving: boolean;
  primary?: boolean;
  onSave(
    answer: "confirmed" | "potentially_eligible" | "ineligible" | "insufficient_information",
  ): void;
}) {
  const id = useId();
  const [answer, setAnswer] = useState(condition.status ?? "");
  const [problem, setProblem] = useState(false);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!answer) {
      setProblem(true);
      return;
    }
    setProblem(false);
    onSave(answer as ConditionFact["status"] & string);
  };
  return (
    <form className="grid gap-8" onSubmit={submit} noValidate>
      <label className="grid gap-4" htmlFor={`${id}-answer`}>
        <span className="small">
          Does this condition apply to you? {conditionWords(condition.field, condition.value)}
        </span>
        <select
          id={`${id}-answer`}
          className="input"
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
        >
          <option value="">Choose…</option>
          {Object.entries(ELIGIBILITY_STATUS).map(([value, words]) => (
            <option key={value} value={value}>
              {words}
            </option>
          ))}
        </select>
      </label>
      {problem && <p role="alert">Choose an answer first.</p>}
      <div>
        <Button
          type="submit"
          variant={primary ? "primary" : "secondary"}
          disabledReason={saving ? "Saving…" : undefined}
        >
          Save this answer
        </Button>
      </div>
    </form>
  );
}

function OptionDetail({
  workspaceId,
  option,
  concept,
  offering,
  variant,
  inputs,
  pinned,
  onPin,
  busy,
  onWrite,
}: {
  workspaceId: string;
  option: OptionFacts;
  concept: ActionConcept;
  offering: Offering | undefined;
  variant: Variant | undefined;
  inputs: PlanningInputsDocument;
  pinned: boolean;
  onPin(): void;
  busy: boolean;
  onWrite: Action;
}) {
  const [editingLoan, setEditingLoan] = useState(false);
  const plan = offering?.payment_plans?.find((p) => p.plan_id === option.plan_id);
  const quotedCost = offering?.facts?.find((fact) => fact.field === "quoted_cost")?.value;
  const figure = option.missing.find(isFigureFact);
  const condition = option.eligibility_conditions.find((item) => item.status !== "confirmed");
  const revisableConditions = option.eligibility_conditions.filter(
    (item) => item.status !== null && item.field !== condition?.field,
  );
  const loan = variant?.tuition_fee_loan;
  const figures = inputs.offering_figures?.find((item) => item.offering_id === option.offering_id);
  const suppliedFigures: Figure[] = [];
  if (figures?.start) suppliedFigures.push({ fact: "start_date", ...figures.start });
  if (figures?.finish) suppliedFigures.push({ fact: "finish_date", on: figures.finish });
  if (figures?.weekly_hours !== null && figures?.weekly_hours !== undefined)
    suppliedFigures.push({ fact: "weekly_hours", hours: figures.weekly_hours });
  if (figures?.cost) suppliedFigures.push({ fact: "cost", money: figures.cost });
  const saveCondition = (condition: ConditionFact, answer: ConditionFact["status"] & string) =>
    void onWrite((inputs) =>
      withVariant(inputs, option.variant_id, {
        condition_statuses: {
          ...(inputs.variants?.find((item) => item.variant_id === option.variant_id)
            ?.condition_statuses ?? {}),
          [condition.field]: answer,
        },
      }),
    );
  const saveEntry = (answer: boolean | null) =>
    void onWrite((inputs) =>
      withVariant(inputs, option.variant_id, { entry_requirements_met: answer }),
    );
  return (
    <section
      className="option-detail grid gap-16"
      aria-label={`${concept.title ?? "Option"} details`}
    >
      <header className="grid gap-8">
        <h3 className="display text-25">{concept.title ?? "Your option"}</h3>
        <p className="small muted">{optionState(option)}</p>
      </header>
      {missingLine(option.missing) && <p className="small">{missingLine(option.missing)}</p>}
      {option.entry_expected && (
        <p className="small">
          An entry requirement depends on a qualification you expect: if you get your grades.
        </p>
      )}
      {option.missing.includes("entry_confirmation") && (
        <p className="small">
          Review your qualifications in{" "}
          <Link href={chapterHref(workspaceId, "skills")}>Skills</Link>, then answer the entry
          question below.
        </p>
      )}
      {option.entry_requirements.length > 0 && !editingLoan && (
        <div className="grid gap-8">
          {option.entry_requirements_met !== null && (
            <p className="small">
              You said you {option.entry_requirements_met ? "meet" : "do not meet"} the entry
              requirements. Careerwright has not checked this at its source.
            </p>
          )}
          {option.entry_requirements_met === null ? (
            <EntryQuestion
              requirements={option.entry_requirements}
              current={null}
              saving={busy}
              onSave={saveEntry}
            />
          ) : (
            <details>
              <summary>Change entry answer</summary>
              <div className="pt-12">
                <EntryQuestion
                  requirements={option.entry_requirements}
                  current={option.entry_requirements_met}
                  saving={busy}
                  onSave={saveEntry}
                />
              </div>
            </details>
          )}
        </div>
      )}
      {figure && !editingLoan && (
        <MissingFactBox
          key={`${option.offering_id}-${figure}`}
          fact={figure}
          statedIntakes={figure === "start_date" ? option.stated_intakes : []}
          primary
          saving={busy}
          onSave={(value: Figure) =>
            void onWrite((inputs) => withFigure(inputs, option.offering_id, value))
          }
        />
      )}
      {!figure &&
        !editingLoan &&
        option.missing.includes("eligibility_confirmation") &&
        condition && (
          <EligibilityQuestion
            key={condition.field}
            condition={condition}
            saving={busy}
            onSave={(answer) => saveCondition(condition, answer)}
          />
        )}
      <dl className="kv">
        <div className="contents">
          <dt>Provider</dt>
          <dd>{concept.provider ?? NOT_KNOWN}</dd>
        </div>
        <div className="contents">
          <dt>Start</dt>
          <dd>
            {offering?.start
              ? `${formatDay(offering.start)}${option.supplied.includes("start_date") ? ` (${suppliedLabel})` : ""}`
              : figures?.start
                ? `${formatDay(figures.start.on)} (${figures.start.basis === "stated_intake" ? "your choice of a stated intake" : suppliedLabel})`
                : NOT_KNOWN}
          </dd>
        </div>
        <div className="contents">
          <dt>Finish</dt>
          <dd>
            {offering?.finish
              ? `${formatDay(offering.finish)}${option.supplied.includes("finish_date") ? ` (${suppliedLabel})` : ""}`
              : figures?.finish
                ? `${formatDay(figures.finish)} (${suppliedLabel})`
                : NOT_KNOWN}
          </dd>
        </div>
        <div className="contents">
          <dt>Hours a week</dt>
          <dd>
            {offering?.weekly_hours ?? figures?.weekly_hours ?? NOT_KNOWN}
            {(option.supplied.includes("weekly_hours") ||
              (offering?.weekly_hours == null && figures?.weekly_hours != null)) &&
              ` (${suppliedLabel})`}
          </dd>
        </div>
      </dl>
      <div>
        <h3 className="section-title">What you would pay</h3>
        {plan?.payments?.length ? (
          <ul className="fact-list">
            {plan.payments.map((payment) => (
              <li
                key={`${payment.kind}-${payment.amount.minor_units}-${payment.due}-${payment.month_offset}-${payment.cited.claim_id}`}
              >
                {formatMoney(payment.amount)}{" "}
                {payment.kind === "extra" ? "extra cost" : "course fee"}
                {plan.supplied_cost ? ` (${suppliedLabel})` : ""}
                {payment.due ? `, due ${formatDay(payment.due)}` : ""}
              </li>
            ))}
          </ul>
        ) : (
          <p className="small">
            {figures?.cost
              ? `${formatMoney(figures.cost)} (${suppliedLabel})`
              : plan?.unknown
                ? NOT_KNOWN
                : "No payment stated for this option."}
          </p>
        )}
        {plan?.recurring && (
          <p className="small">
            {formatMoney(plan.recurring.amount)} in repeated payments;{" "}
            {plan.recurring.count === null
              ? "the number of payments is not known yet"
              : `${plan.recurring.count} payments`}
            .
          </p>
        )}
        {typeof quotedCost === "string" && (
          <p className="small">
            Its page quotes {quotedCost}. This does not confirm the total payable or when it is due.
          </p>
        )}
      </div>
      {loan && !editingLoan && (
        <div className="grid gap-4">
          <h3 className="section-title">{FEE_LOAN_KIND[loan.kind ?? "tuition_fee_loan"]}</h3>
          <p>
            {loan.amount ? formatMoney(loan.amount) : NOT_KNOWN}. {LOAN_TO_REPAY}
          </p>
          <p className="small">
            You said: {ELIGIBILITY_STATUS[loan.eligibility].toLowerCase()} about eligibility;{" "}
            {AWARD_STATE[loan.application].toLowerCase()}.
          </p>
        </div>
      )}
      {option.supplied.length > 0 && (
        <p className="small">
          Careerwright used {option.supplied.join(", ").replaceAll("_", " ")} from {suppliedLabel}.
        </p>
      )}
      {suppliedFigures.length > 0 && !editingLoan && (
        <details className="grid gap-8">
          <summary>Change your figures</summary>
          <div className="grid gap-16 pt-12">
            {suppliedFigures.map((current) => (
              <MissingFactBox
                key={`${current.fact}-${JSON.stringify(current)}`}
                fact={current.fact}
                current={current}
                statedIntakes={current.fact === "start_date" ? option.stated_intakes : []}
                primary={false}
                saving={busy}
                onSave={(value) =>
                  void onWrite((stated) => withFigure(stated, option.offering_id, value))
                }
              />
            ))}
          </div>
        </details>
      )}
      {!editingLoan && revisableConditions.length > 0 && (
        <details className="grid gap-8">
          <summary>Change eligibility answers</summary>
          <div className="grid gap-16 pt-12">
            {revisableConditions.map((item) => (
              <EligibilityQuestion
                key={item.field}
                condition={item}
                saving={busy}
                primary={false}
                onSave={(answer) => saveCondition(item, answer)}
              />
            ))}
          </div>
        </details>
      )}
      {concept.kind === "learning" &&
        (editingLoan ? (
          <FeeLoanForm
            current={loan}
            saving={busy}
            onCancel={() => setEditingLoan(false)}
            onSave={(answer) => {
              void onWrite((inputs) =>
                withVariant(inputs, option.variant_id, { tuition_fee_loan: answer }),
              ).then((saved) => {
                if (saved) setEditingLoan(false);
              });
            }}
          />
        ) : (
          <Button variant="secondary" onClick={() => setEditingLoan(true)}>
            {loan ? "Change fee loan answer" : "Tell Careerwright about a fee loan"}
          </Button>
        ))}
      <div className="grid gap-4">
        <Button variant="secondary" onClick={onPin}>
          {pinned ? "Unpin from this screen" : "Pin on this screen"}
        </Button>
        <Button
          variant="secondary"
          disabledReason={busy ? "Saving…" : undefined}
          onClick={() =>
            void onWrite((inputs) => withExcluded(inputs, option.variant_id, !option.left_out))
          }
        >
          {option.left_out ? "Keep this in route searches" : "Leave this out of route searches"}
        </Button>
        {option.left_out && (
          <p className="small">You left this option out. Careerwright still shows it here.</p>
        )}
      </div>
      <details>
        <summary>Sources and conditions</summary>
        <div className="grid gap-8 pt-12">
          <p className="small">
            {concept.cited?.excerpt
              ? `From its source: “${concept.cited.excerpt}”`
              : "Source words are not known yet."}
          </p>
          {concept.cited?.source_url && (
            <a href={concept.cited.source_url} target="_blank" rel="noopener noreferrer nofollow">
              Open source page
            </a>
          )}
          {concept.cited?.retrieved_on && (
            <p className="small">
              Careerwright read this on {formatDay(concept.cited.retrieved_on)}.
            </p>
          )}
          {option.eligibility_conditions.map((condition) => (
            <p key={condition.field} className="small">
              {conditionWords(condition.field, condition.value)}:{" "}
              {condition.status ? ELIGIBILITY_STATUS[condition.status] : NOT_KNOWN}
            </p>
          ))}
          {option.age_rules.map((rule) => (
            <p key={rule.field} className="small">
              {ageRuleWords(rule.value)}
            </p>
          ))}
          {option.age_rules.length > 0 && <p className="small">{AGE_NOT_APPLIED}</p>}
        </div>
      </details>
    </section>
  );
}

export function OptionsScreen({
  workspaceId,
  options,
  checkpoint,
  inputs,
  busy,
  onWrite,
  onAdd,
  failure,
}: {
  workspaceId: string;
  options: OptionsOut;
  checkpoint: CheckpointOut;
  inputs: PlanningInputsDocument;
  busy: boolean;
  onWrite: Action;
  onAdd(target: string, value: AddedOption): Promise<string | null>;
  failure: unknown;
}) {
  const [chosenTarget, setChosenTarget] = useState<string | null>(null);
  const [chosenVariant, setChosenVariant] = useState<string | null>(null);
  const [pinned, setPinned] = useState<ReadonlySet<string>>(new Set());
  const [view, setView] = useState<"options" | "checkpoint" | "add">("options");
  const [editing, setEditing] = useState<NeededInput | null>(null);
  const target =
    checkpoint.targets.find((item) => item.target_title === chosenTarget) ?? checkpoint.targets[0];
  const catalogue = options.targets.find(
    (item) => item.target_title === target?.target_title,
  )?.catalogue;
  const selected =
    target?.options.find((item) => item.variant_id === chosenVariant) ?? target?.options[0];
  const concept = catalogue?.concepts.find((item) => item.concept_id === selected?.concept_id);
  const offering = catalogue?.offerings.find((item) => item.offering_id === selected?.offering_id);
  const variant = catalogue?.variants.find((item) => item.variant_id === selected?.variant_id);
  const nextNeed = checkpoint.needs.find(
    (need) => need.input !== "direct_spend_cap" && need.input !== "monthly_payment_cap",
  );
  return (
    <div className="chapter-layout">
      <div className="chapter-reading">
        <header className="chapter-heading">
          <h1 className="page-title">Options</h1>
          <p>Find a way to build what you need. Check the missing facts before searching routes.</p>
        </header>
        {failure ? <RequestFailure error={failure} /> : null}
        <fieldset className="flex flex-wrap gap-8">
          <legend className="sr-only">Options view</legend>
          <Button
            variant={view === "options" ? "choice" : "secondary"}
            aria-pressed={view === "options"}
            onClick={() => setView("options")}
          >
            Explore options
          </Button>
          <Button
            variant={view === "checkpoint" ? "choice" : "secondary"}
            aria-pressed={view === "checkpoint"}
            onClick={() => setView("checkpoint")}
          >
            Before a route search
            {checkpoint.needs.length > 0 ? ` (${checkpoint.needs.length})` : ""}
          </Button>
          {target && (
            <Button
              variant={view === "add" ? "choice" : "secondary"}
              aria-pressed={view === "add"}
              onClick={() => setView("add")}
            >
              Add your own option
            </Button>
          )}
        </fieldset>
        {checkpoint.targets.length === 0 ? (
          <p>Choose a target in You to see options for it.</p>
        ) : view === "add" && target ? (
          <AddOptionForm
            target={target.target_title}
            saving={busy}
            onCancel={() => setView("options")}
            onSave={async (value) => {
              const id = await onAdd(target.target_title, value);
              if (id !== null) {
                setChosenVariant(id);
                setView("options");
              }
              return id;
            }}
          />
        ) : view === "options" ? (
          <div className="grid gap-24">
            {checkpoint.targets.length > 1 && (
              <fieldset className="flex flex-wrap gap-8">
                <legend className="sr-only">Target role</legend>
                {checkpoint.targets.map((item) => (
                  <Button
                    key={item.target_title}
                    variant={item.target_title === target?.target_title ? "choice" : "secondary"}
                    aria-pressed={item.target_title === target?.target_title}
                    onClick={() => {
                      setChosenTarget(item.target_title);
                      setChosenVariant(null);
                    }}
                  >
                    {item.target_title}
                  </Button>
                ))}
              </fieldset>
            )}
            {target && (
              <section className="grid gap-16" aria-labelledby="options-target">
                <h2 id="options-target" className="section-title">
                  For {target.target_title}
                </h2>
                {target.reviewed_options === 0 && (
                  <p>
                    No reviewed option found yet. That does not mean there are none. You can add one
                    you know about.
                  </p>
                )}
                {target.scope.code === "retain_variants" && (
                  <p role="status">
                    Careerwright has {target.scope.concepts} options (limit{" "}
                    {target.scope.max_concepts}) and up to {target.scope.most_starts} starts for one
                    option (limit {target.scope.max_starts}). Leave out some options to narrow the
                    route search; nothing has been hidden.
                  </p>
                )}
                {target.options.length > 0 && catalogue ? (
                  selected &&
                  concept && (
                    <OptionDetail
                      key={selected.variant_id}
                      workspaceId={workspaceId}
                      option={selected}
                      concept={concept}
                      offering={offering}
                      variant={variant}
                      inputs={inputs}
                      pinned={pinned.has(selected.variant_id)}
                      onPin={() =>
                        setPinned((current) => {
                          const next = new Set(current);
                          if (next.has(selected.variant_id)) next.delete(selected.variant_id);
                          else next.add(selected.variant_id);
                          return next;
                        })
                      }
                      busy={busy}
                      onWrite={onWrite}
                    />
                  )
                ) : (
                  <div className="grid gap-8">
                    <p>No bridge found yet. That does not mean there are none.</p>
                    <div>
                      <Button variant="secondary" onClick={() => setView("add")}>
                        Add an option you know
                      </Button>
                    </div>
                  </div>
                )}
              </section>
            )}
            {target && options.data_mode !== "demo" && (
              <OptionResearch
                key={target.target_title}
                workspaceId={workspaceId}
                target={target.target_title}
              />
            )}
            {target && target.schemes.length > 0 && (
              <details>
                <summary>Funding that may apply to this target</summary>
                <div className="grid gap-8 pt-12">
                  {target.schemes.map((scheme) => (
                    <p key={scheme.instrument_id} className="small">
                      {catalogue?.instruments?.find(
                        (item) => item.instrument_id === scheme.instrument_id,
                      )?.programme ?? INSTRUMENT_KIND[scheme.kind]}
                      . {RECORD_STATE[scheme.review_state]}.{" "}
                      {scheme.age_rules.length > 0
                        ? `${scheme.age_rules.map((rule) => ageRuleWords(rule.value)).join("; ")}. ${AGE_NOT_APPLIED}`
                        : "Age rule not stated."}
                    </p>
                  ))}
                </div>
              </details>
            )}
          </div>
        ) : (
          <section className="grid gap-16" aria-label="Review before a route search">
            {editing ? (
              <PlanningQuestion
                key={`edit-${editing}`}
                need={{ input: editing, effect: "blocks_a_solve" }}
                current={inputs}
                editing
                saving={busy}
                onSave={async (update) => {
                  const saved = await onWrite(update);
                  if (saved) setEditing(null);
                  return saved;
                }}
                onCancel={() => setEditing(null)}
              />
            ) : (
              <>
                {checkpoint.not_working && <p>{notWorkingWords}</p>}
                {checkpoint.payment_cap_basis && (
                  <p className="small">{paymentCapMeaning(checkpoint.payment_cap_basis)}</p>
                )}
                {checkpoint.needs.length === 0 ? (
                  <div className="grid gap-8">
                    <p>Careerwright has the answers it needs to try a route search.</p>
                    <div>
                      <Link className="btn btn-primary" href={chapterHref(workspaceId, "routes")}>
                        Open Routes
                      </Link>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="small">
                      Careerwright still needs{" "}
                      {checkpoint.needs
                        .map((need) => NEEDED_INPUT[need.input].name.toLowerCase())
                        .join(", ")}
                      .
                    </p>
                    {nextNeed ? (
                      <PlanningQuestion
                        key={nextNeed.input}
                        need={nextNeed}
                        current={inputs}
                        saving={busy}
                        onSave={onWrite}
                      />
                    ) : (
                      <p>
                        The spending limits are answered in{" "}
                        <Link href={chapterHref(workspaceId, "you")}>You</Link>.
                      </p>
                    )}
                  </>
                )}
                <PlanningAnswers inputs={inputs} onChange={setEditing} />
              </>
            )}
          </section>
        )}
        <details className="place-more chapter-secondary">
          <summary>About these option records</summary>
          <p className="small muted">{packLine(checkpoint.pack.dated)}</p>
        </details>
      </div>
      {target && (
        <aside
          className="chapter-landscape options-landscape"
          aria-labelledby="option-landscape-title"
        >
          <header className="chapter-heading">
            <h2 id="option-landscape-title">Ways toward {target.target_title.toLowerCase()}</h2>
            <p>Select an option to check its cost, dates and entry requirements.</p>
          </header>
          <div className="option-destination">
            <span aria-hidden="true" />
            {target.target_title}
          </div>
          <fieldset className="option-choice-list">
            <legend className="sr-only">Options to inspect</legend>
            {[...target.options]
              .sort((a, b) => Number(pinned.has(b.variant_id)) - Number(pinned.has(a.variant_id)))
              .map((option) => {
                const item = catalogue?.concepts.find(
                  (candidate) => candidate.concept_id === option.concept_id,
                );
                const start = catalogue?.offerings.find(
                  (candidate) => candidate.offering_id === option.offering_id,
                );
                const supplied = inputs.offering_figures?.find(
                  (candidate) => candidate.offering_id === option.offering_id,
                );
                const hours = start?.weekly_hours ?? supplied?.weekly_hours;
                const begins = start?.start ?? supplied?.start?.on;
                return (
                  <Button
                    key={option.variant_id}
                    variant={option.variant_id === selected?.variant_id ? "choice" : "secondary"}
                    aria-pressed={option.variant_id === selected?.variant_id}
                    className="option-path-node"
                    onClick={() => {
                      setChosenVariant(option.variant_id);
                      setView("options");
                    }}
                  >
                    <span className="option-path-kind">
                      {item ? ACTION_KIND[item.kind] : "Option type not known"}
                    </span>
                    <strong>{item?.title ?? "Unnamed option"}</strong>
                    {hours != null && (
                      <span>
                        {hours}h / week
                        {option.supplied.includes("weekly_hours") ||
                        (start?.weekly_hours == null && supplied?.weekly_hours != null)
                          ? ` (${suppliedLabel})`
                          : ""}
                      </span>
                    )}
                    {begins && (
                      <span>
                        Starts {formatMonth(begins)}
                        {option.supplied.includes("start_date") ||
                        (start?.start == null && supplied?.start)
                          ? ` (${supplied?.start?.basis === "stated_intake" ? "your choice of a stated intake" : suppliedLabel})`
                          : ""}
                      </span>
                    )}
                    <span>{optionState(option)}</span>
                    <span>
                      {option.missing.length > 0
                        ? `${option.missing.length} ${option.missing.length === 1 ? "fact" : "facts"} to confirm`
                        : "No missing planning facts"}
                    </span>
                    {pinned.has(option.variant_id) && <span>pinned on this screen</span>}
                    {option.left_out && <span>Left out of route searches</span>}
                  </Button>
                );
              })}
          </fieldset>
          {target.options.length === 0 && (
            <p>No option checked yet. Add one you know or research this target.</p>
          )}
          <p className="decision-map-note">
            An option is a possible bridge, not a place booked or a confirmed outcome. Unknown facts
            stay unresolved in route searches.
          </p>
        </aside>
      )}
    </div>
  );
}

export function OptionsChapter({ workspaceId }: { workspaceId: string }) {
  const options = usePlanningOptions(workspaceId);
  const checkpoint = useCheckpoint(workspaceId);
  const inputs = usePlanningInputs(workspaceId);
  const write = useWritePlanningInputs(workspaceId);
  const paste = usePasteOptionText(workspaceId);
  const reads = [options, checkpoint, inputs];
  const failed = reads.find((item) => item.data === undefined && item.error);
  if (failed)
    return (
      <div className="chapter-reading">
        <h1 className="page-title">Options</h1>
        <RequestFailure
          error={failed.error}
          actions={
            <Button onClick={() => void Promise.all(reads.map((item) => item.refetch()))}>
              Try again
            </Button>
          }
        />
      </div>
    );
  if (!options.data || !checkpoint.data || !inputs.data)
    return (
      <div className="chapter-reading">
        <h1 className="page-title">Options</h1>
        <LoadingState stage="Loading options" />
      </div>
    );
  const save: Action = async (update) => {
    const current = inputs.data;
    try {
      await write.mutateAsync({
        expected_version: current.version,
        inputs: update(submitted(current.inputs)),
      });
      return true;
    } catch {
      // The mutation keeps its error for RequestFailure in the chapter.
      return false;
    }
  };
  const add = async (target: string, value: AddedOption): Promise<string | null> => {
    try {
      const source = value.text ? await paste.mutateAsync({ text: value.text }) : null;
      const optionId = crypto.randomUUID();
      const current = inputs.data;
      const stated = submitted(current.inputs);
      await write.mutateAsync({
        expected_version: current.version,
        inputs: {
          ...stated,
          own_options: [
            ...(stated.own_options ?? []),
            {
              option_id: optionId,
              target,
              kind: value.kind,
              text_id: source?.text_id ?? null,
              title: { typed: value.title },
              provider: value.provider ? { typed: value.provider } : null,
            },
          ],
        },
      });
      return `own:${optionId}`;
    } catch {
      // The failed command remains visible through RequestFailure.
      return null;
    }
  };
  return (
    <OptionsScreen
      workspaceId={workspaceId}
      options={options.data}
      checkpoint={checkpoint.data}
      inputs={inputs.data.inputs}
      busy={write.isPending || paste.isPending}
      onWrite={save}
      onAdd={add}
      failure={paste.error ?? write.error}
    />
  );
}
