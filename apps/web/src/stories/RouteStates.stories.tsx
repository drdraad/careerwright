import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { useState } from "react";
import { RouteExplorer } from "@/components/RouteExplorer";
import { planningStateTargets } from "@/test/routeStateData";

const meta: Meta<typeof RouteExplorer> = {
  title: "Routes/Planning information states",
  component: RouteExplorer,
  parameters: { layout: "fullscreen", surface: "reading", designProposal: true },
};
export default meta;
type Story = StoryObj<typeof meta>;

function ReactiveStates() {
  const [missingHours, setMissingHours] = useState(false);
  const [stale, setStale] = useState(false);
  const targets = planningStateTargets.map((target) =>
    target.id === "complete"
      ? {
          ...target,
          status: stale ? ("stale" as const) : ("available" as const),
          routes: target.routes.map((route) => ({
            ...route,
            steps: route.steps.map((step) => ({ ...step, weekly_hours: missingHours ? null : 6 })),
          })),
        }
      : target,
  );
  return (
    <div className="decision-proposal route-expansion-example">
      <div className="decision-demo-banner">
        <strong>Fictional planning states</strong>
        <span>
          Interaction examples only. No provider, place, source or route recommendation is verified.
        </span>
      </div>
      <main className="route-expansion-layout">
        <section className="decision-reading">
          <h1>Watch the route answer its facts</h1>
          <p>
            One search found no supported route in its monthly model. Another route needs planning
            facts. The third has its planning information, while its source and place still need
            checking.
          </p>
          <p>
            Open the reporting role and inspect its course. Change its hours to see that step
            respond without losing the inspection.
          </p>
          <button
            type="button"
            aria-pressed={missingHours}
            onClick={() => setMissingHours(!missingHours)}
          >
            {missingHours ? "Restore recorded weekly hours" : "Remove recorded weekly hours"}
          </button>
          <button type="button" aria-pressed={stale} onClick={() => setStale(!stale)}>
            {stale ? "Show current saved result" : "Mark saved result out of date"}
          </button>
        </section>
        <section className="decision-map" aria-label="Route planning states">
          <RouteExplorer targets={targets} startLabel="Your starting point" />
        </section>
      </main>
    </div>
  );
}

export const Reactive: Story = { render: () => <ReactiveStates /> };
export const Pending: Story = {
  args: {
    targets: planningStateTargets.map((target) => ({ ...target, status: "pending" })),
    startLabel: "Your starting point",
  },
};
