// The seven states every component family must show distinctly (UI-04): loading, empty,
// unknown, conditional, stale, error and disabled. Each story composes the real components.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { Alert } from "@/components/Alert";
import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { FieldError, FieldStateSelect, ValueInput } from "@/components/fields";
import { LoadingState } from "@/components/LoadingState";
import { StatusBadge } from "@/components/Status";
import { describeField } from "@/lib/profile";
import { unknownDocument } from "./data";

const meta: Meta = { title: "States", parameters: { surface: "reading" } };
export default meta;
type Story = StoryObj;

export const Loading: Story = {
  render: () => (
    <div className="card max-w-[560px]">
      <LoadingState stage="Loading what we know" />
    </div>
  ),
};

export const Empty: Story = {
  render: () => (
    <div className="max-w-[720px]">
      <EmptyState
        state="notStarted"
        title="No routes yet"
        next={<Button>Review what we know</Button>}
      >
        <p>
          Routes are compared once your options are reviewed. Nessa's route search isn't part of
          this build yet, so no route has been computed for this workspace.
        </p>
      </EmptyState>
    </div>
  ),
};

export const Unknown: Story = {
  render: () => (
    <div className="card grid max-w-[560px] gap-12">
      <p className="section-title">Budget</p>
      <StatusBadge
        state="unknown"
        detail={`total ${describeField(unknownDocument.direct_spend_cap).toLowerCase()}, not £0`}
      />
      <p className="small">
        Monthly limit: {describeField(unknownDocument.monthly_payment_cap)}. Routes are shown
        without a spending check until you answer.
      </p>
    </div>
  ),
};

export const Conditional: Story = {
  parameters: { surface: "space" },
  render: () => (
    <div className="card-on-space grid max-w-[560px] gap-12">
      <p className="section-title">Route B</p>
      <StatusBadge state="conditional" detail="ready only once its assessed report is passed" />
    </div>
  ),
};

export const Stale: Story = {
  render: () => (
    <div className="grid max-w-[640px] gap-16">
      <Alert tone="stale" title="Version 3 was saved while you were editing">
        <p>
          Your edits are kept below, now based on version 3. Version 3 changed: Work areas. Check
          those answers, then save again.
        </p>
      </Alert>
      <StatusBadge state="stale" detail="last checked 2 days ago; may have closed" />
    </div>
  ),
};

export const ErrorState: Story = {
  name: "Error",
  render: () => (
    <div className="grid max-w-[640px] gap-16">
      <Alert tone="error" title="Nessa's database isn't reachable">
        <p>Nothing was lost. Try again in a moment.</p>
        <p className="muted">Reference 3f2a9c1e0b7d4a5e8c6f1a2b3c4d5e6f</p>
      </Alert>
      <div className="card">
        <ValueInput
          label="Total spending limit"
          kind="money"
          draft={{ state: "provided", text: "-20", items: [] }}
          error="Enter an amount of £0 or more."
          errorId="story-error"
          onChange={() => {}}
        />
        <FieldError id="story-error">Enter an amount of £0 or more.</FieldError>
      </div>
      <StatusBadge state="failed" detail="the reply didn't pass validation" />
      <StatusBadge state="provider_unavailable" detail="your work is kept" />
    </div>
  ),
};

export const Disabled: Story = {
  render: () => (
    <div className="card grid max-w-[560px] gap-16">
      <div className="flex flex-wrap items-center gap-8">
        <Button variant="primary" disabledReason="No changes to save.">
          Save changes
        </Button>
      </div>
      <FieldStateSelect
        label="Weekly study hours"
        draft={{ state: "skipped", text: "", items: [] }}
        disabledReason="Saving: you can change this again in a moment."
        onChange={() => {}}
      />
    </div>
  ),
};
