// Synthetic Skills states for the working chapter, including an expected qualification,
// a protected requirement, a target outside the reviewed pack and a person with no role.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { SkillsContent } from "@/components/SkillsChapter";
import type { SkillsOut } from "@/generated/api";
import { skillsData, target } from "@/test/skillsData";

const meta: Meta = { title: "Skills", parameters: { surface: "reading" } };
export default meta;
type Story = StoryObj;

function Scene({ data }: { data: SkillsOut }) {
  const [queries] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: false } } }),
  );
  return (
    <QueryClientProvider client={queries}>
      <div className="chapter on-reading chapter-panel">
        <SkillsContent data={data} workspaceId="story-skills" />
      </div>
    </QueryClientProvider>
  );
}

export const ExpectedGrades: Story = { render: () => <Scene data={skillsData} /> };

const gate = {
  gate_key: "gate-registration",
  kind: "legal_practice" as const,
  protected: true as const,
  modelled: true,
  label: "Registration",
  issuing_body: "NMC",
  jurisdiction: "England",
  verification: "NMC register",
  acceptable_proof: ["register entry"],
};
const firstRequirement = target.requirements[0];
const firstPrompt = skillsData.questions.prompts[0];
if (!firstRequirement || !firstPrompt)
  throw new Error("The Skills story needs a requirement and a question.");
const withGate: SkillsOut = {
  ...skillsData,
  targets: [
    {
      ...target,
      not_assessed_reason: "no_rubric",
      requirements: [
        {
          ...firstRequirement,
          row_id: "registration",
          subject: "registration",
          label: "NMC registration",
          gate,
          entry_facts: [
            {
              qualification: "NMC registration",
              status: "achieved",
              standing: "achieved_unverified",
            },
          ],
        },
      ],
    },
  ],
  questions: {
    ...skillsData.questions,
    prompts: [
      {
        ...firstPrompt,
        prompt_id: "registration",
        kind: "requirement",
        subject: "registration",
        label: "NMC registration",
        rows: [],
        gate,
      },
    ],
    initial: ["registration"],
  },
};
export const ProtectedGate: Story = { render: () => <Scene data={withGate} /> };

const outsidePack: SkillsOut = {
  ...skillsData,
  targets: [
    {
      ...target,
      pack_target: null,
      seed: "none_of_these",
      esco_listed: [],
      requirements: [],
      not_assessed_reason: "no_rubric",
    },
  ],
  questions: { ...skillsData.questions, state: "insufficient_coverage", prompts: [], initial: [] },
};
export const NoReviewedTarget: Story = { render: () => <Scene data={outsidePack} /> };

const noRole: SkillsOut = { ...skillsData, usual_in_role: null };
export const NoCurrentRole: Story = { render: () => <Scene data={noRole} /> };

const withRole: SkillsOut = {
  ...skillsData,
  usual_in_role: {
    role_title: "Warehouse assistant",
    occupation_id: "occupation:warehouse",
    occupation_label: "Warehouse assistant",
    skills: [
      {
        skill_id: "role-skill-1",
        subject: "esco:role-skill-1",
        label: "organise stock",
        skill_type: null,
        state: "usual_in_role",
        answer: null,
        evidence_id: null,
        not_part_of_job: false,
      },
    ],
  },
};
export const CurrentRoleSkills: Story = { render: () => <Scene data={withRole} /> };

export const NoTarget: Story = { render: () => <Scene data={{ ...skillsData, targets: [] }} /> };
