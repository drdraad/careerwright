"use client";

import { useEffect, useRef, useState } from "react";
import type {
  CheckpointOut,
  PlanSnapshot,
  ProfileOut,
  RouteDetail,
  SkillsOut,
} from "@/generated/api";
import { formatDay, formatMonth } from "@/lib/dates";
import { formatMoney, formatSignedMoney } from "@/lib/money";
import { missingLine, NOT_KNOWN } from "@/lib/optionWords";
import { describeQualification } from "@/lib/profile";
import { ROUTE_QUALIFICATION } from "@/lib/routeWords";
import { useWorldSettings } from "@/lib/world/settings";
import { Button } from "./Button";
import { DecisionAtmosphere } from "./DecisionAtmosphere";
import { RouteJourney } from "./RouteJourney";
import "./careerWorkspace.css";

type Props = {
  routes: RouteDetail[];
  skills: SkillsOut;
  plan: PlanSnapshot;
  checkpoint: CheckpointOut;
  profile: ProfileOut;
};

const month = (value: string) => formatMonth(`${value}-01`);
const mode = (route: RouteDetail) => (route.schedule.index === 0 ? "Full-time" : "Part-time");

export function DecisionProposal({ routes, skills, plan, checkpoint, profile }: Props) {
  const world = useWorldSettings();
  const [view, setView] = useState<"skills" | "routes" | "plan">("routes");
  const [selectedIndex, setSelectedIndex] = useState(plan.source.schedule_index);
  const [preview, setPreview] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const previousView = useRef(view);
  useEffect(() => {
    if (previousView.current !== view) heading.current?.focus({ preventScroll: true });
    previousView.current = view;
  }, [view]);
  const selected = routes.find((route) => route.schedule.index === selectedIndex) ?? routes[0];
  const target = skills.targets[0];
  if (!selected || !target) return null;
  const saved = selected.schedule.index === plan.source.schedule_index;
  const shownRoute = view === "plan" && !preview ? plan.route : selected;
  const step = shownRoute.steps[0];
  const completed = plan.progress?.completed_steps ?? [];
  const missingOptions = checkpoint.targets
    .flatMap((item) => item.options)
    .filter((option) => option.missing.includes("cost"));
  const qualifications = profile.document.qualifications;
  const activeMonth = selected.months.find((row) =>
    selected.steps[0]?.active_months.includes(row.month),
  );

  function openSavedPlan() {
    setSelectedIndex(plan.source.schedule_index);
    setPreview(false);
    setView("plan");
  }

  return (
    <div className="decision-proposal" data-still={world.reduced || world.calm || world.paused}>
      <div className="decision-demo-banner">
        <strong>Synthetic demo</strong>
        <span>
          Made-up profile and planning assumptions. Course source records remain labelled.
        </span>
        <a href="?id=design-proposal-p01-decision--three-targets&viewMode=story">
          Three-target example
        </a>
      </div>
      <header className="decision-shell-header">
        <a className="decision-brand" href="#decision-content">
          <span className="decision-brand-mark" aria-hidden="true" /> Careerwright
        </a>
        <DecisionAtmosphere settings={world} />
        <div className="decision-target">
          <span>Your target</span>
          <strong>{target.target_title}</strong>
        </div>
      </header>
      <nav className="decision-chapters" aria-label="Your career chapters">
        <span className="decision-context-chapter">You</span>
        <span className="decision-context-chapter">Roles</span>
        <Button
          className="decision-chapter"
          aria-current={view === "skills" ? "page" : undefined}
          onClick={() => setView("skills")}
        >
          Skills
        </Button>
        <span className="decision-context-chapter">Options</span>
        <Button
          className="decision-chapter"
          aria-current={view === "routes" ? "page" : undefined}
          onClick={() => setView("routes")}
        >
          Routes
        </Button>
        <Button
          className="decision-chapter"
          aria-current={view === "plan" ? "page" : undefined}
          onClick={openSavedPlan}
        >
          Plan
        </Button>
      </nav>
      <main id="decision-content" className="decision-layout">
        <section className="decision-reading" aria-labelledby="decision-title">
          {view === "routes" && (
            <>
              <header className="decision-page-heading">
                <h1 id="decision-title" ref={heading} tabIndex={-1}>
                  Compare your routes
                </h1>
                <p>Study faster, or keep more of your pay.</p>
              </header>
              <div className="decision-caution">
                <strong>SQL is still unresolved.</strong>
                <p>Both routes assume an assessed outcome the provider has not confirmed.</p>
              </div>
              <fieldset className="decision-route-picker" aria-label="Compare routes">
                {routes.map((route) => (
                  <Button
                    key={route.schedule.index}
                    className="decision-route-option"
                    aria-pressed={selectedIndex === route.schedule.index}
                    onClick={() => setSelectedIndex(route.schedule.index)}
                  >
                    <span className="decision-route-mode">
                      <span>Route {route.schedule.index + 1}</span> <strong>{mode(route)}</strong>{" "}
                      {route.schedule.index === plan.source.schedule_index && (
                        <span>Saved plan</span>
                      )}
                    </span>{" "}
                    <span className="decision-route-date">
                      <strong>{month(route.schedule.readiness_month)}</strong>{" "}
                      <span>{route.schedule.months_to_readiness}-month route</span>
                      <span>
                        {route.steps[0]?.weekly_hours}h study +{" "}
                        {route.steps[0]?.work_pattern?.hours_per_week}h work / week
                      </span>{" "}
                    </span>{" "}
                    <span className="decision-route-cost">
                      <strong>{formatSignedMoney(route.schedule.objective_cost)}</strong>{" "}
                      <span>Modelled cost</span>
                      <span>
                        {route.costs.pay_difference?.minor_units === 0
                          ? "Keeps your stated pay"
                          : route.costs.pay_difference
                            ? `${formatSignedMoney(route.costs.pay_difference)} lost pay`
                            : "Pay impact unknown"}
                      </span>
                    </span>
                  </Button>
                ))}
              </fieldset>
              <Button
                className="decision-primary"
                onClick={() => {
                  if (saved) openSavedPlan();
                  else {
                    setPreview(true);
                    setView("plan");
                  }
                }}
              >
                {saved ? "Review saved plan" : "Preview this plan"}
              </Button>
              <p className="decision-action-note">
                {saved
                  ? "Route 2 is your saved choice. Nothing is booked."
                  : "A local preview. Your saved choice stays Route 2."}
              </p>
              <h2 className="decision-route-title">
                {selected.steps[0]?.title ?? "Learning route"}
              </h2>
              <dl className="decision-facts">
                <div>
                  <dt>Pay lost against continuing work</dt>
                  <dd>
                    {selected.costs.pay_difference === null
                      ? NOT_KNOWN
                      : formatSignedMoney(selected.costs.pay_difference)}
                    <span>Included in the economic cost above</span>
                  </dd>
                </div>
                <div>
                  <dt>Take-home pay while studying</dt>
                  <dd>
                    {activeMonth?.route_income
                      ? `${formatMoney(activeMonth.route_income)} / month`
                      : NOT_KNOWN}
                    <span>From your supplied work pattern</span>
                  </dd>
                </div>
                <div>
                  <dt>Course fee used in this model</dt>
                  <dd>
                    {selected.costs.direct_cost === null
                      ? NOT_KNOWN
                      : formatMoney(selected.costs.direct_cost)}
                    <span>Your supplied figure, not checked. Provider quote not known yet.</span>
                  </dd>
                </div>
              </dl>
              <p className="decision-model-basis">
                Compared over {selected.basis.horizon_months} months from{" "}
                {month(selected.basis.planning_start)}, against continuing your supplied work
                pattern.
              </p>
              <details className="decision-disclosure">
                <summary>
                  Assumptions and sources ({selected.schedule.qualifications.length})
                </summary>
                <ul className="decision-source-list">
                  {selected.schedule.qualifications.map((reason) => (
                    <li key={reason}>{ROUTE_QUALIFICATION[reason]}.</li>
                  ))}
                </ul>
                <p>
                  Catalogue: {selected.label.name}, dated {formatDay(selected.label.dated)}.
                </p>
                <p>
                  These are qualifications on the model's result, not qualifications you have
                  achieved. Readiness in this model does not guarantee a job.
                </p>
                <dl className="decision-facts">
                  <div>
                    <dt>Your monthly payment limit</dt>
                    <dd>
                      {checkpoint.monthly_payment_cap
                        ? formatMoney(checkpoint.monthly_payment_cap)
                        : NOT_KNOWN}
                    </dd>
                  </div>
                  <div>
                    <dt>Cash you want to keep</dt>
                    <dd>
                      {selected.costs.reserve ? formatMoney(selected.costs.reserve) : NOT_KNOWN}
                    </dd>
                  </div>
                </dl>
                {selected.steps.map((routeStep) => {
                  const source = routeStep.sources.find((citation) => citation.source_url);
                  return source ? (
                    <p key={routeStep.variant_id}>
                      <a
                        href={source.source_url ?? undefined}
                        target="_blank"
                        rel="noopener noreferrer nofollow"
                      >
                        {routeStep.provider ?? "Provider"}: course source
                      </a>
                      {source.retrieved_on ? ` · Read ${formatDay(source.retrieved_on)}` : ""}.
                      Source records have not been reviewed.
                    </p>
                  ) : (
                    <p key={routeStep.variant_id}>No provider source recorded.</p>
                  );
                })}
              </details>
            </>
          )}
          {view === "skills" && (
            <>
              <header className="decision-page-heading">
                <p className="decision-context">Skills for {target.target_title.toLowerCase()}</p>
                <h1 id="decision-title" ref={heading} tabIndex={-1}>
                  What your evidence tells us
                </h1>
                <p>Your examples support two skills. SQL remains a gap.</p>
              </header>
              <div className="decision-caution">
                <strong>A provisional skills checklist</strong>
                <p>
                  Your answers are self-reported. The checklist and course outcomes still need
                  review.
                </p>
              </div>
              <ul className="decision-skill-list">
                {target.requirements.map((requirement) => {
                  const answer = requirement.latest_skill;
                  const reported =
                    answer &&
                    ["done_independently", "done_with_help", "used"].includes(answer.answer);
                  return (
                    <li className="decision-skill-row" key={requirement.row_id}>
                      <div>
                        <h2>{requirement.label}</h2>
                        <span
                          className={`decision-evidence-label ${reported ? "decision-self-reported" : "decision-unresolved"}`}
                        >
                          {reported ? "Self-reported evidence" : "Unresolved"}
                        </span>
                      </div>
                      {reported ? (
                        <details className="decision-disclosure">
                          <summary>Read your saved example</summary>
                          <blockquote>{answer.example ?? "No example saved."}</blockquote>
                          {answer.last_done && <p>Last used: {month(answer.last_done)}.</p>}
                          <p>Your own answer; not independently verified.</p>
                        </details>
                      ) : (
                        <p>
                          {answer?.answer === "not_learned"
                            ? "You said you have not learned this yet."
                            : "No usable evidence yet."}{" "}
                          The routes use a hypothetical assessed SQL outcome.
                        </p>
                      )}
                    </li>
                  );
                })}
              </ul>
              {qualifications.state === "provided" &&
                qualifications.value &&
                qualifications.value.length > 0 && (
                  <details className="decision-disclosure">
                    <summary>Your qualifications</summary>
                    <ul>
                      {qualifications.value.map((qualification) => (
                        <li key={qualification.name}>{describeQualification(qualification)}</li>
                      ))}
                    </ul>
                    <p>Expected qualifications are not counted as achieved.</p>
                  </details>
                )}
              <Button className="decision-primary" onClick={() => setView("routes")}>
                Compare routes for SQL
              </Button>
              {missingOptions.length > 0 && (
                <details className="decision-disclosure">
                  <summary>Other options: facts still missing</summary>
                  <p>
                    {missingOptions.length} other{" "}
                    {missingOptions.length === 1 ? "option has" : "options have"} an unknown cost.
                    These are separate from the supplied £0 fee used in the two routes.
                  </p>
                  <ul>
                    {missingOptions.map((option, index) => (
                      <li key={option.variant_id}>
                        Option {index + 1}: {missingLine(option.missing)}
                      </li>
                    ))}
                  </ul>
                  <p>Unknown costs remain unknown; they are never treated as £0.</p>
                </details>
              )}
            </>
          )}
          {view === "plan" && (
            <>
              <header className="decision-page-heading">
                <p className="decision-context">
                  {preview ? "Local preview · not saved" : "Saved plan · Route 2"}
                </p>
                <h1 id="decision-title" ref={heading} tabIndex={-1}>
                  {preview ? "A look at the full-time plan" : "Your next step, kept in view"}
                </h1>
                <p>
                  {preview
                    ? "Explore this route without changing your saved plan."
                    : `${mode(plan.route)} study towards ${plan.target_title.toLowerCase()}.`}
                </p>
              </header>
              <div className="decision-progress">
                <strong>
                  {preview ? 0 : completed.length} / {shownRoute.steps.length}
                </strong>
                <span>steps reported complete</span>
              </div>
              <div className="decision-next-action">
                <span>{preview ? "Before taking this route" : "Next action"}</span>
                <h2>Confirm the course with {step?.provider ?? "the provider"}</h2>
                <p>
                  Proposed course start:{" "}
                  {preview
                    ? step?.start_date
                      ? formatDay(step.start_date)
                      : step?.start_month
                        ? month(step.start_month)
                        : NOT_KNOWN
                    : plan.next_action
                      ? formatDay(plan.next_action.on)
                      : NOT_KNOWN}
                </p>
                <p>Confirm the place, timetable, fee and assessed SQL outcome with the provider.</p>
              </div>
              <ol className="decision-plan-steps">
                {shownRoute.steps.map((routeStep) => (
                  <li className="decision-plan-step" key={routeStep.variant_id}>
                    <strong>{routeStep.title}</strong>
                    <span>
                      {routeStep.start_month ? month(routeStep.start_month) : NOT_KNOWN} to{" "}
                      {routeStep.finish_month ? month(routeStep.finish_month) : NOT_KNOWN}
                    </span>
                    <span>
                      {!preview && completed.includes(routeStep.variant_id)
                        ? "Reported complete"
                        : "Not reported complete"}
                    </span>
                  </li>
                ))}
              </ol>
              <div className="decision-caution">
                <strong>SQL is still unresolved.</strong>
                <p>
                  Planned learning and reported completion do not verify a skill. No place or
                  booking is confirmed here.
                </p>
              </div>
              <Button className="decision-primary" onClick={() => setView("routes")}>
                Back to route comparison
              </Button>
              {preview && (
                <Button className="decision-text-button" onClick={openSavedPlan}>
                  Return to your saved plan
                </Button>
              )}
            </>
          )}
        </section>
        <aside className="decision-map" aria-label="Your route map">
          <div className="decision-map-heading">
            <span>
              {view === "plan"
                ? preview
                  ? "Plan preview"
                  : "Saved route"
                : "Your possible routes"}
            </span>
            <h2>{target.target_title}</h2>
            <p>Select a route to compare it.</p>
          </div>
          <RouteJourney
            routes={routes}
            selectedIndex={shownRoute.schedule.index}
            onSelect={(index) => {
              setSelectedIndex(index);
              setView("routes");
            }}
            targetTitle={target.target_title}
            startLabel={`You in ${month(selected.basis.planning_start)}`}
            planIndex={plan.source.schedule_index}
            completedSteps={completed}
          />
          <p className="decision-map-note">
            A path through the monthly model. Each endpoint assumes the SQL outcome; it is not
            verified readiness or a job offer.
          </p>
        </aside>
      </main>
    </div>
  );
}
