// The person's own details beside a title (Task 6d slice C): seniority and industry, each
// optional and never a default, and the skills ESCO lists for the role's kind of work that the
// person marks "not part of my job", a display state. Nothing shows for a person who gave no
// title (the product owner, 1 November 2026: many people have never had a job).
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { OriginOut, SupportNoteOut, TitleDetailsListOut } from "@/generated/api";
import { fakeApi, type Route } from "@/test/fakeApi";
import { TitleDetails } from "./TitleDetails";

const WS = "w-titles";
const role = {
  title_use: "role" as const,
  title: "bookkeeper",
  seniority: null,
  industry: null,
  not_part_of_job: [],
  version: 0,
};
const target = { ...role, title_use: "target" as const, title: "Doula" };
const list = (...titles: TitleDetailsListOut["titles"]): TitleDetailsListOut => ({
  profile_version: 2,
  titles,
});
const usual = (skill_id: string, label: string, not_part_of_job = false) => ({
  skill_id,
  subject: `esco:${skill_id}`,
  label,
  skill_type: "skill/competence",
  state: "usual_in_role" as const,
  answer: null,
  evidence_id: null,
  not_part_of_job,
});
const origin = (skills: ReturnType<typeof usual>[]): OriginOut =>
  ({ usual_skills: skills }) as unknown as OriginOut;

function renderDetails(routes: Route[]) {
  const sent = fakeApi(routes);
  render(
    <QueryClientProvider client={new QueryClient()}>
      <TitleDetails workspaceId={WS} />
    </QueryClientProvider>,
  );
  return { user: userEvent.setup(), sent };
}

const get = (answer: TitleDetailsListOut): Route => ({
  method: "GET",
  path: /\/profile\/titles$/,
  answer,
});
const originRoute = (answer: OriginOut): Route => ({ method: "GET", path: /\/origin$/, answer });

describe("[PROF-11][MAP1-09] seniority and industry beside each title, and ESCO's list for the role", () => {
  it("shows nothing for a person who gave no title", async () => {
    const { sent } = renderDetails([get(list())]);
    await waitFor(() => expect(sent.some((s) => s.path.endsWith("/profile/titles"))).toBe(true));
    await act(async () => {});
    expect(screen.queryByRole("region", { name: "Seniority and industry" })).toBeNull();
    expect(document.body).not.toHaveTextContent(/job|ESCO/);
  });

  it("says a title's seniority and industry are not given, and saves them beside it", async () => {
    const { user, sent } = renderDetails([
      get(list(role, target)),
      originRoute(origin([])),
      {
        method: "PUT",
        path: /\/profile\/titles$/,
        status: 201,
        answer: { ...role, support_note: null },
      },
    ]);

    const section = await screen.findByRole("region", { name: "Seniority and industry" });
    expect(within(section).getAllByText("Seniority and industry: not given.")).toHaveLength(2);
    expect(section).toHaveTextContent("Target role: Doula");
    expect(section).not.toHaveTextContent(/your job|my job/i);
    await user.click(
      within(section).getByRole("button", { name: "Add seniority or industry for bookkeeper" }),
    );
    await user.type(within(section).getByLabelText("Seniority (optional)"), "Senior");
    await user.click(within(section).getByRole("button", { name: "Save" }));

    await waitFor(() => expect(sent.some((s) => s.method === "PUT")).toBe(true));
    expect(sent.find((s) => s.method === "PUT")?.body).toEqual({
      expected_version: 0,
      title_use: "role",
      title: "bookkeeper",
      seniority: "Senior",
      industry: null,
      not_part_of_job: [],
    });
    // The form gives way to what was saved; focus goes to the title's heading, never lost.
    await waitFor(() =>
      expect(within(section).getByRole("heading", { name: "Your role: Bookkeeper" })).toHaveFocus(),
    );
  });

  it("lets the person mark a skill ESCO lists for their role not part of their job", async () => {
    const { user, sent } = renderDetails([
      get(list({ ...role, seniority: "Senior", version: 1 })),
      originRoute(origin([usual("k1", "keep records"), usual("k2", "check accounts")])),
      {
        method: "PUT",
        path: /\/profile\/titles$/,
        status: 201,
        answer: { ...role, version: 2, not_part_of_job: ["k1"], support_note: null },
      },
    ]);

    const section = await screen.findByRole("region", { name: "Seniority and industry" });
    await user.click(
      await within(section).findByText("The 2 skills ESCO lists for this kind of work"),
    );
    expect(within(section).getByText(/ESCO, the EU's list of jobs and skills/)).toBeVisible();
    const mark = within(section).getByRole("button", { name: "Not part of my job: keep records" });
    expect(mark).toHaveAttribute("aria-pressed", "false");
    await user.click(mark);

    await waitFor(() => expect(sent.some((s) => s.method === "PUT")).toBe(true));
    // The whole of the title's details, the seniority kept as it was.
    expect(sent.find((s) => s.method === "PUT")?.body).toEqual({
      expected_version: 1,
      title_use: "role",
      title: "bookkeeper",
      seniority: "Senior",
      industry: null,
      not_part_of_job: ["k1"],
    });
  });

  it("shows a marked skill as the person's own display choice", async () => {
    renderDetails([
      get(list({ ...role, not_part_of_job: ["k1"], version: 1 })),
      originRoute(origin([usual("k1", "keep records", true)])),
    ]);

    const section = await screen.findByRole("region", { name: "Seniority and industry" });
    await userEvent
      .setup()
      .click(await within(section).findByText("The skill ESCO lists for this kind of work"));
    expect(
      within(section).getByRole("button", { name: "Not part of my job: keep records" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      within(section).getByText(
        "You said this isn't part of your job. Careerwright doesn't use it to check anything.",
      ),
    ).toBeVisible();
  });

  it("[PROF-09] shows the calm support panel beside the saved details when the words trigger the screen", async () => {
    const entryPanel: SupportNoteOut = {
      policy_version: "support-policy-9",
      review_status: "not yet reviewed as built",
      message:
        "If anything you typed is about how you are feeling, support is available any time, " +
        "from people trained to help. Your answers were saved as usual.",
      resources: [],
    };
    const { user } = renderDetails([
      get(list(target)),
      {
        method: "PUT",
        path: /\/profile\/titles$/,
        status: 201,
        answer: { ...target, version: 1, support_note: entryPanel },
      },
    ]);

    const section = await screen.findByRole("region", { name: "Seniority and industry" });
    await user.click(
      within(section).getByRole("button", { name: "Add seniority or industry for Doula" }),
    );
    await user.type(
      within(section).getByLabelText("Industry (optional)"),
      "I volunteer on a suicide prevention helpline.",
    );
    await user.click(within(section).getByRole("button", { name: "Save" }));

    const shown = await screen.findByRole("region", { name: "Support is available" });
    expect(shown).toHaveTextContent("Your answers were saved as usual.");
    await user.click(within(shown).getByRole("button", { name: /Dismiss/ }));
    expect(screen.queryByRole("region", { name: "Support is available" })).toBeNull();
  });
});
