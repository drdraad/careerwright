import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { ProfileDocument, ProfileOut } from "@/generated/api";
import { useProfile } from "@/lib/queries";
import { fakeApi } from "@/test/fakeApi";
import { ProfileHistory } from "./ProfileHistory";

const WS = "w-history";
const unasked = { state: "unasked" as const, value: null, source_ref_id: null };
const base: ProfileDocument = {
  schema_version: "5",
  work_status: unasked,
  qualifications: unasked,
  disliked_tasks: unasked,
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
};
function version(version: number, role: string, source: string): ProfileOut {
  return {
    workspace_id: WS,
    version,
    created_by: null,
    created_at: `2026-11-0${version}T10:20:00Z`,
    document: {
      ...base,
      current_role: { state: "provided", value: role, source_ref_id: source },
    },
  };
}

function History() {
  const profile = useProfile(WS);
  if (profile.data === undefined) return null;
  return (
    <>
      <p>Current: {profile.data.document.current_role.value}</p>
      <ProfileHistory workspaceId={WS} profile={profile.data} />
    </>
  );
}

describe("earlier saved answers", () => {
  it("loads history when opened, previews a prior version, then restores it only after confirmation", async () => {
    const first = version(1, "Teacher", "source-1");
    const versions = [first, version(2, "Nurse", "source-2")];
    let current = version(3, "Builder", "source-3");
    const sent = fakeApi([
      { method: "GET", path: /\/profile$/, answer: () => current },
      {
        method: "GET",
        path: /\/profile\/versions$/,
        answer: () => ({ items: [current, ...versions.toReversed()], next_cursor: null }),
      },
      {
        method: "GET",
        path: /\/profile\/versions\/1$/,
        answer: () => versions[0],
      },
      {
        method: "POST",
        path: /\/profile\/revert$/,
        status: 201,
        answer: () => {
          current = { ...first, version: 4 };
          return current;
        },
      },
    ]);
    const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queries}>
        <History />
      </QueryClientProvider>,
    );
    const user = userEvent.setup();
    await screen.findByText("Current: Builder");
    expect(sent.some((request) => request.path.endsWith("/profile/versions"))).toBe(false);

    await user.click(screen.getByText("Earlier answers"));
    await screen.findByRole("button", { name: "View version 1" });
    expect(screen.getByText("Version 2")).toBeVisible();
    expect(document.querySelector('time[datetime="2026-11-01T10:20:00Z"]')).toBeVisible();
    await user.click(screen.getByRole("button", { name: "View version 1" }));
    const preview = await screen.findByRole("region", { name: "Answers in version 1" });
    expect(within(preview).getByText("Teacher")).toBeVisible();
    expect(within(preview).getByText("Current role")).toBeVisible();
    expect(sent.some((request) => request.path.endsWith("/profile/revert"))).toBe(false);

    await user.click(within(preview).getByRole("button", { name: "Restore version 1" }));
    expect(within(preview).getByText("Restore version 1 as a new saved version?")).toBeVisible();
    expect(sent.some((request) => request.path.endsWith("/profile/revert"))).toBe(false);
    await user.click(within(preview).getByRole("button", { name: "Cancel" }));
    expect(sent.some((request) => request.path.endsWith("/profile/revert"))).toBe(false);
    await user.click(within(preview).getByRole("button", { name: "Restore version 1" }));
    await user.click(within(preview).getByRole("button", { name: "Confirm restore" }));
    await waitFor(() => expect(screen.getByText("Current: Teacher")).toBeVisible());
    expect(sent.find((request) => request.path.endsWith("/profile/revert"))?.body).toEqual({
      expected_version: 3,
      to_version: 1,
    });
    expect(current.version).toBe(4);
    expect(current.document.current_role.source_ref_id).toBe("source-1");
    expect(screen.getByRole("status")).toHaveTextContent(
      "Version 1 was restored as a new saved version.",
    );
  });
});
