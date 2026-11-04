import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type {
  JobOut,
  JobPage,
  OccupationEvidenceOut,
  ProfileOut,
  TargetRecordOut,
} from "@/generated/api";
import { fakeApi } from "@/test/fakeApi";
import { Openings, RoleCard, RolesChapter } from "./RolesChapter";

const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const profile: ProfileOut = {
  workspace_id: "w-roles",
  version: 2,
  created_by: null,
  created_at: null,
  document: {
    schema_version: "5",
    preferred_name: unasked,
    current_role: unasked,
    cities: unasked,
    target_titles: unasked,
    weekly_study_hours: unasked,
    direct_spend_cap: unasked,
    monthly_payment_cap: unasked,
    enjoyed_tasks: unasked,
    confident_tasks: unasked,
    evidenced_tasks: unasked,
    work_style: unasked,
    minimum_salary: unasked,
    work_status: unasked,
    qualifications: unasked,
    disliked_tasks: unasked,
  },
};
const target: TargetRecordOut = {
  key: "lab technician",
  title: "Lab technician",
  kind: "own_words",
  link: "none",
  concept_id: null,
  label_matches: 0,
  coverage: "not_covered",
  pack_target_id: null,
  on_a_list: false,
};
const freshness: JobOut["freshness"] = {
  kind: "job",
  state: "current",
  label: "Current",
  usable_as_current: true,
  last_attempt_at: null,
  last_success_at: "2026-11-01T12:00:00Z",
  valid_until: "2026-11-08T12:00:00Z",
  verified_until: null,
  max_age_hours: 168,
};
const baseJob: JobOut = {
  job_id: "j1",
  title: "Lab technician apprentice",
  employer: "North Labs",
  advertiser: "employer",
  locations: [{ label: "Manchester" }],
  work_mode: null,
  salary: {
    currency: "GBP",
    minimum_minor_units: 2200000,
    maximum_minor_units: 2400000,
    period: "year",
    basis: "advertised",
  },
  salary_confirmed: true,
  employment_type: "Apprenticeship",
  date_posted: "2026-11-01",
  description_kind: null,
  exemplar: false,
  favourite: false,
  first_seen_at: "2026-11-01T12:00:00Z",
  freshness,
  copies: [
    {
      copy_id: "c1",
      attempt_id: "a1",
      provider: "Adzuna",
      route: "adzuna",
      source_url: "https://example.com/job",
      source_job_id: "job-1",
      description_kind: null,
      rights_status: null,
      retrieved_at: "2026-11-01T12:00:00Z",
    },
  ],
};
const jobs: JobPage = {
  items: [
    baseJob,
    {
      ...baseJob,
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
  next_cursor: null,
  total_jobs: 2,
  salary_floor: null,
  exemplars: 0,
  city_counts: { Manchester: 1, Leeds: 1 },
  coverage: {},
  adverts: null,
  empty_reason: null,
  acquisition_model_spend: null,
};

function shown(targets: TargetRecordOut[] = [], openings = jobs) {
  fakeApi([
    { method: "GET", path: /\/targets$/, answer: { profile_version: 2, targets } },
    { method: "GET", path: /\/discoveries$/, answer: { items: [], next_cursor: null } },
    { method: "GET", path: /\/jobs$/, answer: openings },
  ]);
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queries}>
      <RolesChapter workspaceId="w-roles" profile={profile} />
    </QueryClientProvider>,
  );
}

describe("Roles journey", () => {
  it("gives a clear choice when no role is settled", async () => {
    shown();
    expect(await screen.findByRole("link", { name: "Choose a role in You" })).toHaveAttribute(
      "href",
      "/w/w-roles/you",
    );
  });

  it("shows a chosen role and leaves unsupported evidence unknown", async () => {
    shown([target]);
    expect(await screen.findByRole("heading", { name: "Lab technician" })).toBeVisible();
    expect(screen.getByText(/cannot show a checked workday or skills/)).toBeVisible();
    expect(screen.getByText(/Outlook: not enough evidence yet/)).toBeVisible();
  });

  it("gives a research action without claiming an empty workspace means no vacancies", async () => {
    shown([target], { ...jobs, items: [], total_jobs: 0 });
    expect(
      await screen.findByText(/Check current vacancies on employers' own sites/),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "Skills" })).toHaveAttribute(
      "href",
      "/w/w-roles/skills",
    );
    expect(screen.getByText(/No live opening has been checked here/)).toBeVisible();
  });

  it("shares area and title filters between the list and pay lens", async () => {
    render(<Openings data={jobs} />);
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Area" }), "Manchester");
    expect(screen.getByText("Showing 1 of 2 loaded adverts.")).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Pay lens" }));
    expect(
      within(screen.getByRole("region", { name: "Advertised pay" })).getByText(
        "Lab technician apprentice",
      ),
    ).toBeVisible();
    expect(screen.queryByText("Care assistant")).not.toBeInTheDocument();
    expect(screen.getByText(/Apprenticeship/)).toBeVisible();
    expect(screen.getByText(/captured 2026-11-01/)).toBeVisible();
  });

  it("maps loaded areas to employers and keeps the selected opening across views", async () => {
    render(<Openings data={jobs} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Opportunity map" }));
    const map = within(screen.getByRole("region", { name: "Opportunity map" }));
    expect(map.getByText(/not distance or commute time/)).toBeVisible();
    expect(map.getByRole("button", { name: "Manchester" })).toBeVisible();
    await user.click(map.getByRole("button", { name: "Leeds" }));
    expect(screen.getByText("Showing 1 of 2 loaded adverts.")).toBeVisible();
    expect(map.getByRole("button", { name: "Care assistant" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await user.click(screen.getByRole("button", { name: "Pay lens" }));
    expect(
      within(screen.getByRole("region", { name: "Predicted pay" })).getByText("Care assistant"),
    ).toBeVisible();
    expect(screen.getByText(/Selected advert/)).toBeVisible();
  });

  it("does not turn an empty source search into a claim there are no jobs", () => {
    render(
      <Openings
        data={{ ...jobs, items: [], total_jobs: 0, empty_reason: "no_source_retrieved" }}
      />,
    );
    expect(screen.getByText(/None of the sources could be fetched/)).toBeVisible();
    expect(screen.getByText(/This isn't a sign there are no vacancies/)).toBeVisible();
  });

  it("never labels a target's unreviewed pack as a fit", () => {
    render(<RoleCard title="Lab technician" target={target} />);
    expect(screen.getByText(/No reviewed route pack/)).toBeVisible();
    expect(screen.queryByText(/Matches your preferences/)).not.toBeInTheDocument();
  });

  it("labels a benchmark as the pay group's figure and a score as experimental", () => {
    const evidence: OccupationEvidenceOut = {
      concept_id: "o-lab",
      title: "Lab technician",
      esco_uri: "https://example.com/esco/lab",
      regions: [{ code: "NW", name: "North West" }],
      uk_soc: {
        isco_code: "3111",
        resolution: "single_candidate",
        review_state: "reviewed",
        proposed_soc_code: "3111",
        reviewed_soc_code: "3111",
        reviewer: "reviewer",
        reviewed_on: "2026-11-01",
        candidates: [],
      },
      modelled_pay: {
        basis: "modelled",
        soc_code: "3111",
        benchmarks: [
          {
            soc_code: "3111",
            soc_title: "Science technicians",
            region_code: "NW",
            region_name: "North West",
            geography: "region",
            population: "full_time",
            period: "year",
            pay_definition: "gross",
            jobs_thousands: null,
            statistics: [
              {
                statistic: "median",
                amount: { currency: "GBP", minor_units: 3000000 },
                withheld: null,
                cv: null,
                reliability: "precise",
              },
            ],
          },
        ],
      },
      modelled_pay_unavailable: null,
      trend: { state: "unavailable", reason: "single_snapshot" },
      ai_evidence: { state: "assessed", ilo: null, observed_use: [] },
      ai_resilience: {
        state: "published_range",
        unscored_reason: null,
        lower: 5,
        upper: 8,
        bands: [],
        band_words: [],
        evidence_quality: "limited",
        synthetic: true,
        synthetic_label: "Synthetic fixture range",
        pack_version: "p1",
        pack_dated: "2026-11-01",
      },
      releases: [],
    };
    render(<RoleCard title="Lab technician" target={target} evidence={evidence} />);
    expect(screen.getByText(/Science technicians.*£30,000/)).toHaveTextContent(
      "not pay for this exact title",
    );
    expect(screen.getByText(/AI Resilience Score: experimental 5–8 out of 10/)).toHaveTextContent(
      "Synthetic fixture range",
    );
    expect(screen.getByText("Outlook: not enough evidence yet.")).toBeVisible();
  });
});
