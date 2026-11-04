import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { userEvent, within } from "storybook/test";
import { OptionsScreen } from "@/components/OptionsChapter";
import { checkpointFixture, optionsFixture } from "@/test/optionsFixture";

const meta = {
  title: "Options",
  component: OptionsScreen,
  parameters: { surface: "reading" },
  decorators: [
    (Story) => (
      <div className="chapter on-reading chapter-panel">
        <Story />
      </div>
    ),
  ],
  args: {
    workspaceId: "w-story",
    options: optionsFixture,
    checkpoint: checkpointFixture,
    inputs: {},
    busy: false,
    failure: null,
    onWrite: async () => true,
    onAdd: async () => null,
  },
} satisfies Meta<typeof OptionsScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

export const DegreeAndLoan: Story = {};

export const TLevelAndMissingCost: Story = {
  play: async ({ canvasElement }) => {
    await userEvent.click(within(canvasElement).getByRole("button", { name: /Digital T Level/ }));
  },
};

export const BeforeRouteSearch: Story = {
  play: async ({ canvasElement }) => {
    await userEvent.click(
      within(canvasElement).getByRole("button", { name: /Before a route search/ }),
    );
  },
};

export const AddYourOwn: Story = {
  play: async ({ canvasElement }) => {
    await userEvent.click(
      within(canvasElement).getByRole("button", { name: "Add your own option" }),
    );
  },
};

export const NoReviewedOption: Story = {
  args: {
    options: {
      ...optionsFixture,
      targets: optionsFixture.targets.map((target) => ({ ...target, catalogue: null })),
    },
    checkpoint: {
      ...checkpointFixture,
      targets: checkpointFixture.targets.map((target) => ({
        ...target,
        reviewed_options: 0,
        options: [],
      })),
    },
  },
};

export const OverTheRouteSearchBounds: Story = {
  args: {
    checkpoint: {
      ...checkpointFixture,
      targets: checkpointFixture.targets.map((target) => ({
        ...target,
        scope: { ...target.scope, concepts: 25, most_starts: 3, code: "retain_variants" as const },
      })),
    },
  },
};

export const NoTargetYet: Story = {
  args: {
    options: { ...optionsFixture, targets: [] },
    checkpoint: { ...checkpointFixture, targets: [] },
  },
};
