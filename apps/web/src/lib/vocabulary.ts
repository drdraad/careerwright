// How the shared state vocabulary reads in the UI (STATE-01, UI-04). The values come only from
// the generated client; these tables give each one words and a glyph. `Record<…>` over the
// generated unions makes a new API value a compile error here until it has words.

import type { GlyphName } from "@/components/Glyph";
import type {
  AiResilienceFilterOut,
  BudgetScope,
  ConversationMode,
  DataMode,
  Direction,
  Emphasis,
  EmptyReason,
  EntryMode,
  ErrorCode,
  FailureClass,
  FieldState,
  FloorUnknown,
  ModelExtractionState,
  NotIncluded,
  PartialCompleteness,
  PayPeriod,
  ProfileField,
  ProfileInput,
  RecordPart,
  Resolution,
  SalaryFloorOut,
  SearchDid,
  SearchEmptyReason,
  SketchOut,
  SlateOut,
  Step,
  SuggestionOut,
  TargetCoverage,
  WorkState,
} from "@/generated/api";
import { listLimit } from "./bounds";
import { formatMoney } from "./money";
import type { UsdInputProblem } from "./usd";

/** Only error and stale add a hue; everything else is carried by glyph and words. */
export type Tone = "neutral" | "unknown" | "stale" | "error";

/** Where a reached spending limit can be raised: the spending line (`ModelSpending`). */
export const RAISE_THE_LIMIT =
  "You can raise the limit under Model spending, in the Account and settings menu.";

/** The spending line in the account menu (MODEL-10). Amounts are in US dollars, as Meta bills. */
export const SPENDING = {
  heading: "Model spending",
  spent: (spent: string, limit: string) => `${spent} of ${limit} spent this month`,
  perRun: (limit: string) => `Each run can use up to ${limit}.`,
  unknown: (calls: number) =>
    calls === 1
      ? "Meta didn't report the cost of 1 call, so Careerwright counts it at its most."
      : `Meta didn't report the cost of ${calls} calls, so Careerwright counts each at its most.`,
  demo: "This demo workspace never calls a model, so it spends nothing.",
  dollars: "Meta bills in US dollars.",
  change: "Change",
  monthLabel: "Monthly limit, in US dollars",
  runLabel: "Most for one run, in US dollars",
  save: "Save limits",
  cancel: "Cancel",
  saved: "Saved.",
} as const;

/** Why a typed dollar amount can't be used (`parseUsdInput`). */
export const USD_INPUT_PROBLEM: Record<UsdInputProblem, string> = {
  empty: "Enter an amount.",
  negative: "Enter an amount of zero or more.",
  not_a_number: "Enter an amount in dollars, such as 5 or 0.75.",
  too_precise: "Use at most two digits after the point.",
  too_large: "Enter a smaller amount.",
};

/** What a run may cost before the person starts it (`RunEstimate`; spec section 16). */
export const RUN_ESTIMATE = {
  costs: (most: string) => `This can cost up to ${most} on your Meta key.`,
  restart: (hard: string) => `If it has to restart, never more than ${hard}.`,
  free: "This uses the demo's stand-in, so it costs nothing.",
  refused: {
    run: `It needs more than this workspace's limit for one run. ${RAISE_THE_LIMIT}`,
    period: `This month's spending limit doesn't leave room for it. ${RAISE_THE_LIMIT}`,
  } satisfies Record<BudgetScope, string>,
} as const;

export type StatePresentation = { label: string; glyph: GlyphName; tone: Tone };

export const WORK_STATE: Record<WorkState, StatePresentation> = {
  draft: { label: "Draft", glyph: "draft", tone: "neutral" },
  queued: { label: "Queued", glyph: "queued", tone: "neutral" },
  running: { label: "Running", glyph: "running", tone: "neutral" },
  partial: { label: "Partial results", glyph: "partial", tone: "neutral" },
  complete: { label: "Complete", glyph: "complete", tone: "neutral" },
  cancelled: { label: "Cancelled", glyph: "cancelled", tone: "neutral" },
  blocked_missing_information: {
    label: "Needs information first",
    glyph: "blocked",
    tone: "unknown",
  },
  insufficient_coverage: { label: "Not enough coverage", glyph: "coverage", tone: "unknown" },
  stale: { label: "Stale", glyph: "stale", tone: "stale" },
  provider_unavailable: { label: "Provider unavailable", glyph: "unavailable", tone: "error" },
  failed: { label: "Failed", glyph: "error", tone: "error" },
};

/** States the API does not own but the UI must show distinctly (design README). */
export const DISPLAY_STATE = {
  conditional: { label: "Conditional", glyph: "conditional", tone: "neutral" },
  unknown: { label: "Unknown", glyph: "unknown", tone: "unknown" },
  synthetic: { label: "Synthetic demo", glyph: "synthetic", tone: "neutral" },
  notStarted: { label: "Not started", glyph: "blocked", tone: "unknown" },
} satisfies Record<string, StatePresentation>;

export const FIELD_STATE: Record<FieldState, string> = {
  unasked: "Not asked yet",
  provided: "Answered",
  unknown: "Unknown",
  skipped: "Skipped",
  prefer_not_to_say: "Prefer not to say",
};

/** The order the field-state control offers; "Answered" first. */
export const FIELD_STATE_ORDER: readonly FieldState[] = [
  "provided",
  "unknown",
  "skipped",
  "prefer_not_to_say",
  "unasked",
];

export const DATA_MODE: Record<DataMode, string> = {
  demo: "Demo data",
  live_assisted: "Live-assisted",
  live_vacancy: "Live vacancies",
};

export type ProfileFieldName = keyof ProfileInput;

type FieldKind = "text" | "list" | "hours" | "money" | "salary";

type FieldWords = { label: string; hint: string; lessPrecise: string } & (
  | { kind: Exclude<FieldKind, "list"> }
  // A list's bound comes from the API's published schema (`listLimit` in ./profile).
  | { kind: "list"; itemLabel: string }
);

/** A pay period as it reads after an amount ("£28,000 a year"). */
export const PAY_PERIOD: Record<PayPeriod, string> = {
  year: "a year",
  month: "a month",
  week: "a week",
  hour: "an hour",
};

/** Words for each profile field and, per spec section 3, what a missing answer makes less precise. */
export const PROFILE_FIELDS: Record<ProfileFieldName, FieldWords> = {
  preferred_name: {
    label: "Preferred name",
    kind: "text",
    hint: "Optional. Used only to address you.",
    lessPrecise: "Nothing: it is only used to address you.",
  },
  current_role: {
    label: "Current role",
    kind: "text",
    hint: "Your current job title, or what you do now.",
    lessPrecise: "Which requirements you may already meet.",
  },
  cities: {
    label: "Work areas",
    kind: "list",
    itemLabel: "Work area",
    hint: `Up to ${listLimit("cities")} English cities, such as Leeds or Bristol.`,
    lessPrecise: "Roles, pay and listings: none can be searched without a work area.",
  },
  target_titles: {
    label: "Target roles",
    kind: "list",
    itemLabel: "Target role",
    hint: `Up to ${listLimit("target_titles")} roles you are considering.`,
    lessPrecise: "Every later chapter: requirements, options and routes start from a target.",
  },
  weekly_study_hours: {
    label: "Weekly study hours",
    kind: "hours",
    hint: "Hours a week you could give to learning.",
    lessPrecise: "Which courses fit your week, and how long a route takes.",
  },
  // Session 2: "total spending limit and monthly payment limit - what do these mean??" Each
  // hint says it in plain words, wherever the limit is shown (`EXPLAINED_FIELDS`).
  direct_spend_cap: {
    label: "Total spending limit",
    kind: "money",
    hint: "The most you'd spend on the whole change, all added up: course fees, exams, equipment and the like. Pay you'd give up while you train isn't part of it.",
    lessPrecise: "Which routes are affordable: they are shown without a spending check.",
  },
  monthly_payment_cap: {
    label: "Monthly payment limit",
    kind: "money",
    hint: "The most you could pay out in any one month. A route with a bigger payment in some month doesn't fit, even if its total does.",
    lessPrecise: "Whether a route's payments fit any single month.",
  },
  enjoyed_tasks: {
    label: "Tasks you enjoy",
    kind: "list",
    itemLabel: "Task you enjoy",
    hint: "Work you find satisfying, whether or not you are good at it yet.",
    lessPrecise: "Which directions are suggested: suggestions lean on your experience alone.",
  },
  confident_tasks: {
    label: "Tasks you believe you can do",
    kind: "list",
    itemLabel: "Task you believe you can do",
    hint: "Things you are confident about, even without proof yet.",
    lessPrecise: "Which gaps are worth checking first.",
  },
  evidenced_tasks: {
    label: "Tasks you can show you have done",
    kind: "list",
    itemLabel: "Task you can show",
    hint: "Things you have done and could point to, such as work, a course or a reference.",
    lessPrecise: "Which requirements count as demonstrated rather than unresolved.",
  },
  work_style: {
    label: "How you like to work",
    kind: "list",
    itemLabel: "Way you like to work",
    hint: "Optional, in your own words, such as outdoors or in a small team. It never rules work out.",
    lessPrecise: "Nothing is ruled out: suggestions just lean less on your working preferences.",
  },
  minimum_salary: {
    label: "Lowest pay you'd accept",
    kind: "salary",
    hint: "Before tax, with its period. A firm limit: vacancies whose advertised pay in that period is below it, and suggestions whose reviewed official pay is, are left out; Careerwright says how many, and why the rest were kept.",
    lessPrecise:
      "No route is checked against pay. Unknown pay is never treated as below your limit.",
  },
};

/** Answers whose label alone isn't plain enough: their hint is shown beside them everywhere. */
export const EXPLAINED_FIELDS: ReadonlySet<ProfileFieldName> = new Set([
  "direct_spend_cap",
  "monthly_payment_cap",
]);

export const PROFILE_FIELD_ORDER: readonly ProfileFieldName[] = [
  "target_titles",
  "cities",
  "current_role",
  "weekly_study_hours",
  "direct_spend_cap",
  "monthly_payment_cap",
  "minimum_salary",
  "enjoyed_tasks",
  "confident_tasks",
  "evidenced_tasks",
  "work_style",
  "preferred_name",
];

/** The entry choices (spec section 3: "I know my direction" or "Help me explore"). */
export const ENTRY_MODE: Record<EntryMode, string> = {
  sure: "I know my direction",
  unsure: "Help me explore",
};

/** The tone the person chooses (spec section 4); practical until they choose another. */
export const CONVERSATION_MODE: Record<ConversationMode, string> = {
  practical: "Keep this practical",
  gentle: "Help me explore gently",
  challenge: "Challenge my assumptions",
};

/** Careerwright's first question for each entry, before any reply exists (spec section 4). */
export const OPENING_QUESTION: Record<EntryMode, string> = {
  sure: "Which role are you aiming for, and at what level?",
  unsure: "What would you most like to be different about your working life?",
};

/** What each opening question asks about: the target, or nothing in particular ("open"). */
export const OPENING_ASKS: Record<EntryMode, ProfileFieldName | "open"> = {
  sure: "target_titles",
  unsure: "open",
};

/**
 * One-tap example replies under each demo question, by what it asks about (the API's
 * `asks_about`, or the opening's). Each is a reply the demo interviewer reads (its fixed
 * patterns, or Skip, Unknown and Prefer not to say), so tapping one never brings the same
 * question back (STATE-09; backend `test_interview_agent.py` taps each). A field the demo
 * never asks about has none.
 */
export const EXAMPLE_REPLIES: Record<ProfileFieldName | "open", readonly string[]> = {
  open: ["I enjoy working with people", "Skip"],
  target_titles: ["I want to be a nurse", "Skip"],
  current_role: ["I'm a warehouse supervisor", "Skip"],
  cities: ["Leeds", "Skip"],
  weekly_study_hours: ["5 hours a week", "Unknown"],
  direct_spend_cap: ["Up to £600", "Prefer not to say"],
  monthly_payment_cap: [],
  minimum_salary: [],
  enjoyed_tasks: [],
  confident_tasks: [],
  evidenced_tasks: [],
  work_style: [],
  preferred_name: [],
};

/** "Do you have a role in mind, or would you like to explore?": two ways on, in the
 *  conversation, that open existing views and commit nothing by themselves (STATE-09). */
export const ROLE_OR_EXPLORE = {
  explore: "Show me suggestions",
  name: "Name a role",
} as const;

/** Before detailed collection (BND1-02): what Careerwright covers, in one plain line. */
export const ENGLAND_ONLY = "Careerwright covers England for now.";

/** Before the entry choice: what Careerwright is for, in one plain line (session 2's start
 *  page: "It's for inputing information about yourself and your job preferences, not sure"). */
export const PURPOSE =
  "Careerwright helps you find work that could suit you, see what it would take, and plan a route you can afford.";

/** A suggestion's words beyond the API's (Task W2E): each says what Careerwright did. */
export const SUGGESTION_WORDS = {
  /** A suggestion that is one of the person's targets (STATE-10). */
  chosen: "Saved as one of your targets",
  /** The skills it was joined to a title of the person's by, named under the reason that says
   *  so (the API's): the first few (the audit's F4), the join never stated twice (D-I2). */
  skillsNamed: (first: string, more: boolean) =>
    more ? `Among them: ${first}.` : `Those skills: ${first}.`,
  otherSkills: (count: number) => `The other ${count} ${count === 1 ? "skill" : "skills"}`,
  /** The slate's unexpected connection, in words; its light in the world is Task M's. */
  connection: "An unexpected connection",
  /** What the connection's skills haven't been checked against yet. */
  notCompared: "Careerwright hasn't compared them with your own experience yet.",
} as const;

/** A streamed reply's state in words. Only "incomplete" is final; nothing streamed is saved. */
export const PARTIAL_REPLY: Record<PartialCompleteness, { label: string }> = {
  none: { label: "Careerwright is reading your message" },
  streaming: { label: "Writing a reply, not checked yet" },
  stopped: { label: "The reply stopped. Careerwright is trying again" },
  incomplete: { label: "This reply didn't finish and wasn't checked" },
  // Its text is never served; the checked reply replaces it.
  superseded: { label: "Replaced by the checked reply" },
};
/** A failed turn's reply so far: shown, never saved (MODEL-03). */
export const FAILED_REPLY_LABEL = "Stopped: not checked, nothing saved";

/** Why a model run ended without a result, in the person's words (failure classes). */
export const FAILURE_CLASS: Record<FailureClass, { title: string; action: string }> = {
  access_revoked: {
    title: "Access to this workspace ended while Careerwright was working",
    action: "Nothing was saved from it.",
  },
  credential_unavailable: {
    title: "No usable Meta key was found",
    action: "Save a key to continue. Editing still works without one.",
  },
  model_not_permitted: {
    title: "That model isn't allowed for this workspace's data",
    action: "Nothing was sent. Check the workspace's data label.",
  },
  // F10: points to the spending line (Task 3b).
  budget_exceeded: {
    title: "The spending limit for model calls is reached",
    action: `Careerwright stopped before spending more. Your work is kept. ${RAISE_THE_LIMIT}`,
  },
  provider_authentication: {
    title: "Meta didn't accept the key",
    action: "Rotate it with a working key, then try again.",
  },
  provider_billing: {
    title: "Meta refused the call for billing reasons",
    action: "Check your Meta account, then try again.",
  },
  provider_permission: {
    title: "The key isn't allowed to use that model",
    action: "Check the key's access in your Meta account.",
  },
  provider_request_rejected: {
    title: "Meta rejected the request",
    action: "Try again. If it repeats, add the details yourself.",
  },
  provider_unavailable: {
    title: "Meta isn't available right now",
    action: "Your work is kept. Try again later.",
  },
  invalid_model_output: {
    title: "The reply didn't pass Careerwright's checks twice",
    action: "Nothing was saved from it. Try again, or add the details yourself.",
  },
  model_refused: {
    title: "The model declined to answer",
    action: "Nothing was saved. Rephrase, or add the details yourself.",
  },
  output_truncated: {
    title: "The reply was cut off",
    action: "Nothing was saved from it. Try a shorter message.",
  },
  bound_exceeded: {
    title: "The model did more work than Careerwright allowed for",
    action: "Its cost was recorded and nothing was saved from it. Try again later.",
  },
  app_store_unavailable: {
    title: "Careerwright couldn't save the result",
    action: "Try again in a moment.",
  },
  retrieval_failed: {
    title: "None of the sources could be read",
    action: "This isn't a sign there are no vacancies. Try again later, or paste the advert.",
  },
  source_blocked: {
    title: "Every source was refused by its access rules",
    action: "Nothing was fetched. Choose other sources, or paste the advert.",
  },
  unknown_failure: {
    title: "Something went wrong while Careerwright was working",
    action: "Nothing was saved from it. Try again.",
  },
};

/** Why a job listing has no vacancy (STATE-02). Only `none_found_in_sources_checked` says
 * none was there, and only an API's own empty answer gives it. */
export const EMPTY_REASON: Record<EmptyReason, { title: string; detail: string }> = {
  no_sources_checked: {
    title: "No sources checked yet",
    detail: "Add a page to check, or run a search.",
  },
  sources_pending: {
    title: "Still checking your sources",
    detail: "Careerwright is fetching or reading them now. The list updates when it's done.",
  },
  no_source_retrieved: {
    title: "None of the sources could be fetched",
    detail: "This isn't a sign there are no vacancies. Try again later, or paste the advert.",
  },
  no_posting_readable: {
    title: "Careerwright couldn't read a job advert on these pages",
    detail: "This isn't a sign there are no vacancies. Paste the advert, or try another page.",
  },
  no_posting_found_by_model: {
    title: "Careerwright read these pages and found no job advert on them",
    detail:
      "This isn't a sign there are no vacancies: only these pages were read. Paste the advert, or try another page.",
  },
  none_found_in_sources_checked: {
    title: "No matching listings found in the sources checked",
    detail: "Only these sources were checked. Others may list vacancies.",
  },
  all_below_salary_floor: {
    title: "Every vacancy found advertises less than your minimum salary",
    detail:
      "Vacancies with unknown, predicted or differently stated pay are always kept. Change your minimum salary to see the others.",
  },
};

/** How a page went that Careerwright's model read for a job advert (fix round 3, review C M5).
 * None says there are no vacancies. */
export const MODEL_EXTRACTION_STATE: Record<
  ModelExtractionState,
  { title: string; detail: string }
> = {
  pending: {
    title: "Careerwright is reading this page",
    detail: "Its job advert, if it has one, appears here when the reading is done.",
  },
  postings_read: {
    title: "Careerwright read a job advert on this page",
    detail: "Each value was checked against the page's own words.",
  },
  postings_conflicting: {
    title: "The adverts on this page disagree with each other",
    detail:
      "Careerwright can't tell which is right, so none is shown. Paste the advert you mean, or try its own page.",
  },
  no_posting_found: {
    title: "Careerwright read this page and found no job advert on it",
    detail: "This isn't a sign there are no vacancies. Paste the advert, or try another page.",
  },
  not_read: {
    title: "Careerwright couldn't read a job advert on this page",
    detail: "This isn't a sign there are no vacancies. Paste the advert, or try another page.",
  },
  not_run: {
    title: "Careerwright didn't read this page",
    detail: "This isn't a sign there are no vacancies. Paste the advert, or try another page.",
  },
};

/** Why a source search proposed no page (review B I5). None says there are no vacancies:
 * only that this search found no posting page Careerwright could check. */
export const SEARCH_EMPTY_REASON: Record<SearchEmptyReason, { title: string; detail: string }> = {
  search_returned_nothing: {
    title: "The search returned no pages",
    detail:
      "This isn't a sign there are no vacancies. Try again later, or add a page you found yourself.",
  },
  no_candidate_proposed: {
    title: "The search returned pages, but none was a single job posting",
    detail:
      "This isn't a sign there are no vacancies. Add a posting you found yourself, or paste the advert.",
  },
  all_excluded: {
    title: "Every page the search suggested is one Careerwright can't use",
    detail:
      "This isn't a sign there are no vacancies. Look on employers' own careers sites, or paste the advert.",
  },
};

/** The slate's three directions (relative to what the person has told Careerwright). */
export const DIRECTION: Record<Direction, string> = {
  close_to_current: "Close to what you do now",
  transferable: "Builds on skills you could carry over",
  less_familiar: "Something different",
};

export const EMPHASIS: Record<Emphasis, string> = {
  balanced: "Balanced",
  practical: "Closer to what I do",
  unfamiliar: "Less familiar",
  broad: "Broader",
  deeper: "More depth",
};

/** "Show why this wasn't included". */
export const NOT_INCLUDED: Record<NotIncluded, string> = {
  duplicate: "Nearly the same as another occupation",
  excluded_occupation: "You said it's not for you",
  excluded_family: "You excluded this kind of work",
  below_salary_floor: "Its official pay is below your minimum salary",
  below_ai_resilience_minimum: "Its AI Resilience range starts below the minimum you chose",
  ai_resilience_unscored_excluded: "It has no AI Resilience range, and you chose to hide those",
  below_relevance_floor: "Matched your answers too weakly to suggest",
  family_limit: "Its kind of work is already shown",
  less_relevant: "Matched less closely than the ones shown",
};

/** Beside a search under "Found by these searches" that was too general to find work on its
 *  own (the API's `too_general`, ADR 0007 decision 13): it found nothing itself. */
export const ADDED_WEIGHT_ONLY =
  "too general to find work on its own, so it only added weight to what another search found";

/** Where a written explanation's quotation of ESCO comes from (a quotation of the person's
 *  own answers reads "You said"). */
export const RECORD_PART: Record<RecordPart, string> = {
  title: "ESCO's title",
  description: "ESCO's description",
  essential_skill: "An essential skill in ESCO",
};

/** What matching a target title to ESCO did (case, punctuation and plurals folded): never a
 *  claim about what ESCO holds, which another spelling or a hidden label can make untrue. */
export const RESOLUTION: Record<Resolution, string> = {
  esco: "Found in ESCO",
  ambiguous: "Matched to several occupations in ESCO",
  provisional: "Your own title: Careerwright couldn't match it in ESCO",
  not_found: "Careerwright couldn't match it in ESCO",
};

// Discovery's facts in words (Task 6d slice A; ruling R11). The API serves what each search or
// match did, with a reason code and the values the words need, never a sentence; these maps
// word each one. Each is keyed by every reason the API can send, so a new reason fails the type
// check here until it has words. What each says is what the API's sentence said before; only
// where the words live changed. A title takes no article and no plural rule: the templates
// need none.

type SlateNote = SlateOut["notes"][number];
type FewerReason = SlateOut["fewer_reasons"][number];
type SuggestionReason = SuggestionOut["reasons"][number];
/** Words for each fact of a union, by its reason, from that fact's own values. */
type Worded<U extends { reason: string }> = {
  [R in U["reason"]]: (fact: Extract<U, { reason: R }>) => string;
};

/** The person's words, quoted. */
const q = (text: string) => `“${text}”`;
/** The person's words quoted at the start of a sentence. */
const opening = (text: string) => q(text.charAt(0).toUpperCase() + text.slice(1));
/** “a”, “a” and “b”, or “a”, “b” and “c”. */
const quotedList = (texts: readonly string[]) =>
  texts.length < 2
    ? texts.map(q).join("")
    : `${texts.slice(0, -1).map(q).join(", ")} and ${q(texts.at(-1) ?? "")}`;
const count = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;

/** Which of the person's answers found a suggestion, as its line starts. */
export const ANSWER_SOURCE: Record<ProfileField, string> = {
  preferred_name: "Your preferred name",
  current_role: "Your current role",
  cities: "Your work areas",
  target_titles: "A role you named",
  weekly_study_hours: "Your weekly hours",
  direct_spend_cap: "Your total spending limit",
  monthly_payment_cap: "Your monthly payment limit",
  enjoyed_tasks: "What you enjoy",
  confident_tasks: "What you believe you can do",
  evidenced_tasks: "What you have done",
  work_style: "How you like to work",
  minimum_salary: "The lowest pay you'd accept",
};

/** What an answer's searches did that found no work: each says what the search did, never
 *  what ESCO holds (a search reads the main names of essential skills only). */
function answerFoundNoWork(fact: Extract<SlateNote, { reason: "answer_found_no_work" }>): string {
  const did = (kind: SearchDid) =>
    fact.searches.filter((search) => search.did === kind).map((search) => search.text);
  const read = did("read_main_names");
  const common = did("only_common_words");
  const joined = did("no_shared_occupation");
  const mainName = "main name of a skill ESCO lists as essential holds all the words of";
  const commonOnly = "only common words, which Careerwright doesn't search for";
  if (fact.own_words) {
    return read.length > 0
      ? `No ${mainName} ${q(fact.answer)}, so it found no work.`
      : `${opening(fact.answer)} has ${commonOnly}, so it found no work.`;
  }
  const its = (texts: string[], several: string) =>
    texts.length === 1 ? `its search ${q(texts[0] ?? "")}` : `${several} ${quotedList(texts)}`;
  const parts: string[] = [];
  if (read.length > 0) parts.push(`no ${mainName} ${its(read, "any of its searches")}`);
  if (common.length > 0) {
    parts.push(
      `${its(common, "its searches")} ${common.length > 1 ? "have" : "has"} ${commonOnly}`,
    );
  }
  if (joined.length > 0) {
    const own = joined.length > 1 ? "your own titles" : "your own title";
    parts.push(
      `Careerwright found no other occupation in ESCO that shares ${fact.min_shared} or more essential skills with ${its(joined, "any of its searches")}, ${own}`,
    );
  }
  return `${opening(fact.answer)} found no work: ${parts.join(", and ")}.`;
}

/** A search too general to find work on its own: what it did, and what would help. A model's
 *  search is the one too general, so the person is asked to say more only of their own words. */
function tooGeneral(fact: Extract<SlateNote, { reason: "too_general" }>): string {
  const did =
    fact.by === "occupations"
      ? `reached ${fact.occupations} occupations in ESCO through the main names of their essential skills, too many to choose from on its own`
      : `matched the main names of ${fact.skills} different essential skills in ESCO, none of them just those words, so it's too general to choose work from on its own`;
  if (fact.own_words) {
    return `${opening(fact.search)} ${did}. Say more about it, such as what it's about or who it's for.`;
  }
  const narrower =
    fact.narrower_for.length > 0
      ? ` Careerwright would need a narrower search to find work from ${quotedList(fact.narrower_for)}.`
      : "";
  return `The search ${q(fact.search)} (from ${quotedList(fact.answers)}) ${did}.${narrower}`;
}

/** How the slate was made: "How Careerwright searched". */
export const SLATE_NOTE: Worded<SlateNote> = {
  release_changed: (fact) =>
    `These searches were chosen when ESCO ${fact.searched} was held; this slate uses ${fact.held}, so some occupations may have changed.`,
  one_word_work_style: (fact) =>
    `How you like to work (${fact.answers.map(q).join(", ")}) isn't searched on its own, because a single word matches too loosely. Careerwright searches a longer answer, such as “working outdoors”.`,
  answer_found_no_work: answerFoundNoWork,
  too_general: tooGeneral,
  join_kept_best: (fact) =>
    `Careerwright found ${fact.found} other occupations in ESCO that share ${fact.min_shared} or more essential skills with ${q(fact.title)}, and keeps the ${fact.kept} with the largest share of essential skills in common.`,
  small_pool: (fact) =>
    `Careerwright chose these from ${fact.pool_size} occupations that match your answers closely. It aims for at least ${fact.pool_target}, but doesn't add weaker matches to get there.`,
  casting_wider: () =>
    "Casting wider: a lower bar for relevance and one suggestion per kind of work.",
  more_depth: (fact) =>
    `Showing up to ${fact.family_limit} from one kind of work, because you asked for more depth.`,
};

/** Why there are fewer than six suggestions. */
export const FEWER_REASON: Worded<FewerReason> = {
  nothing_found: () => "None of your answers found work to suggest yet.",
  few_matched: (fact) =>
    `Only ${count(fact.count, "occupation", "occupations")} matched your answers closely enough to suggest. Careerwright doesn't fill the rest with weaker matches.`,
  kinds_of_work_shown: (fact) =>
    `${count(fact.count, "more is", "more are")} in kinds of work already shown ${fact.family_limit} times; ask for more depth to see them.`,
  exclusions_removed: (fact) =>
    `Your exclusions removed ${count(fact.count, "occupation", "occupations")}.`,
  title_not_matched: (fact) =>
    `Careerwright couldn't match ${q(fact.title)} to an occupation in ESCO, so it can't join other work to that title by shared skills. Choose the ESCO occupation closest to it.`,
  title_matched_several: (fact) =>
    `Careerwright matched ${q(fact.title)} to ${fact.occupations} occupations in ESCO, so it can't join other work to that title by shared skills until you choose which one you mean.`,
  no_shared_occupation: (fact) =>
    `Careerwright found no other occupation in ESCO that shares ${fact.min_shared} or more essential skills with ${q(fact.title)}.`,
};

/** Why a suggestion could suit the person: what found it, from one of their answers. */
export const SUGGESTION_REASON: Worded<SuggestionReason> = {
  joined_by_shared_skills: (fact) =>
    `${ANSWER_SOURCE[fact.field]}: ${q(fact.answer)}. ESCO lists ${fact.shared} of the same essential skills for both, so Careerwright joined them by those skills.`,
  searched_through_skill: (fact) =>
    `${ANSWER_SOURCE[fact.field]}: ${q(fact.answer)}. Careerwright searched for ${q(fact.search)}, and ESCO lists ${q(fact.skill)} as an essential skill for this work.`,
  title_idea_matched: (fact) =>
    `${ANSWER_SOURCE[fact.field]}: ${q(fact.answer)}. Careerwright thought of the title ${q(fact.title)} from it and matched that title to this occupation in ESCO.`,
  own_title_matched: (fact) =>
    `${ANSWER_SOURCE[fact.field]}: ${q(fact.answer)}. Careerwright matched it to this occupation in ESCO.`,
};

// TypeScript can't relate a fact's reason to its own entry, so each lookup says so once here.
export const slateNote = (fact: SlateNote): string =>
  (SLATE_NOTE[fact.reason] as (fact: SlateNote) => string)(fact);
export const fewerReason = (fact: FewerReason): string =>
  (FEWER_REASON[fact.reason] as (fact: FewerReason) => string)(fact);
export const suggestionReason = (fact: SuggestionReason): string =>
  (SUGGESTION_REASON[fact.reason] as (fact: SuggestionReason) => string)(fact);

/** A suggestion's facts beyond what found it, in words: what might not suit, the entry gate,
 *  how to try it, and what isn't researched yet. */
export function suggestionWords(suggestion: SuggestionOut): {
  mightNot: string[];
  entryGate: string;
  tryIt: string[];
  evidenceGap: string;
} {
  const mightNot: string[] = [];
  if (suggestion.essential_skills.length > 0) {
    mightNot.push(
      `ESCO lists ${suggestion.essential_skill_count} essential skills, not yet compared with your experience, including: ${suggestion.essential_skills.join(", ")}.`,
    );
  }
  if (suggestion.regulated === true) {
    mightNot.push(
      "ESCO marks this as a regulated profession in at least one European country. Whether England requires registration isn't checked yet.",
    );
  }
  if (suggestion.different_kind_of_work) {
    mightNot.push(
      "It's a different kind of work from what you've told Careerwright about, so it may need new experience.",
    );
  }
  const first = suggestion.essential_skills[0];
  return {
    mightNot,
    entryGate:
      suggestion.regulated === true
        ? "Registration may be required. Not checked yet."
        : "Entry requirements aren't researched yet.",
    tryIt: [
      "Talk to someone who does this work about a typical week (an informational interview).",
      ...(first === undefined ? [] : [`Try one of its tasks on a small scale: ${first}.`]),
    ],
    evidenceGap:
      "Pay, demand and listings in your work areas aren't researched yet. Finding no listings later would be a demand signal, not proof this work doesn't exist.",
  };
}

/** Why the salary floor kept pay it couldn't compare, after "kept because". */
export const FLOOR_UNKNOWN: Record<FloorUnknown, string> = {
  no_pay: "Careerwright found no pay in what it read",
  no_upper_amount: "Careerwright found no top to the pay range",
  predicted: "the pay Careerwright found is an estimate, not the advertiser's own figure",
  basis_unknown: "Careerwright couldn't tell whether the pay is advertised or estimated",
  period_differs: "official pay is not given per your floor's period",
  period_not_stated: "Careerwright couldn't tell the pay's period",
  other_currency: "the pay Careerwright found is in another currency",
  no_reviewed_mapping: "no reviewed UK occupation code links them to pay data",
  no_work_area: "you have not named a city, so no region's pay applies",
  not_published: "the official figure is not published for your regions",
};

/** The salary floor's effect on a slate, every count, so the counts add up. */
export function floorWords(floor: SalaryFloorOut): string {
  const parts = [
    `${floor.left_out} left out because their official pay is below it`,
    `${floor.meets} meet it`,
    ...floor.kept_by_reason.map(
      (kept) => `${kept.count} kept because ${FLOOR_UNKNOWN[kept.reason]}`,
    ),
  ];
  return `Your minimum salary of ${formatMoney(floor.amount)} ${PAY_PERIOD[floor.period]} (gross) is applied: ${parts.join("; ")}. Unknown pay is never treated as below it.`;
}

/** The AI Resilience filter's effect, when it is not at its default (Any, unscored kept). */
export function aiFilterWords(filter: AiResilienceFilterOut): string | null {
  if (filter.minimum === null && filter.include_unscored) return null;
  const minimum = filter.minimum === null ? "Any" : `${filter.minimum} or more`;
  const ranges = filter.synthetic
    ? "each range (a synthetic fixture range here, not a real assessment)"
    : "each reviewed range";
  const unscored = filter.include_unscored
    ? `${filter.unscored} unscored kept`
    : `${filter.unscored_excluded} unscored left out`;
  return `AI Resilience Score filter, ${minimum} on the lower end of ${ranges}: ${filter.below_minimum} left out below it; ${unscored}.`;
}

/** The titles Careerwright thought of but couldn't match, in one line; null with none. */
export function titleIdeasWords(ideas: SlateOut["title_ideas"]): string | null {
  const unmatched = ideas
    .filter((idea) => idea.outcome === "not_matched")
    .map((idea) => idea.title);
  return unmatched.length === 0
    ? null
    : `Titles Careerwright thought of but couldn't match to an occupation in ESCO, so not suggested: ${unmatched.join(", ")}.`;
}

/** The early requirement sketch's label: never a checked or best route. */
export const SKETCH_LABEL = "Early sketch, not a checked route";

/** For a title Careerwright couldn't match in ESCO, by its coverage; null says nothing more. The
 *  option pack researched a pack target, and its coverage line says what Careerwright can
 *  check, so it never reads "not researched" (Task 6d slice A fix round 1; say less). */
const UNMATCHED_STATUS: Record<TargetCoverage, string | null> = {
  pack_target: null,
  several_pack_targets: null,
  not_covered:
    "Careerwright couldn't match this title to an occupation in ESCO, so there's no requirement list yet. Not researched.",
};

/** What a target's resolution means for its requirements, under each sketched target, from
 *  its match and its coverage; null: no line. */
export const RESEARCH_STATUS: Record<Resolution, (coverage: TargetCoverage) => string | null> = {
  esco: () => "Requirements from ESCO; not yet compared with your experience.",
  ambiguous: () =>
    "Careerwright matched this title to several occupations in ESCO. Choose the one you mean.",
  provisional: (coverage) => UNMATCHED_STATUS[coverage],
  not_found: (coverage) => UNMATCHED_STATUS[coverage],
};

/** The sketch's generic steps, each unresolved, with what each can use so far. */
export const SKETCH_STEP: Record<
  Step,
  { name: string; detail: (inputs: SketchOut["inputs"]) => string }
> = {
  compare: {
    name: "Compare these requirements with what you have done",
    detail: () => "Not compared yet: nothing is marked missing or met.",
  },
  find_options: {
    name: "Find courses, work routes or funding for any gaps",
    detail: () => "Not researched yet: no providers, prices or dates.",
  },
  check_time_and_cost: {
    name: "Check the time and cost against your week and budget",
    detail: (inputs) =>
      `${inputs.weekly_study_hours === "provided" ? "Uses your weekly hours." : "Your weekly hours aren't known, so timing can't be checked yet."} ${inputs.direct_spend_cap === "provided" ? "Uses your spending limit." : "Your spending limit isn't known, so costs can't be checked yet."}`,
  },
};

/** How far Careerwright can cover a target, in one plain line where it is chosen (Task 6d
 *  slice A; session W2 judges the words). `asks`: whether Careerwright can show what the work
 *  usually asks for (the target names one ESCO occupation). */
export const TARGET_COVERAGE: Record<TargetCoverage, (asks: boolean) => string> = {
  pack_target: () => "Careerwright can check skills, options and routes for this role.",
  not_covered: (asks) =>
    asks
      ? "Careerwright can show what this work usually asks for. It can't check skills, options or routes for it yet."
      : "Careerwright can't check skills, options or routes for this role yet.",
  several_pack_targets: () =>
    "Careerwright can't check skills, options or routes for this role yet.",
};

/** An error code in the status vocabulary: its words and its tone (STATE-01). */
export type ErrorStatement = { title: string; action: string; tone: Tone };

/**
 * The tone each code takes. Only real failures are red: a stale version reads as stale, a
 * search limit as a partial result, missing evidence as unknown, and a refusal by policy or a
 * missing prerequisite as a plain notice.
 */
const ERROR_TONE: Record<ErrorCode, Tone> = {
  SOURCE_BLOCKED: "neutral",
  RETRIEVAL_FAILED: "error",
  INSUFFICIENT_EVIDENCE: "unknown",
  SCHEMA_INVALID: "error",
  MODEL_UNAVAILABLE: "error",
  BUDGET_EXCEEDED: "neutral",
  SOLVE_LIMIT_REACHED: "neutral",
  STALE_INPUT_VERSION: "stale",
  FEATURE_NOT_IN_M0: "neutral",
  MODEL_SCOPE_EXCEEDED: "neutral",
  COARSE_MODEL_UNRESOLVED: "unknown",
  NO_ROUTE_IN_BOUNDED_MODEL: "neutral",
  UNAUTHENTICATED: "neutral",
  NOT_INVITED: "error",
  NOT_FOUND: "error",
  METHOD_NOT_ALLOWED: "error",
  REQUEST_REJECTED: "error",
  CLIENT_NOT_ALLOWED: "error",
  HOST_NOT_ALLOWED: "error",
  ORIGIN_NOT_ALLOWED: "error",
  VALIDATION_FAILED: "error",
  LIMIT_EXCEEDED: "error",
  IDEMPOTENCY_KEY_REQUIRED: "error",
  IDEMPOTENCY_KEY_REUSED: "error",
  CONSENT_REQUIRED: "neutral",
  CREDENTIAL_EXISTS: "neutral",
  CREDENTIAL_REVOKED: "neutral",
  CREDENTIAL_REQUIRED: "neutral",
  MODE_NOT_SUPPORTED: "neutral",
  STORE_UNAVAILABLE: "error",
  AUTH_UNAVAILABLE: "error",
  INTERNAL_ERROR: "error",
  TAXONOMY_UNAVAILABLE: "error",
  REFERENCE_DATA_UNAVAILABLE: "error",
  CONFIRMATION_REQUIRED: "neutral",
  PROPOSAL_NOT_AVAILABLE: "neutral",
  ALREADY_DECIDED: "neutral",
  SLATE_ALREADY_EXPLAINED: "neutral",
  RUN_FINISHED: "neutral",
  PROTECTED_GATE: "neutral",
};

/** What the person sees for each API error code. The API's own message is never shown. */
const ERROR_WORDS: Record<ErrorCode, Omit<ErrorStatement, "tone">> = {
  SOURCE_BLOCKED: {
    title: "That source can't be used",
    action: "Its access rules don't allow it. Choose another source.",
  },
  RETRIEVAL_FAILED: { title: "A source couldn't be read", action: "Try again later." },
  INSUFFICIENT_EVIDENCE: {
    title: "Not enough evidence",
    action: "Add evidence or mark the question as unresolved.",
  },
  SCHEMA_INVALID: {
    title: "A reply didn't pass validation",
    action: "Nothing was saved from it. Try again.",
  },
  MODEL_UNAVAILABLE: {
    title: "The model isn't available",
    action: "Your work is kept. Editing and saved results still work.",
  },
  BUDGET_EXCEEDED: {
    title: "The spending limit for model calls is reached",
    action: `Careerwright stopped before spending more. Your work is kept. ${RAISE_THE_LIMIT}`,
  },
  SOLVE_LIMIT_REACHED: {
    title: "The route search stopped at its limit",
    action: "Routes found so far are kept and marked incomplete.",
  },
  STALE_INPUT_VERSION: {
    title: "This changed since you loaded it",
    action: "Review the latest version, then save again.",
  },
  FEATURE_NOT_IN_M0: {
    title: "Not available in this version",
    action: "This feature is planned for later.",
  },
  MODEL_SCOPE_EXCEEDED: {
    title: "Outside what Careerwright can plan",
    action: "This route needs more than the planning model covers.",
  },
  COARSE_MODEL_UNRESOLVED: {
    title: "The monthly model can't settle this",
    action: "Check the exact dates with the provider.",
  },
  NO_ROUTE_IN_BOUNDED_MODEL: {
    title: "No route within these limits",
    action: "Review the limits that prevented one.",
  },
  UNAUTHENTICATED: { title: "You're signed out", action: "Sign in again to continue." },
  NOT_INVITED: {
    title: "This account isn't invited",
    action: "Sign in with an invited account.",
  },
  NOT_FOUND: {
    title: "Not found",
    action: "It may have been removed, or it belongs to another account.",
  },
  METHOD_NOT_ALLOWED: { title: "That action isn't supported", action: "Reload the page." },
  REQUEST_REJECTED: { title: "The request was rejected", action: "Reload the page and try again." },
  CLIENT_NOT_ALLOWED: {
    title: "Careerwright serves this computer only",
    action: "Open Careerwright on the machine it runs on.",
  },
  HOST_NOT_ALLOWED: {
    title: "Careerwright answers on its local address only",
    action: "Open it at the address Careerwright printed when it started.",
  },
  ORIGIN_NOT_ALLOWED: {
    title: "This page isn't allowed to make changes",
    action: "Open Careerwright at its local address.",
  },
  VALIDATION_FAILED: {
    title: "Some answers aren't valid",
    action: "Check the highlighted fields and save again.",
  },
  LIMIT_EXCEEDED: { title: "Over the limit", action: "Remove an entry first." },
  IDEMPOTENCY_KEY_REQUIRED: { title: "The request was incomplete", action: "Try again." },
  IDEMPOTENCY_KEY_REUSED: {
    title: "The request was refused as a duplicate",
    action: "Reload the page and make the change again.",
  },
  CONSENT_REQUIRED: {
    title: "Consent is needed first",
    action: "Agree to encrypted storage to save a key. Editing still works without one.",
  },
  CREDENTIAL_EXISTS: { title: "A key is already saved", action: "Rotate it instead." },
  CREDENTIAL_REVOKED: { title: "That key was revoked", action: "Save a new key to continue." },
  CREDENTIAL_REQUIRED: {
    title: "A key is needed",
    action: "Save a Meta key to run this. Editing still works without one.",
  },
  MODE_NOT_SUPPORTED: {
    title: "That data mode isn't available",
    action: "Use demo or live-assisted mode.",
  },
  STORE_UNAVAILABLE: {
    title: "Careerwright's database isn't reachable",
    action: "Nothing was lost. Try again in a moment.",
  },
  AUTH_UNAVAILABLE: {
    title: "Sign-in isn't reachable",
    action: "Nothing was lost. Try again in a moment.",
  },
  INTERNAL_ERROR: {
    title: "Something went wrong on our side",
    action: "Try again. Quote the reference below if you report it.",
  },
  TAXONOMY_UNAVAILABLE: {
    title: "The occupation list isn't loaded",
    action: "Run the setup step again, then restart Careerwright. Your work is kept.",
  },
  REFERENCE_DATA_UNAVAILABLE: {
    title: "Pay and AI evidence aren't loaded",
    action: "Run the setup step again, then restart Careerwright. Your work is kept.",
  },
  CONFIRMATION_REQUIRED: {
    title: "Confirm each limit or target first",
    action: "Tick the confirmation beside each one you want saved.",
  },
  PROPOSAL_NOT_AVAILABLE: {
    title: "There is nothing from this reply to save",
    action: "The reply didn't finish or didn't pass its checks. Send your message again.",
  },
  ALREADY_DECIDED: {
    title: "You already chose what to keep from this reply",
    action: "Edit the answers directly if you want to change them.",
  },
  SLATE_ALREADY_EXPLAINED: {
    title: "These suggestions have had their one written note",
    action:
      "Suggest again for a new set of suggestions, which gets a note of its own. The suggestions shown now would be replaced.",
  },
  RUN_FINISHED: {
    title: "This had already finished",
    action: "Nothing was cancelled. Its result stands.",
  },
  PROTECTED_GATE: {
    title: "A legal or entry requirement can't be switched off",
    action: "Challenge its source, or choose a different target.",
  },
};

/** What the person can do when a slate's written note isn't there (ADR 0007 decision 12). */
export const NOTE_RECOVERY = {
  /** Its run stopped before any request reached a model, so the one call is unused. */
  retry: "No request reached the model, so Careerwright can try the note again.",
  /** A request was sent: this slate has had its one call. */
  spent: "These suggestions have had their one written note.",
  /** What Suggest again does, wherever it is offered for a note. */
  suggestAgain:
    "Suggest again makes a new set of suggestions, which gets a note of its own: the suggestions shown now would be replaced.",
  /** The request for the note was refused before any run existed. */
  resend: "Nothing was sent to the model.",
} as const;

/** The line on each card when its note is missing: after a run that failed, or after a
 *  request refused before any run existed. "How Careerwright found it" follows at once. */
export const NOTE_CARD = {
  failed: {
    detail: "no written note",
    after: "Nothing from it was kept.",
  },
  refused: {
    detail: "no written note",
    after: "Careerwright didn't ask the model, so nothing was sent.",
  },
} as const;

/** What can work after a refusal that asking again would only repeat: changing the answers
 *  (the chapter then offers Suggest again) or Suggest again itself. Never Try again. */
export type NoteRefusalWords = {
  title: string;
  action: string;
  recovery: "edit_answers" | "suggest_again";
};

/** Such refusals of a slate's note, by the error's `details.reason`. */
export const NOTE_REFUSAL_REASON = {
  no_quotable_answer: {
    title: "Your answers can't be quoted on their own",
    action:
      "Add a few words to what you enjoy, can do or have done with Edit answers directly. Careerwright then offers Suggest again.",
    recovery: "edit_answers",
  },
  answers_too_long: {
    title: "Your answers are too long for a written note",
    action:
      "Shorten or remove some answers with Edit answers directly. Careerwright then offers Suggest again.",
    recovery: "edit_answers",
  },
  no_suggestions: {
    title: "There are no suggestions here to explain",
    action:
      "Add to your answers with Edit answers directly. Careerwright then offers Suggest again.",
    recovery: "edit_answers",
  },
} as const satisfies Record<string, NoteRefusalWords>;

/** Such refusals of a slate's note, by error code. */
export const NOTE_REFUSAL_CODE: Partial<Record<ErrorCode, NoteRefusalWords>> = {
  PROPOSAL_NOT_AVAILABLE: {
    title: "These suggestions have no searches to explain",
    action: "Their search didn't finish or didn't pass its checks.",
    recovery: "suggest_again",
  },
  STALE_INPUT_VERSION: {
    title: "Your answers changed after these suggestions were made",
    action: "A note would quote answers you have since changed.",
    recovery: "suggest_again",
  },
  SLATE_ALREADY_EXPLAINED: {
    title: "These suggestions have had their one written note",
    action: "Careerwright doesn't write it again for the same suggestions.",
    recovery: "suggest_again",
  },
};

export const ERROR_STATEMENT = Object.fromEntries(
  (Object.keys(ERROR_WORDS) as ErrorCode[]).map((code) => [
    code,
    { ...ERROR_WORDS[code], tone: ERROR_TONE[code] },
  ]),
) as Record<ErrorCode, ErrorStatement>;
