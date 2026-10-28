// How the shared state vocabulary reads in the UI (STATE-01, UI-04). The values come only from
// the generated client; these tables give each one words and a glyph. `Record<…>` over the
// generated unions makes a new API value a compile error here until it has words.

import type { GlyphName } from "@/components/Glyph";
import type { DataMode, ErrorCode, FieldState, ProfileInput, WorkState } from "@/generated/api";

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

type FieldKind = "text" | "list" | "hours" | "money";

/** Words for each profile field and, per spec section 3, what a missing answer makes less precise. */
export const PROFILE_FIELDS: Record<
  ProfileFieldName,
  { label: string; kind: FieldKind; hint: string; lessPrecise: string }
> = {
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
    hint: "Up to three English cities.",
    lessPrecise: "Roles, pay and listings: none can be searched without a work area.",
  },
  target_titles: {
    label: "Target roles",
    kind: "list",
    hint: "Up to three roles you are considering.",
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
};

export const PROFILE_FIELD_ORDER: readonly ProfileFieldName[] = [
  "target_titles",
  "cities",
  "current_role",
  "weekly_study_hours",
  "direct_spend_cap",
  "monthly_payment_cap",
  "preferred_name",
];

export type ErrorStatement = { title: string; action: string };

/** What the person sees for each API error code. The API's own message is never shown. */
export const ERROR_STATEMENT: Record<ErrorCode, ErrorStatement> = {
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
    action: "Open it at the address `make demo` printed.",
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
};
