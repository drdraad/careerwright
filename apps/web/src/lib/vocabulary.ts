// How the shared state vocabulary reads in the UI (STATE-01, UI-04). The values come only from
// the generated client; these tables give each one words and a glyph. `Record<…>` over the
// generated unions makes a new API value a compile error here until it has words.

import type { GlyphName } from "@/components/Glyph";
import type {
  ConversationMode,
  DataMode,
  Direction,
  Emphasis,
  EmptyReason,
  EntryMode,
  ErrorCode,
  FailureClass,
  FieldState,
  ModelExtractionState,
  NotIncluded,
  PartialCompleteness,
  PayPeriod,
  ProfileInput,
  RecordPart,
  Resolution,
  SearchEmptyReason,
  WorkState,
} from "@/generated/api";
import { listLimit } from "./bounds";

/** Only error and stale add a hue; everything else is carried by glyph and words. */
export type Tone = "neutral" | "unknown" | "stale" | "error";

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
  direct_spend_cap: {
    label: "Total spending limit",
    kind: "money",
    hint: "The most you would spend on the change in total.",
    lessPrecise: "Which routes are affordable: they are shown without a spending check.",
  },
  monthly_payment_cap: {
    label: "Monthly payment limit",
    kind: "money",
    hint: "The most you could pay in any one month.",
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
    hint: "Before tax, with its period. Recorded as a firm limit, but not applied to anything until pay is researched.",
    lessPrecise:
      "No route is checked against pay. Unknown pay is never treated as below your limit.",
  },
};

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
export const ENTRY_MODE: Record<EntryMode, { label: string; detail: string }> = {
  sure: {
    label: "I know my direction",
    detail: "Confirm the role you're aiming for, then the practical limits.",
  },
  unsure: {
    label: "Help me explore",
    detail: "Start from what you enjoy. Nessa suggests varied directions to consider.",
  },
};

/** The tone the person chooses (spec section 4); practical until they choose another. */
export const CONVERSATION_MODE: Record<ConversationMode, string> = {
  practical: "Keep this practical",
  gentle: "Help me explore gently",
  challenge: "Challenge my assumptions",
};

/** Nessa's first question for each entry, before any reply exists (spec section 4). */
export const OPENING_QUESTION: Record<EntryMode, string> = {
  sure: "Which role are you aiming for, and at what level?",
  unsure: "What would you most like to be different about your working life?",
};

/** A streamed reply's state in words. Only "incomplete" is final; nothing streamed is saved. */
export const PARTIAL_REPLY: Record<PartialCompleteness, { label: string }> = {
  none: { label: "Nessa is reading your message" },
  streaming: { label: "Writing a reply, not checked yet" },
  stopped: { label: "The reply stopped. Nessa is trying again" },
  incomplete: { label: "This reply didn't finish and wasn't checked" },
  // Its text is never served; the checked reply replaces it.
  superseded: { label: "Replaced by the checked reply" },
};
/** A failed turn's reply so far: shown, never saved (MODEL-03). */
export const FAILED_REPLY_LABEL = "Stopped: not checked, nothing saved";

/** Why a model run ended without a result, in the person's words (failure classes). */
export const FAILURE_CLASS: Record<FailureClass, { title: string; action: string }> = {
  access_revoked: {
    title: "Access to this workspace ended while Nessa was working",
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
  budget_exceeded: {
    title: "The spending limit for model calls is reached",
    action: "Raise the limit or wait for the next month.",
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
    title: "The reply didn't pass Nessa's checks twice",
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
    title: "The model did more work than Nessa allowed for",
    action: "Its cost was recorded and nothing was saved from it. Try again later.",
  },
  app_store_unavailable: {
    title: "Nessa couldn't save the result",
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
    title: "Something went wrong while Nessa was working",
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
    detail: "Nessa is fetching or reading them now. The list updates when it's done.",
  },
  no_source_retrieved: {
    title: "None of the sources could be fetched",
    detail: "This isn't a sign there are no vacancies. Try again later, or paste the advert.",
  },
  no_posting_readable: {
    title: "Nessa couldn't read a job advert on these pages",
    detail: "This isn't a sign there are no vacancies. Paste the advert, or try another page.",
  },
  no_posting_found_by_model: {
    title: "Nessa read these pages and found no job advert on them",
    detail:
      "This isn't a sign there are no vacancies: only these pages were read. Paste the advert, or try another page.",
  },
  none_found_in_sources_checked: {
    title: "No matching listings found in the sources checked",
    detail: "Only these sources were checked. Others may list vacancies.",
  },
};

/** How a page went that Nessa's model read for a job advert (fix round 3, review C M5).
 * None says there are no vacancies. */
export const MODEL_EXTRACTION_STATE: Record<
  ModelExtractionState,
  { title: string; detail: string }
> = {
  pending: {
    title: "Nessa is reading this page",
    detail: "Its job advert, if it has one, appears here when the reading is done.",
  },
  postings_read: {
    title: "Nessa read a job advert on this page",
    detail: "Each value was checked against the page's own words.",
  },
  postings_conflicting: {
    title: "The adverts on this page disagree with each other",
    detail:
      "Nessa can't tell which is right, so none is shown. Paste the advert you mean, or try its own page.",
  },
  no_posting_found: {
    title: "Nessa read this page and found no job advert on it",
    detail: "This isn't a sign there are no vacancies. Paste the advert, or try another page.",
  },
  not_read: {
    title: "Nessa couldn't read a job advert on this page",
    detail: "This isn't a sign there are no vacancies. Paste the advert, or try another page.",
  },
  not_run: {
    title: "Nessa didn't read this page",
    detail: "This isn't a sign there are no vacancies. Paste the advert, or try another page.",
  },
};

/** Why a source search proposed no page (review B I5). None says there are no vacancies:
 * only that this search found no posting page Nessa could check. */
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
    title: "Every page the search suggested is one Nessa can't use",
    detail:
      "This isn't a sign there are no vacancies. Look on employers' own careers sites, or paste the advert.",
  },
};

/** The slate's three directions (relative to what the person has told Nessa). */
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
  below_relevance_floor: "Matched your answers too weakly to suggest",
  family_limit: "Its kind of work is already shown",
  less_relevant: "Matched less closely than the ones shown",
};

/** Where a written explanation's quotation of ESCO comes from (a quotation of the person's
 *  own answers reads "You said"). */
export const RECORD_PART: Record<RecordPart, string> = {
  title: "ESCO's title",
  description: "ESCO's description",
  essential_skill: "An essential skill in ESCO",
};

export const RESOLUTION: Record<Resolution, string> = {
  esco: "Found in ESCO",
  ambiguous: "Several ESCO occupations have this title",
  provisional: "Your own title, not in ESCO",
  not_found: "Not found in ESCO",
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
  CONFIRMATION_REQUIRED: "neutral",
  PROPOSAL_NOT_AVAILABLE: "neutral",
  ALREADY_DECIDED: "neutral",
  SLATE_ALREADY_EXPLAINED: "neutral",
  RUN_FINISHED: "neutral",
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
    action: "Raise the limit or wait for the next month.",
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
    title: "Outside what Nessa can plan",
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
    title: "Nessa serves this computer only",
    action: "Open Nessa on the machine it runs on.",
  },
  HOST_NOT_ALLOWED: {
    title: "Nessa answers on its local address only",
    action: "Open it at the address Nessa printed when it started.",
  },
  ORIGIN_NOT_ALLOWED: {
    title: "This page isn't allowed to make changes",
    action: "Open Nessa at its local address.",
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
    title: "Nessa's database isn't reachable",
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
    action: "Run the setup step again, then restart Nessa. Your work is kept.",
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
};

/** What the person can do when a slate's written note isn't there (ADR 0007 decision 12). */
export const NOTE_RECOVERY = {
  /** Its run stopped before any request reached a model, so the one call is unused. */
  retry: "No request reached the model, so Nessa can try the note again.",
  /** A request was sent: this slate has had its one call. */
  spent: "These suggestions have had their one written note.",
  /** What Suggest again does, wherever it is offered for a note. */
  suggestAgain:
    "Suggest again makes a new set of suggestions, which gets a note of its own: the suggestions shown now would be replaced.",
  /** The request for the note was refused before any run existed. */
  resend: "Nothing was sent to the model.",
} as const;

/** The line on each card when its note is missing: after a run that failed, or after a
 *  request refused before any run existed. */
export const NOTE_CARD = {
  failed: {
    detail: "no written note",
    after: "Nothing from it was kept; how Nessa found this suggestion is below.",
  },
  refused: {
    detail: "no written note",
    after:
      "Nessa didn't ask the model, so nothing was sent; how Nessa found this suggestion is below.",
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
      "Add a few words to what you enjoy, can do or have done with Edit answers directly. Nessa then offers Suggest again.",
    recovery: "edit_answers",
  },
  answers_too_long: {
    title: "Your answers are too long for a written note",
    action:
      "Shorten or remove some answers with Edit answers directly. Nessa then offers Suggest again.",
    recovery: "edit_answers",
  },
  no_suggestions: {
    title: "There are no suggestions here to explain",
    action: "Add to your answers with Edit answers directly. Nessa then offers Suggest again.",
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
    action: "Nessa doesn't write it again for the same suggestions.",
    recovery: "suggest_again",
  },
};

export const ERROR_STATEMENT = Object.fromEntries(
  (Object.keys(ERROR_WORDS) as ErrorCode[]).map((code) => [
    code,
    { ...ERROR_WORDS[code], tone: ERROR_TONE[code] },
  ]),
) as Record<ErrorCode, ErrorStatement>;
