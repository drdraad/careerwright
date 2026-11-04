// Synthetic Roles states for reviewing a selected target, an unresolved title and openings.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Openings, RoleCard } from "@/components/RolesChapter";
import type {
  JobOut,
  JobPage,
  OccupationEvidenceOut,
  OccupationOut,
  TargetRecordOut,
} from "@/generated/api";

const meta: Meta = { title: "Roles", parameters: { surface: "reading" } };
export default meta;
type Story = StoryObj;

const target: TargetRecordOut = {
  key: "lab technician",
  title: "Lab technician",
  kind: "esco",
  link: "occupation_choice",
  concept_id: "o-lab",
  label_matches: 1,
  coverage: "pack_target",
  pack_target_id: "P01",
  on_a_list: true,
};
const occupation: OccupationOut = {
  concept_id: "o-lab",
  concept_kind: "esco",
  esco_uri: "https://data.europa.eu/esco/occupation/o-lab",
  esco_code: "o-lab",
  preferred_label: "Laboratory technician",
  alternative_labels: ["Scientific laboratory technician", "Lab assistant"],
  description: "Prepare samples, maintain laboratory equipment and record test results.",
  regulated: null,
  isco_groups: [{ code: "3111", label: "Chemical and physical science technicians" }],
  broader_concept_id: null,
  skills: [
    {
      skill_id: "s1",
      preferred_label: "prepare samples",
      skill_type: "skill",
      relation: "essential",
    },
  ],
  attribution: "ESCO",
  adaptation: "Shortened for this demonstration",
};
const evidence = {
  concept_id: "o-lab",
  title: "Laboratory technician",
  esco_uri: occupation.esco_uri,
  regions: [{ code: "E12000002", name: "North West" }],
  uk_soc: {
    isco_code: "3111",
    resolution: "single_candidate",
    review_state: "unreviewed",
    proposed_soc_code: "3111",
    reviewed_soc_code: null,
    reviewer: null,
    reviewed_on: null,
    candidates: [],
  },
  modelled_pay: null,
  modelled_pay_unavailable: "no_reviewed_mapping",
  trend: { state: "unavailable", reason: "single_snapshot" },
  ai_evidence: { state: "no_evidence", ilo: null, observed_use: [] },
  ai_resilience: {
    state: "unscored",
    unscored_reason: "no_record",
    lower: null,
    upper: null,
    bands: [],
    band_words: [],
    evidence_quality: null,
    synthetic: false,
    synthetic_label: null,
    pack_version: "demo-v1",
    pack_dated: "2026-11-01",
  },
  releases: [],
} satisfies OccupationEvidenceOut;
const job = {
  job_id: "j1",
  title: "Laboratory technician apprentice",
  employer: "North Labs",
  locations: [{ label: "Manchester" }],
  salary: {
    currency: "GBP",
    minimum_minor_units: 2200000,
    maximum_minor_units: 2400000,
    period: "year",
    basis: "advertised",
  },
  salary_confirmed: true,
  employment_type: "Apprenticeship",
  exemplar: false,
  freshness: { label: "Current" },
  copies: [
    {
      provider: "Adzuna",
      source_url: "https://example.com/lab",
      retrieved_at: "2026-11-01T12:00:00Z",
    },
  ],
} as JobOut;
const jobs = {
  items: [
    job,
    {
      ...job,
      job_id: "j2",
      title: "Care assistant",
      employer: null,
      locations: [{ label: "Leeds" }],
      salary: {
        currency: "GBP",
        minimum_minor_units: 1900000,
        maximum_minor_units: null,
        period: "year",
        basis: "predicted",
      },
      salary_confirmed: false,
      employment_type: null,
    },
  ],
  total_jobs: 2,
  exemplars: 0,
  empty_reason: null,
  next_cursor: null,
} as JobPage;

export const SelectedTarget: Story = {
  render: () => (
    <div className="chapter on-reading chapter-panel grid gap-24">
      <RoleCard title={target.title} target={target} occupation={occupation} evidence={evidence} />
      <Openings data={jobs} />
    </div>
  ),
};

export const UnresolvedTitle: Story = {
  render: () => (
    <div className="chapter on-reading chapter-panel">
      <RoleCard
        title="My own specialist title"
        target={{
          ...target,
          title: "My own specialist title",
          concept_id: null,
          coverage: "not_covered",
        }}
      />
    </div>
  ),
};

export const NoSourcesFetched: Story = {
  render: () => (
    <div className="chapter on-reading chapter-panel">
      <Openings data={{ ...jobs, items: [], total_jobs: 0, empty_reason: "no_source_retrieved" }} />
    </div>
  ),
};
