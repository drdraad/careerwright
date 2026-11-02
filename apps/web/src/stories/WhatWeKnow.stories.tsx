// What we know (Task W2F; session W2, findings 1 and 2), in the You chapter's reading panel:
// long values beside their labels (three long targets, an expected qualification and long task
// answers, which the visual checks measure so no label is printed over its value at any width),
// a target removed from the list with Undo, and the answer form open with its Save kept in
// view. The long values are invented for layout testing only; the rest is P01's, from the
// supplied synthetic pack.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { userEvent, within } from "storybook/test";
import { ProfileEditor } from "@/components/ProfileEditor";
import { WhatWeKnow } from "@/components/WhatWeKnow";
import type { ProfileDocument, ProfileInput, ProfileOut } from "@/generated/api";
import { useProfile } from "@/lib/queries";
import { fakeApi } from "@/test/fakeApi";
import { longDocument, profile } from "./data";

const given = <T,>(value: T) => ({ state: "provided" as const, value, source_ref_id: "s1" });

/** Long answers beside short labels: the three-target maximum at its longest, an expected
 *  qualification, and tasks in the person's own long words (invented for layout testing). */
const longAnswers: ProfileDocument = {
  ...longDocument,
  target_titles: given([
    "Senior data governance and information quality manager",
    "Clinical data standards and interoperability specialist",
    "Veterinary nurse in a large animal referral hospital",
  ]),
  current_role: given("Warehouse shift supervisor on nights and weekend cover"),
  work_status: given("in_education_or_training" as const),
  qualifications: given([
    { name: "A levels in Biology, Chemistry and English Literature", status: "expected" as const },
    { name: "GCSEs in nine subjects", status: "achieved" as const },
    { name: "Duke of Edinburgh silver award", status: "achieved" as const },
  ]),
  enjoyed_tasks: given([
    "looking after animals",
    "being outdoors in all weathers",
    "helping people who are worried about something",
  ]),
  confident_tasks: given(["explaining complicated rules to new starters on a busy shift"]),
};

/** The API at the network edge: a save stores the targets it was sent; Undo restores them. */
function Api({ first, children }: { first: ProfileOut; children: ReactNode }) {
  const [queries] = useState(() => {
    const versions = [first];
    const latest = () => versions.at(-1) ?? first;
    const at = (target_titles: ProfileDocument["target_titles"]): ProfileOut => ({
      ...first,
      version: latest().version + 1,
      document: { ...first.document, target_titles },
    });
    fakeApi([
      { method: "GET", path: /\/profile$/, answer: () => latest() },
      {
        method: "PUT",
        path: /\/profile$/,
        status: 201,
        answer: (sent) => {
          const { target_titles } = (sent.body as { profile: ProfileInput }).profile;
          versions.push(at({ ...target_titles, value: target_titles.value ?? null }));
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
          versions.push(at(restored.document.target_titles));
          return latest();
        },
      },
    ]);
    return new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } });
  });
  return <QueryClientProvider client={queries}>{children}</QueryClientProvider>;
}

/** What we know as the You chapter shows it, reading its profile from the API, with the answer
 *  form open when `editing`. */
function Known({ first, editing }: { first: ProfileOut; editing: boolean }) {
  const current = useProfile(first.workspace_id);
  const shown = current.data ?? first;
  return (
    <div className="chapter chapter-you on-reading">
      <section className="known" aria-labelledby="known-title">
        <h2 id="known-title" className="display text-25">
          What we know
        </h2>
        <WhatWeKnow
          profile={shown}
          editing={editing}
          onEdit={() => {}}
          form={
            editing && (
              <div id="edit-answers">
                <ProfileEditor workspaceId={shown.workspace_id} profile={shown} />
              </div>
            )
          }
        />
      </section>
    </div>
  );
}

const meta: Meta = { title: "What we know", parameters: { surface: "reading" } };
export default meta;
type Story = StoryObj;

const shown =
  (document: ProfileDocument, editing = false) =>
  () => {
    const first = profile(document, 4);
    return (
      <Api first={first}>
        <Known first={first} editing={editing} />
      </Api>
    );
  };

/** Long values beside their labels, at every width: never printed over them (finding 1). */
export const LongValues: Story = { render: shown(longAnswers) };

/** A target removed from the list: what it did, with Undo in orchid, in place (finding 2). */
export const TargetRemoved: Story = {
  render: shown(longAnswers),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.click(
      await canvas.findByRole("button", {
        name: "Remove Veterinary nurse in a large animal referral hospital from your targets",
      }),
    );
    await canvas.findByRole("button", { name: /^Undo removing/ });
  },
};

/** The answer form open: Save changes and Discard stay at the foot of the window as the form
 *  scrolls past (finding 9: Save was some 3,400 px down). */
export const AnswerFormOpen: Story = { render: shown(longAnswers, true) };
