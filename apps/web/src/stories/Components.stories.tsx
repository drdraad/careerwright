// The shell's component vocabulary: status words for every API state, buttons, notices and
// form controls, on both surfaces.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Alert } from "@/components/Alert";
import { Button } from "@/components/Button";
import { FieldStateSelect, ListInput, ValueInput } from "@/components/fields";
import { StatusBadge, SyntheticLabel } from "@/components/Status";
import { WorkState } from "@/generated/api";
import { listLimit } from "@/lib/bounds";
import { DISPLAY_STATE } from "@/lib/vocabulary";

const meta: Meta = { title: "Components" };
export default meta;
type Story = StoryObj;

function Vocabulary() {
  return (
    <ul className="grid gap-12">
      {Object.values(WorkState).map((state) => (
        <li key={state}>
          <StatusBadge state={state} />
        </li>
      ))}
      {(Object.keys(DISPLAY_STATE) as Array<keyof typeof DISPLAY_STATE>).map((state) => (
        <li key={state}>
          <StatusBadge state={state} />
        </li>
      ))}
      <li>
        <SyntheticLabel />
      </li>
    </ul>
  );
}

export const StatusVocabularyOnSpace: Story = { render: () => <Vocabulary /> };

export const StatusVocabularyOnReading: Story = {
  parameters: { surface: "reading" },
  render: () => <Vocabulary />,
};

export const Buttons: Story = {
  parameters: { surface: "reading" },
  render: () => (
    <div className="flex flex-wrap items-center gap-12">
      <Button variant="primary">Save changes</Button>
      <Button>Discard changes</Button>
      <Button variant="quiet">Source</Button>
      <Button variant="secondary" glyph="signOut">
        Sign out
      </Button>
      <Button variant="primary" disabledReason="No changes to save.">
        Save changes
      </Button>
    </div>
  ),
};

export const Notices: Story = {
  render: () => (
    <div className="grid max-w-[720px] gap-16">
      <Alert
        tone="neutral"
        glyph="synthetic"
        title="Fixture preview: not your routes"
        announce={false}
      >
        These routes come from the synthetic TRACE-01 worked trace in the supplied fixture pack.
      </Alert>
      <Alert tone="stale" title="This changed since you loaded it">
        Review the latest version, then save again.
      </Alert>
      <Alert tone="unknown" title="Total spending limit: Unknown">
        The result is less precise, never filled in with a guess.
      </Alert>
      <Alert tone="error" title="Nessa's service isn't reachable">
        Nothing you saved is lost. If Nessa is restarting, try again in a moment.
      </Alert>
    </div>
  ),
};

export const FormControls: Story = {
  parameters: { surface: "reading" },
  render: () => (
    <div className="card grid max-w-[640px] gap-16">
      <FieldStateSelect
        label="Current role"
        draft={{ state: "unknown", text: "", items: [] }}
        onChange={() => {}}
      />
      <ValueInput
        label="Weekly study hours"
        kind="hours"
        draft={{ state: "provided", text: "7.5", items: [] }}
        onChange={() => {}}
      />
      <ListInput
        label="Work areas"
        itemLabel="Work area"
        limit={listLimit("cities")}
        draft={{ state: "provided", text: "", items: ["Manchester", "Leeds", "York"] }}
        onChange={() => {}}
      />
    </div>
  ),
};
