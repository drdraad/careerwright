// Story data. Every amount, date and name that stands for a person comes from the supplied
// synthetic fixture pack (P01 and TRACE-01), never typed into a component; the extra
// long-label and three-target cases say so where they are built.
import type {
  ProfileDocument,
  ProfileOut,
  SourceOut,
  TargetRecordOut,
  WorkspaceOut,
} from "@/generated/api";
import { previewFromTrace, type RoutePreview, TRACE_SHA256 } from "@/lib/fixtures/trace";
import persona from "../../../../fixtures/m0/personas/P01.json";
import trace from "../../../../fixtures/m0/worked_trace.json";

const SOURCE_ID = "8d1f6f8e-46a1-5c2b-9d0e-3f7a1b2c4d5e";

export const fixtureSource: SourceOut = {
  source_ref_id: SOURCE_ID,
  kind: "fixture",
  label: "Synthetic fixture persona P01 (supplied M0 pack)",
  locator: "fixtures/m0/personas/P01.json",
  content_sha256: "03e72eefa7f975fc50c075a17f2136a0f39385efce25ccdb2834b5f9a5ec518e",
  recorded_by: null,
  observed_at: `${persona.data_as_of}T00:00:00Z`,
  created_at: `${persona.data_as_of}T00:00:00Z`,
};

export const directSource: SourceOut = {
  ...fixtureSource,
  source_ref_id: "5b0c3a7e-1111-4d2c-8e9f-0a1b2c3d4e5f",
  kind: "direct_entry",
  label: "Entered directly in Careerwright",
  locator: null,
  content_sha256: null,
};

const gbp = (minor: number) => ({ minor_units: minor, currency: "GBP" as const });

/** P01's practical inputs as the API holds them after seeding. */
export const p01Document: ProfileDocument = {
  schema_version: "4",
  work_status: { state: "unasked", value: null, source_ref_id: null },
  qualifications: { state: "unasked", value: null, source_ref_id: null },
  preferred_name: { state: "unasked", value: null, source_ref_id: null },
  current_role: { state: "unasked", value: null, source_ref_id: null },
  enjoyed_tasks: { state: "unasked", value: null, source_ref_id: null },
  confident_tasks: { state: "unasked", value: null, source_ref_id: null },
  evidenced_tasks: { state: "unasked", value: null, source_ref_id: null },
  work_style: { state: "unasked", value: null, source_ref_id: null },
  minimum_salary: { state: "unasked", value: null, source_ref_id: null },
  cities: { state: "provided", value: persona.cities, source_ref_id: SOURCE_ID },
  target_titles: { state: "provided", value: persona.target_titles, source_ref_id: SOURCE_ID },
  weekly_study_hours: { state: "unasked", value: null, source_ref_id: null },
  direct_spend_cap: {
    state: "provided",
    value: gbp(persona.direct_spend_cap_minor),
    source_ref_id: SOURCE_ID,
  },
  monthly_payment_cap: {
    state: "provided",
    value: gbp(persona.monthly_payment_cap_minor),
    source_ref_id: SOURCE_ID,
  },
};

/** Unknown and declined answers: the budget is not confirmed, never shown as £0. */
export const unknownDocument: ProfileDocument = {
  ...p01Document,
  direct_spend_cap: { state: "unknown", value: null, source_ref_id: SOURCE_ID },
  monthly_payment_cap: { state: "prefer_not_to_say", value: null, source_ref_id: SOURCE_ID },
  weekly_study_hours: { state: "skipped", value: null, source_ref_id: SOURCE_ID },
};

/** Long labels and the three-target maximum (labels invented for layout testing only). */
export const longDocument: ProfileDocument = {
  ...p01Document,
  target_titles: {
    state: "provided",
    value: [
      persona.target_titles[0] ?? "",
      "Senior data governance and information quality manager",
      "Clinical data standards and interoperability specialist",
    ],
    source_ref_id: SOURCE_ID,
  },
  cities: {
    state: "provided",
    value: ["Manchester", "Newcastle upon Tyne", "Kingston upon Hull"],
    source_ref_id: SOURCE_ID,
  },
};

/** A document's targets as the API stores them, each once (story data: the key the API would
 *  give these titles, which have no punctuation, plurals or accents, is their lower case). The
 *  first of P01's is one of the option pack's targets. */
export function storedTargets(document: ProfileDocument): TargetRecordOut[] {
  const titles = document.target_titles.value ?? [];
  return titles.map((title) => ({
    key: title.toLowerCase(),
    title,
    kind: "own_words",
    link: title === persona.target_titles[0] ? "pack_crosswalk" : "none",
    concept_id: null,
    label_matches: 0,
    coverage: title === persona.target_titles[0] ? "pack_target" : "not_covered",
    pack_target_id: title === persona.target_titles[0] ? "data-quality-analyst-manchester" : null,
    on_a_list: false, // the pack covers the first by its crosswalk, not its title
  }));
}

export function profile(document: ProfileDocument, version = 1): ProfileOut {
  return {
    workspace_id: "74fa4514-899d-5316-80fd-4161dc0dbda0",
    version,
    document,
    created_by: null,
    created_at: `${persona.data_as_of}T00:00:00Z`,
  };
}

export const fixtureWorkspace: WorkspaceOut = {
  workspace_id: "74fa4514-899d-5316-80fd-4161dc0dbda0",
  name: "P01 demo (synthetic)",
  data_mode: "demo",
  synthetic: true,
  fixture: true,
  version: 1,
  last_event_seq: 1,
  created_at: `${persona.data_as_of}T00:00:00Z`,
  updated_at: `${persona.data_as_of}T00:00:00Z`,
};

export const longWorkspace: WorkspaceOut = {
  ...fixtureWorkspace,
  name: "A workspace with a deliberately long name to check that the strip wraps instead of overflowing",
};

/** The real adapter mapping over the pack file's content (the hash is checked on the server). */
export const routePreview: RoutePreview = previewFromTrace(JSON.stringify(trace), TRACE_SHA256);

export const failedPreview: RoutePreview = {
  state: "failed",
  reason: "checksum_mismatch",
  locator: "fixtures/m0/worked_trace.json",
};
