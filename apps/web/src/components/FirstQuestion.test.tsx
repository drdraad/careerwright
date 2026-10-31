// The first question and "Which of these is closest?" against a scripted API (Task 6d slice B;
// S2.8): any UK title is offered as the person types, marked as the UK job-title index's; their
// own words are always offered and kept exactly as typed; the closest step shows every group,
// none picked, and "None of these is my job" never asks for another job.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import type {
  ClosestOut,
  ProfileDocument,
  ProfileOut,
  TitleMatchesOut,
  TitleMatchOut,
  UkTitleOut,
} from "@/generated/api";
import { fakeApi, type Sent } from "@/test/fakeApi";
import { ClosestQuestion, FirstQuestion } from "./FirstQuestion";

const WS = "w-first";
const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const profile: ProfileOut = {
  workspace_id: WS,
  version: 3,
  document: Object.fromEntries(
    [
      "preferred_name",
      "current_role",
      "cities",
      "target_titles",
      "weekly_study_hours",
      "direct_spend_cap",
      "monthly_payment_cap",
      "enjoyed_tasks",
      "confident_tasks",
      "evidenced_tasks",
      "work_style",
      "minimum_salary",
    ].map((name) => [name, unasked]),
  ) as unknown as ProfileDocument,
  created_by: null,
  created_at: "2026-10-31T12:00:00Z",
} as ProfileOut;

const release = { dataset_id: "esco-v1.2.1-en-csv", sample: false } as TitleMatchesOut["release"];
const esco = (label: string, title = label): TitleMatchOut => ({
  source: "esco",
  concept_id: `c-${title}`,
  concept_kind: "esco",
  title,
  matched_label: label,
  label_kind: label === title ? "preferred" : "alternative",
  isco_group: { code: "3512", label: "ICT user support technicians" },
});
const uk = (title: string, codes: string[]): UkTitleOut => ({
  source: "uk_title_index",
  title,
  soc_codes: ["2235"],
  isco_groups: codes.map((code) => ({ code, label: null })),
});
const found = (
  query: string,
  matches: TitleMatchesOut["matches"],
  partial = false,
): TitleMatchesOut => ({
  release,
  query,
  matches,
  total: matches.filter((m) => m.source === "esco").length,
  uk_total: matches.filter((m) => m.source === "uk_title_index").length,
  limit: 8,
  partial,
});

function wrap(children: ReactNode) {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queries}>{children}</QueryClientProvider>);
  return userEvent.setup();
}

function api(answers: Record<string, TitleMatchesOut>): Sent[] {
  return fakeApi([
    {
      method: "GET",
      path: /\/v1\/taxonomy\/titles$/,
      answer: (sent) => {
        const q = new URLSearchParams(sent.query).get("q") ?? "";
        return answers[q] ?? found(q, []);
      },
    },
    { method: "POST", path: /\/origin\/role\/title$/, status: 201, answer: profile },
    { method: "POST", path: /\/origin\/role$/, status: 201, answer: profile },
    { method: "POST", path: /\/origin\/role\/closest$/, status: 201, answer: profile },
  ]);
}

const field = () => screen.getByRole("combobox", { name: "Your job title" });

describe("[DIV1-13] the first question finds any UK title, and keeps the person's own words", () => {
  it("offers a UK job title marked as the index's, and saves it in its words", async () => {
    const sent = api({
      "Registered nurse": found("Registered nurse", [uk("Registered nurse", ["2221"])]),
    });
    const answered = vi.fn();
    const user = wrap(
      <FirstQuestion workspaceId={WS} profile={profile} onSkip={() => {}} onAnswered={answered} />,
    );

    expect(
      screen.getByRole("heading", { name: "What do you do now, or what did you do last?" }),
    ).toBeVisible();
    await user.type(field(), "Registered nurse");
    const list = await screen.findByRole("listbox", { name: "Your job title" });
    const listed = await within(list).findByRole("option", {
      name: /^Registered nurse\s*,\s*UK job title \(ONS\)$/,
    });
    expect(within(listed).getByText("UK job title (ONS)")).toBeVisible();
    // The person's own words are always the last option.
    const options = within(list).getAllByRole("option");
    expect(options.at(-1)).toHaveTextContent("Use my own words: “Registered nurse”");

    await user.click(listed);
    await waitFor(() => expect(sent.some((s) => s.method === "POST")).toBe(true));
    expect(sent.find((s) => s.method === "POST")).toMatchObject({
      path: `/v1/workspaces/${WS}/origin/role/title`,
      body: { expected_version: 3, title: "Registered nurse" },
    });
    expect(answered).toHaveBeenCalledOnce();
  });

  it("saves an ESCO title by its occupation and keeps the label the person picked", async () => {
    const sent = api({
      "IT support": found("IT support", [esco("IT support technician", "ICT help desk agent")]),
    });
    const user = wrap(<FirstQuestion workspaceId={WS} profile={profile} onSkip={() => {}} />);

    await user.type(field(), "IT support");
    const option = await screen.findByRole("option", { name: /IT support technician/ });
    expect(within(option).getByText("In ESCO as ICT help desk agent")).toBeVisible();
    // The keyboard picks too: down to the first title, then Enter.
    await user.keyboard("{ArrowDown}{ArrowUp}{Enter}");

    await waitFor(() => expect(sent.some((s) => s.method === "POST")).toBe(true));
    expect(sent.find((s) => s.method === "POST")).toMatchObject({
      path: `/v1/workspaces/${WS}/origin/role`,
      body: {
        expected_version: 3,
        concept_id: "c-ICT help desk agent",
        label: "IT support technician",
      },
    });
  });

  it("asks about ESCO's closest titles when no list holds every word, and None of these keeps the typed words", async () => {
    const sent = api({
      "Bookkeeping assistant": found("Bookkeeping assistant", [esco("bookkeeper")], true),
    });
    const user = wrap(<FirstQuestion workspaceId={WS} profile={profile} onSkip={() => {}} />);

    await user.type(field(), "Bookkeeping assistant");
    expect(
      await screen.findByText(
        "Careerwright couldn't match that title in ESCO. Is it one of these?",
      ),
    ).toBeVisible();
    const own = screen.getByRole("option", { name: /None of these is my job/ });
    expect(own).toHaveTextContent("Use my own words: “Bookkeeping assistant”");

    await user.click(own);
    await waitFor(() => expect(sent.some((s) => s.method === "POST")).toBe(true));
    // Design review I-2: the refusal is recorded, so nothing later asks for another job.
    expect(sent.find((s) => s.method === "POST")).toMatchObject({
      path: `/v1/workspaces/${WS}/origin/role/title`,
      body: { expected_version: 3, title: "Bookkeeping assistant", none_of_these: true },
    });
  });

  it("refuses nothing typed: with no title found, the person's own words are still offered", async () => {
    const sent = api({});
    const user = wrap(<FirstQuestion workspaceId={WS} profile={profile} onSkip={() => {}} />);

    await user.type(field(), "Orbital gardener");
    expect(
      await screen.findByText("Careerwright found no job title holding those words."),
    ).toBeVisible();
    await user.click(screen.getByRole("option", { name: "Use my own words: “Orbital gardener”" }));
    await waitFor(() => expect(sent.some((s) => s.method === "POST")).toBe(true));
    expect(sent.find((s) => s.method === "POST")?.body).toEqual({
      expected_version: 3,
      title: "Orbital gardener",
    });
  });

  it("goes on without an answer when the person skips, saving nothing", async () => {
    const sent = api({});
    const skipped = vi.fn();
    const user = wrap(<FirstQuestion workspaceId={WS} profile={profile} onSkip={skipped} />);

    await user.click(screen.getByRole("button", { name: "Skip for now" }));
    expect(skipped).toHaveBeenCalledOnce();
    expect(sent.filter((s) => s.method !== "GET")).toEqual([]);
  });
});

const closest = (groups: ClosestOut["groups"]): ClosestOut => ({
  decision: "not_yet",
  groups,
  chosen: null,
});

describe("[DIV1-14] which ESCO occupation is closest, or none of them", () => {
  it("shows every group ONS codes the title to, none picked, and records the person's choice", async () => {
    const sent = api({});
    const user = wrap(
      <ClosestQuestion
        workspaceId={WS}
        profile={profile}
        title="Nurse"
        closest={closest([
          {
            group: { code: "2221", label: "Nursing professionals" },
            occupations: [
              { concept_id: "c1", title: "nurse responsible for general care", esco_uri: "u1" },
              { concept_id: "c2", title: "specialist nurse", esco_uri: "u2" },
            ],
          },
          { group: { code: "2421", label: null }, occupations: [] },
        ])}
      />,
    );

    expect(screen.getByRole("heading", { name: "Which of these is closest?" })).toBeVisible();
    expect(
      screen.getByText(
        "Careerwright found “Nurse” in the UK job-title index and looked up the ESCO occupations in the groups it's in.",
      ),
    ).toBeVisible();
    const nursing = screen.getByRole("region", { name: "Nursing professionals (ISCO-08 2221)" });
    expect(within(nursing).getAllByRole("button")).toHaveLength(2);
    const empty = screen.getByRole("region", { name: "ISCO-08 group 2421" });
    expect(
      within(empty).getByText("Careerwright found no ESCO occupation in this group."),
    ).toBeVisible();
    for (const button of within(nursing).getAllByRole("button")) {
      expect(button).not.toHaveClass("btn-primary"); // none picked for them
    }

    await user.click(within(nursing).getByRole("button", { name: "specialist nurse" }));
    await waitFor(() => expect(sent.some((s) => s.method === "POST")).toBe(true));
    expect(sent.find((s) => s.method === "POST")).toMatchObject({
      path: `/v1/workspaces/${WS}/origin/role/closest`,
      body: { expected_version: 3, concept_id: "c2" },
    });
  });

  it("records None of these is my job as no occupation, and shows a long group a few at a time", async () => {
    const sent = api({});
    const many = Array.from({ length: 15 }, (_, n) => ({
      concept_id: `c${n}`,
      title: `occupation ${String(n).padStart(2, "0")}`,
      esco_uri: `u${n}`,
    }));
    const user = wrap(
      <ClosestQuestion
        workspaceId={WS}
        profile={profile}
        title="Manager"
        closest={closest([
          { group: { code: "1324", label: "Supply managers" }, occupations: many },
        ])}
      />,
    );

    const group = screen.getByRole("region", { name: "Supply managers (ISCO-08 1324)" });
    expect(within(group).getAllByRole("button", { name: /^occupation/ })).toHaveLength(12);
    await user.click(within(group).getByRole("button", { name: "Show 3 more" }));
    expect(within(group).getAllByRole("button", { name: /^occupation/ })).toHaveLength(15);

    await user.click(screen.getByRole("button", { name: "None of these is my job" }));
    await waitFor(() => expect(sent.some((s) => s.method === "POST")).toBe(true));
    expect(sent.find((s) => s.method === "POST")?.body).toEqual({
      expected_version: 3,
      concept_id: null,
    });
  });
});
