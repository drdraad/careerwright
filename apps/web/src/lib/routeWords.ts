import type {
  Comparator,
  Condition,
  Finding,
  FindingCode,
  Lead,
  Narrowing,
  Qualification,
  RouteQualification,
  Verdict,
} from "@/generated/api";
import { formatMonth } from "./dates";
import { formatMoney, formatSignedMoney } from "./money";

export const ROUTE_LEAD: Record<Lead, string> = {
  best_trade_offs_found: "Best trade-offs found",
  none_found_before_limit: "No route found before the search limit",
  unresolved: "Careerwright still needs some facts",
  longer_than_model: "This option is longer than Careerwright can plan yet",
  no_route_in_bounded_model: "No route fits within this monthly model",
};

export const NARROWING: Record<Narrowing, string> = {
  fewer_concepts: "keep fewer options in the search",
  one_start: "choose one start for each option",
  shorter_horizon: "compare fewer months",
};

export const ROUTE_VERDICT: Record<Verdict, string> = {
  affordable_and_feasible: "Fits your stated limits in this monthly model",
  affordable_and_feasible_with_qualifications:
    "Fits your stated limits in this monthly model, with qualifications",
  readiness_not_reached_in_this_model: "Does not reach this target within this model",
  unresolved: "Careerwright cannot settle this route yet",
  not_feasible_in_this_model: "Does not fit your stated limits in this monthly model",
};

export const ROUTE_CONDITION: Record<Condition["verification"], string> = {
  confirm_offer_accepted: "Needs a job offer you accept",
  verify_funding_award: "Needs the funding to be awarded",
  confirm_admission: "Needs a place to be confirmed",
  confirm_loan_approved: "Needs the loan to be approved and repaid later",
};

export function comparatorWords(comparator: Comparator): string {
  const months = comparator.months_sooner;
  const cost = formatMoney(comparator.cost_less);
  const other = `Point ${comparator.point_id}`;
  switch (comparator.dominance) {
    case "sooner_and_cheaper":
      return `${other} is ${months} ${months === 1 ? "month" : "months"} sooner and ${cost} cheaper.`;
    case "sooner_same_cost":
      return `${other} is ${months} ${months === 1 ? "month" : "months"} sooner at the same cost.`;
    case "cheaper_same_time":
      return `${other} costs ${cost} less for the same time.`;
  }
}

export const FINDING: Record<FindingCode, string> = {
  direct_spend_cap: "Above your total spending limit",
  monthly_payment_cap: "Above your monthly payment limit",
  monthly_deficit_cap: "More than the monthly shortfall you allowed",
  reserve: "Would leave less cash than you want to keep",
  workload: "More hours than you said you can give",
  session_clash: "Two steps need the same time",
  prerequisite_not_usable: "A required step is not finished in time",
  application_too_late: "The application would be too late",
  starts_before_planning: "Starts before this plan begins",
  one_start_per_concept: "The same option starts twice",
  exclusive_group: "Two options cannot be taken together",
  conflicting_work_patterns: "The work patterns clash",
  coarse_model_unresolved: "The monthly model cannot settle this",
  dates_unknown: "Start or finish date not known yet",
  cost_unknown: "Cost not known yet",
  workload_unknown: "Hours a week not known yet",
  entry_requirements_unconfirmed: "Entry requirements need your answer",
  baseline_missing: "What you would do instead is not known yet",
  limit_unknown: "A spending limit is not known yet",
  payment_before_start: "A payment is due before the step starts",
  economic_cost_cap: "Above your preferred total cost",
  entry_requirements_not_met: "An entry requirement is not met",
  eligibility_unconfirmed: "Funding conditions need your answer",
  stacking_unconfirmed: "Using these funding schemes together is not confirmed",
  work_rights_unknown: "Your right to work is not known yet",
  work_rights_not_held: "You said you would need a visa to work",
  repayments_above_payment_cap: "Your existing repayments exceed your monthly payment limit",
  job_transitions: "Too many job changes for this model",
  scheme_shared_unconfirmed: "This funding scheme may be shared with another step",
  exclusive_schemes: "These funding schemes cannot be used together",
  loan_amount_unknown: "The amount of the loan is not known yet",
  entry_requirements_expected: "If you get your grades, this entry requirement may be met",
};

export const ROUTE_QUALIFICATION: Record<RouteQualification | Qualification, string> = {
  proposed_records: "An option has not been reviewed",
  accepted_assumptions: "Uses an assumption you accepted",
  synthetic: "Uses made-up demo data",
  conditional_offer: "Needs a job offer",
  conditional_award: "Needs a funding award",
  conditional_application: "Needs an accepted application",
  conditional_loan: "Needs a loan to be approved",
  readiness_not_assessed: "Skills have not been assessed for this target",
  supplied_figures: "Uses a figure you supplied that has not been checked",
  own_options: "Uses an option you added that has not been reviewed",
  provisional_matrix: "Skills assessment is provisional",
  proposed_rubrics: "Uses a skills measure that has not been reviewed",
  self_reported_evidence: "Uses what you said about your skills",
  planned_outcome_assumption: "Assumes a planned step gives you a skill",
  user_assumption: "Uses an assumption you gave",
  missing_outcome_level: "The level a course teaches is not known yet",
  person_confirmed_demonstration: "Uses a skill example you confirmed",
  person_confirmed_verification: "Uses a check you confirmed",
  open_conflict: "The evidence still disagrees",
};

export function findingWords(finding: Finding): string {
  const detail =
    finding.amount == null || finding.limit == null || finding.unit == null
      ? ""
      : finding.unit === "minor_units"
        ? `: ${formatSignedMoney({ minor_units: finding.amount, currency: "GBP" })} against ${formatMoney({ minor_units: finding.limit, currency: "GBP" })}`
        : `: ${finding.amount} hours against ${finding.limit} hours`;
  return `${FINDING[finding.code]}${detail}${finding.month ? ` in ${formatMonth(`${finding.month}-01`)}` : ""}.`;
}
