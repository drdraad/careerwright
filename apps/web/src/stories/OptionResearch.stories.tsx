import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { OptionResearchView } from "@/components/OptionResearchView";
import { optionEstimate, optionResearch, optionRun } from "@/test/optionResearchData";

const meta = {
  title: "Options/Find options for this role",
  component: OptionResearchView,
  parameters: { surface: "reading" },
  decorators: [
    (Story) => (
      <div className="chapter on-reading chapter-panel">
        <Story />
      </div>
    ),
  ],
  args: {
    target: "Data quality analyst",
    cities: ["Leeds", "York"],
    city: "Leeds",
    onCity: () => {},
    keyReady: true,
    canWrite: true,
    estimate: optionEstimate,
    estimateLoading: false,
    estimateError: null,
    research: null,
    researchLoading: false,
    researchError: null,
    starting: false,
    reading: false,
    cancelling: false,
    startError: null,
    readError: null,
    cancelError: null,
    onStart: () => {},
    onRead: () => {},
    onCancel: () => {},
  },
} satisfies Meta<typeof OptionResearchView>;

export default meta;
type Story = StoryObj<typeof meta>;

export const CostBeforeStart: Story = {};
export const BudgetRefused: Story = {
  args: { estimate: { ...optionEstimate, refused_scope: "run" } },
};
export const Searching: Story = {
  args: {
    research: {
      ...optionResearch,
      status: "searching",
      coverage: "none_read",
      search: optionRun("search-id", "running"),
      reading: null,
      pages_attempted: 0,
      pages_read: 0,
      candidates: 0,
      records: [],
    },
  },
};
export const ReadingWithBlockedPage: Story = {
  args: {
    research: {
      ...optionResearch,
      status: "reading",
      coverage: "partial",
      reading: optionRun("reading-id", "running", "acquisition"),
      pages_attempted: 1,
      pages_read: 0,
      pages_blocked: 1,
      records: [],
    },
  },
};
export const CompletedWithProposedRecord: Story = { args: { research: optionResearch } };
export const PartialResult: Story = {
  args: {
    research: {
      ...optionResearch,
      status: "reading_stopped",
      coverage: "partial",
      reading: {
        ...optionRun("reading-id", "failed", "acquisition"),
        failure_class: "retrieval_failed",
      },
      pages_blocked: 1,
      pages_failed: 1,
    },
  },
};
export const NoUsablePages: Story = {
  args: {
    research: {
      ...optionResearch,
      status: "no_pages",
      coverage: "none_read",
      empty_reason: "all_excluded",
      reading: null,
      records: [],
    },
  },
};
