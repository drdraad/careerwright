// What we know's targets (Task W2F; session W2, finding 2): a Remove beside each target,
// through the profile's own save, with Undo where it was done; removing the last leaves the
// target roles Unknown (Task W2F's ruling). The targets are listed once, never also among the
// answers.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { ProfileDocument, ProfileInput, ProfileOut } from "@/generated/api";
import { useProfile } from "@/lib/queries";
import { fakeApi, type Sent } from "@/test/fakeApi";
import { WhatWeKnow } from "./WhatWeKnow";

const WS = "w-known";
const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const given = <T,>(value: T) => ({ state: "provided" as const, value, source_ref_id: "s1" });
const document: ProfileDocument = {
  schema_version: "4",
  work_status: unasked,
  qualifications: unasked,
  preferred_name: unasked,
  current_role: given("Warehouse shift supervisor"),
  cities: given(["Leeds"]),
  target_titles: given(["Veterinary nurse", "Animal care attendant", "Zoo keeper"]),
  weekly_study_hours: unasked,
  direct_spend_cap: unasked,
  monthly_payment_cap: unasked,
  enjoyed_tasks: unasked,
  confident_tasks: unasked,
  evidenced_tasks: unasked,
  work_style: unasked,
  minimum_salary: unasked,
};
const at = (version: number, targets: ProfileDocument["target_titles"]): ProfileOut => ({
  workspace_id: WS,
  version,
  created_by: null,
  created_at: "2027-01-01T00:00:00Z",
  document: { ...document, target_titles: targets },
});

/** The API's profile: a save stores the targets it was sent; Undo restores a version's. */
function profileApi(first: ProfileOut, status = 201): Sent[] {
  const versions = [first];
  const latest = () => versions.at(-1) ?? first;
  return fakeApi([
    { method: "GET", path: /\/profile$/, answer: () => latest() },
    {
      method: "PUT",
      path: /\/profile$/,
      status,
      answer: (sent) => {
        if (status !== 201) {
          return {
            error: {
              code: "STALE_INPUT_VERSION",
              message: "",
              retryable: false,
              stage: "profile",
              correlation_id: "c1",
              details: {},
            },
          };
        }
        const { target_titles } = (sent.body as { profile: ProfileInput }).profile;
        const stored = {
          ...target_titles,
          value: target_titles.value ?? null,
          source_ref_id: "s2",
        };
        versions.push(at(latest().version + 1, stored));
        return { ...latest(), support_note: null };
      },
    },
    {
      method: "POST",
      path: /\/profile\/revert$/,
      status: 201,
      answer: (sent) => {
        const { to_version } = sent.body as { to_version: number };
        const restored = versions.find((v) => v.version === to_version) ?? first;
        versions.push(at(latest().version + 1, restored.document.target_titles));
        return latest();
      },
    },
  ]);
}

/** What we know reading the profile from the (scripted) API, as the You chapter does. */
function Known() {
  const current = useProfile(WS);
  return current.data === undefined ? null : (
    <WhatWeKnow profile={current.data} editing={false} onEdit={() => {}} form={null} />
  );
}

function renderKnown() {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queries}>
      <Known />
    </QueryClientProvider>,
  );
  return userEvent.setup();
}

const saves = (sent: Sent[]) => sent.filter((s) => s.method === "PUT");

describe("[STATE-10][PROF-04] What we know's targets: Remove beside each, with Undo", () => {
  it("lists the targets once, near the top, each with its Remove", async () => {
    profileApi(at(4, document.target_titles));
    renderKnown();

    const targets = await screen.findByRole("region", { name: "Your targets" });
    for (const title of ["Veterinary nurse", "Animal care attendant", "Zoo keeper"]) {
      expect(within(targets).getByText(title)).toBeVisible();
      expect(
        within(targets).getByRole("button", { name: `Remove ${title} from your targets` }),
      ).toBeVisible();
    }
    // Before the other answers, and never repeated among them.
    const answers = screen.getByRole("region", { name: "Your answers" });
    expect(
      targets.compareDocumentPosition(answers) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(answers).not.toHaveTextContent("Target roles");
    expect(answers).not.toHaveTextContent("Zoo keeper");
  });

  it("removes one through the profile's save, then Undo puts it back, focus with each", async () => {
    const sent = profileApi(at(4, document.target_titles));
    const user = renderKnown();

    const targets = await screen.findByRole("region", { name: "Your targets" });
    await user.click(
      within(targets).getByRole("button", { name: "Remove Zoo keeper from your targets" }),
    );

    const removed = await screen.findByRole("heading", {
      name: "Removed “Zoo keeper” from your targets",
    });
    await waitFor(() => expect(removed).toHaveFocus());
    // The profile's own save: the other targets and every other answer as stored.
    const [save] = saves(sent);
    expect(save?.body).toMatchObject({
      expected_version: 4,
      profile: {
        target_titles: { state: "provided", value: ["Veterinary nurse", "Animal care attendant"] },
        current_role: { state: "provided", value: "Warehouse shift supervisor" },
        cities: { state: "provided", value: ["Leeds"] },
        enjoyed_tasks: { state: "unasked" },
      },
    });
    expect(within(targets).queryByText("Zoo keeper")).toBeNull();

    const undo = within(targets).getByRole("button", { name: "Undo removing “Zoo keeper”" });
    expect(undo).toHaveClass("btn-undo"); // orchid, as every undo (session 2, C3)
    await user.click(undo);

    const back = await screen.findByRole("heading", {
      name: "Undone: “Zoo keeper” is one of your targets again",
    });
    await waitFor(() => expect(back).toHaveFocus());
    expect(sent.find((s) => s.path.endsWith("/profile/revert"))?.body).toEqual({
      expected_version: 5,
      to_version: 4,
    });
    expect(within(targets).getByText("Zoo keeper")).toBeVisible();
    expect(within(targets).queryByRole("button", { name: /^Undo/ })).toBeNull();
  });

  it("leaves the target roles Unknown when the last one is removed", async () => {
    const sent = profileApi(at(4, given(["Zoo keeper"])));
    const user = renderKnown();

    await user.click(
      await screen.findByRole("button", { name: "Remove Zoo keeper from your targets" }),
    );

    await screen.findByRole("heading", { name: "Removed “Zoo keeper” from your targets" });
    expect(saves(sent)[0]?.body).toMatchObject({
      profile: { target_titles: { state: "unknown" } },
    });
    const targets = screen.getByRole("region", { name: "Your targets" });
    expect(within(targets).getByText("Unknown")).toBeVisible();
    expect(screen.getByRole("button", { name: "Undo removing “Zoo keeper”" })).toBeVisible();
  });

  it("says when a removal wasn't saved, and keeps the target", async () => {
    profileApi(at(4, document.target_titles), 409);
    const user = renderKnown();

    await user.click(
      await screen.findByRole("button", { name: "Remove Zoo keeper from your targets" }),
    );

    expect(await screen.findByText("This changed since you loaded it")).toBeVisible();
    const targets = screen.getByRole("region", { name: "Your targets" });
    expect(within(targets).getByText("Zoo keeper")).toBeVisible();
    expect(screen.queryByRole("heading", { name: /^Removed/ })).toBeNull();
  });

  it("says the target roles aren't asked yet in one place only", async () => {
    profileApi(at(1, unasked));
    renderKnown();

    const targets = await screen.findByRole("region", { name: "Your targets" });
    expect(within(targets).getByText("Not asked yet")).toBeVisible();
    expect(within(targets).queryByRole("button", { name: /^Remove/ })).toBeNull();
    expect(screen.getByRole("region", { name: "Not asked yet" })).not.toHaveTextContent(
      "Target roles",
    );
  });
});
