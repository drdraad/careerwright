// Research this role (Task 6e; DIV1-15, ADR 0015 decision 2): the estimated cost before it
// starts, only the title sent, the pages read once the search is done, a stop while it runs,
// and the API's result worded: found or not yet found in independent sources, with the
// quotes and dates one step away. A found title idea becomes a target only by the person's
// click. Every title and page here is synthetic.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import type {
  ProfileOut,
  RoleOut,
  RoleResearchOut,
  RunEstimateOut,
  SlateOut,
  TargetRecordOut,
} from "@/generated/api";
import { ROLE_RESEARCH } from "@/lib/vocabulary";
import { fakeApi, type Route } from "@/test/fakeApi";
import { researchable } from "./Directions";
import { type ResearchTitle, RoleResearchList } from "./RoleResearch";

const WS = "w-research";
const TITLE = "Orbital hydroponics technician";
const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const profile: ProfileOut = {
  workspace_id: WS,
  version: 3,
  created_by: null,
  created_at: "2026-11-01T00:00:00Z",
  document: {
    schema_version: "4",
    work_status: unasked,
    qualifications: unasked,
    preferred_name: unasked,
    current_role: unasked,
    cities: unasked,
    target_titles: unasked,
    weekly_study_hours: unasked,
    direct_spend_cap: unasked,
    monthly_payment_cap: unasked,
    enjoyed_tasks: { state: "provided", value: ["growing plants"], source_ref_id: "s1" },
    confident_tasks: unasked,
    evidenced_tasks: unasked,
    work_style: unasked,
    minimum_salary: unasked,
  },
};
const estimate: RunEstimateOut = {
  kind: "source_search",
  model_id: "muse-spark-1.3",
  model_mode: "standard",
  per_run_nano_usd: 45_125_000,
  hard_maximum_nano_usd: 150_000_000,
  refused_scope: null,
};
const run = (run_id: string, status = "complete") =>
  ({ run_id, status, cancel_requested_at: null }) as unknown as RoleResearchOut["search"];
const page = (
  position: number,
  host: string,
  verified: boolean | null,
  source: number | null,
): RoleResearchOut["pages"][number] => ({
  position,
  url: `https://${host}/role`,
  host,
  status: verified === null ? "failed" : "succeeded",
  reason: verified === null ? "timeout" : null,
  rights_class: "other",
  retrieved_at: verified === null ? null : "2026-11-01T10:00:00Z",
  title_verified: verified,
  quote: verified ? `${TITLE} wanted at our Leeds growing hub.` : null,
  source,
});
const research = (over: Partial<RoleResearchOut>): RoleResearchOut => ({
  research_id: "r1",
  title: TITLE,
  review_state: "proposed",
  created_at: "2026-11-01T09:00:00Z",
  state: "searching",
  not_yet_found_reason: null,
  sources: 0,
  official: false,
  candidates: 0,
  empty_reason: null,
  search: run("s1", "running"),
  reading: null,
  pages: [],
  ...over,
});

afterEach(cleanup);

function shown(
  researches: RoleResearchOut[],
  extra: Route[] = [],
  titles: ResearchTitle[] = [{ title: TITLE, why: "idea" }],
) {
  const sent = fakeApi([
    { method: "GET", path: /\/role-research$/, answer: researches },
    { method: "GET", path: /\/spend\/estimate$/, answer: estimate },
    ...extra,
  ]);
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <RoleResearchList workspaceId={WS} profile={profile} titles={titles} canWrite />
    </QueryClientProvider>,
  );
  return { sent, user: userEvent.setup() };
}

describe("[DIV1-15][MODEL-08] research this role", () => {
  it("shows the estimated cost first, then sends only the title, on the version shown", async () => {
    const { sent, user } = shown(
      [],
      [{ method: "POST", path: /\/role-research$/, status: 202, answer: research({}) }],
    );

    expect(await screen.findByText(/This can cost up to \$0\.05 on your Meta key\./)).toBeVisible();
    expect(
      // The title may be the person's own role, so "nothing else" (review M7).
      screen.getByText(/It sends only the title and “England”, nothing else about you\./),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: ROLE_RESEARCH.start }));

    await waitFor(() => expect(sent.some((s) => s.method === "POST")).toBe(true));
    const started = sent.find((s) => s.method === "POST");
    expect(started?.path).toBe(`/v1/workspaces/${WS}/role-research`);
    expect(started?.body).toEqual({ expected_profile_version: 3, title: TITLE });
  });

  it("reads the pages once the search is done, asking once", async () => {
    const ready = research({ state: "ready_to_read", search: run("s1"), candidates: 3 });
    const { sent } = shown(
      [ready],
      [
        {
          method: "POST",
          path: /\/role-research\/r1\/reading$/,
          status: 202,
          answer: research({ state: "reading", search: run("s1"), reading: run("a1", "running") }),
        },
      ],
    );

    await waitFor(() =>
      expect(sent.filter((s) => s.path.endsWith("/role-research/r1/reading"))).toHaveLength(1),
    );
    expect(screen.getByText(ROLE_RESEARCH.state.ready_to_read)).toBeVisible();
  });

  it("can be stopped while it runs", async () => {
    const { sent, user } = shown(
      [research({})],
      [{ method: "POST", path: /\/runs\/s1\/cancel$/, status: 202, answer: {} }],
    );

    await user.click(await screen.findByRole("button", { name: ROLE_RESEARCH.cancel }));

    await waitFor(() =>
      expect(sent.some((s) => s.path === `/v1/workspaces/${WS}/runs/s1/cancel`)).toBe(true),
    );
  });

  it("says found in independent sources, with each quote and date one step away", async () => {
    const found = research({
      state: "found",
      sources: 2,
      search: run("s1"),
      reading: run("a1"),
      pages: [
        page(0, "careers.northwind.example", true, 1),
        page(1, "growers.guild.example", true, 2),
      ],
    });
    shown([found]);

    expect(await screen.findByText(ROLE_RESEARCH.state.found)).toBeVisible();
    expect(
      screen.getByText(
        "Careerwright found the title, word for word, on pages from 2 independent sources.",
      ),
    ).toBeVisible();
    const pages = screen.getByText(ROLE_RESEARCH.pages).closest("details");
    expect(pages).not.toBeNull();
    const list = within(pages as HTMLElement);
    expect(list.getAllByText(/Read on 1 November 2026/)).toHaveLength(2);
    expect(list.getAllByText(`“${TITLE} wanted at our Leeds growing hub.”`)).toHaveLength(2);
    expect(list.getByText(ROLE_RESEARCH.checkedOnly)).toBeInTheDocument();
  });

  it("makes a found title idea a target only by the person's click", async () => {
    const found = research({ state: "found", sources: 2, search: run("s1"), reading: run("a1") });
    const { sent, user } = shown(
      [found],
      [{ method: "PUT", path: /\/profile$/, status: 201, answer: { ...profile, version: 4 } }],
    );

    await user.click(await screen.findByRole("button", { name: ROLE_RESEARCH.makeTarget }));

    await waitFor(() => expect(sent.some((s) => s.method === "PUT")).toBe(true));
    const saved = sent.find((s) => s.method === "PUT")?.body as {
      expected_version: number;
      profile: { target_titles: unknown };
    };
    expect(saved.expected_version).toBe(3);
    expect(saved.profile.target_titles).toEqual({ state: "provided", value: [TITLE] });
  });

  it("says not yet found in independent sources, and counts a page it couldn't read apart", async () => {
    const one = research({
      state: "not_yet_found",
      not_yet_found_reason: "one_source_only",
      sources: 1,
      search: run("s1"),
      reading: run("a1"),
      pages: [page(0, "careers.northwind.example", true, 1), page(1, "slow.example", null, null)],
    });
    shown([one]);

    expect(await screen.findByText(ROLE_RESEARCH.state.not_yet_found)).toBeVisible();
    expect(screen.getByText(ROLE_RESEARCH.notYetFound.one_source_only)).toBeVisible();
    expect(screen.getByText(ROLE_RESEARCH.unread(1))).toBeVisible();
    expect(screen.queryByRole("button", { name: ROLE_RESEARCH.makeTarget })).toBeNull();
  });

  it("never offers to make the person's own title a target again", async () => {
    const found = research({ state: "found", sources: 2, search: run("s1"), reading: run("a1") });
    shown([found], [], [{ title: TITLE, why: "role" }]);

    expect(await screen.findByText(ROLE_RESEARCH.state.found)).toBeVisible();
    expect(screen.queryByRole("button", { name: ROLE_RESEARCH.makeTarget })).toBeNull();
  });
});

describe("[DIV1-15] which titles can be researched", () => {
  const idea = (title: string, reason: SlateOut["title_ideas"][number]["reason"]) =>
    ({ title, reason }) as SlateOut["title_ideas"][number];
  const target = (title: string, kind: TargetRecordOut["kind"], on_a_list = kind !== "own_words") =>
    ({ title, kind, on_a_list }) as TargetRecordOut;
  const role = (text: string, kind: RoleOut["kind"], on_a_list = kind !== "own_words") =>
    ({ kind, text, on_a_list }) as RoleOut;

  it("takes the role and targets in the person's own words and the ideas not yet found", () => {
    expect(
      researchable(
        role("Client onboarding assistant", "own_words"),
        [target("Prompt engineer", "ons"), target("Orbital gardener", "own_words")],
        [
          idea("data analyst", "in_esco"),
          idea("Prompt engineer", "in_uk_title_index"),
          idea(TITLE, "not_yet_found"),
          idea("calm person", "not_searched"),
        ],
      ),
    ).toEqual([
      { title: "Client onboarding assistant", why: "role" },
      { title: TITLE, why: "idea" },
      { title: "Orbital gardener", why: "target" },
    ]);
  });

  it("takes nothing a list holds, own words that ESCO or the option pack holds included", () => {
    // Kept in the person's words, but ESCO holds the title as a label (review M2): the API
    // says so, and the research would be refused.
    expect(
      researchable(
        role("Data analyst", "own_words", true),
        [target("data analyst", "esco"), target("Bookkeeping assistant", "own_words", true)],
        [],
      ),
    ).toEqual([]);
    expect(researchable(role("Prompt engineer", "ons"), [], [])).toEqual([]);
  });

  it("keeps a title Careerwright thought of as its idea once it is made a target", () => {
    // Review M3: never "Your target, in your words" for a model's idea.
    expect(
      researchable(undefined, [target(TITLE, "own_words")], [idea(TITLE, "not_yet_found")]),
    ).toEqual([{ title: TITLE, why: "idea" }]);
  });
});
