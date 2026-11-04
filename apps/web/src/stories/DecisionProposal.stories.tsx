import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { DecisionAtmosphere } from "@/components/DecisionAtmosphere";
import { DecisionProposal } from "@/components/DecisionProposal";
import { RouteExplorer } from "@/components/RouteExplorer";
import { useWorldSettings } from "@/lib/world/settings";
import { p01Checkpoint, p01Plan, p01Profile, p01Routes, p01Skills } from "@/test/p01DesignData";
import { expansionTargets } from "@/test/routeExpansionData";

const meta: Meta<typeof DecisionProposal> = {
  title: "Design proposal/P01 decision",
  component: DecisionProposal,
  parameters: { layout: "fullscreen", surface: "reading", designProposal: true },
  args: {
    routes: p01Routes,
    skills: p01Skills,
    plan: p01Plan,
    checkpoint: p01Checkpoint,
    profile: p01Profile,
  },
};
export default meta;
type Story = StoryObj<typeof meta>;

export const Review: Story = {};

function ThreeTargetExample() {
  const settings = useWorldSettings();
  return (
    <div
      className="decision-proposal route-expansion-example"
      data-still={settings.reduced || settings.calm || settings.paused}
    >
      <div className="decision-demo-banner">
        <strong>Fictional structure example</strong>
        <span>
          Interaction example only. These are not P01 routes, vacancies or computed recommendations.
        </span>
      </div>
      <header className="decision-shell-header">
        <a
          className="decision-brand"
          href="?id=design-proposal-p01-decision--review&viewMode=story"
        >
          <span className="decision-brand-mark" aria-hidden="true" /> Careerwright
        </a>
        <DecisionAtmosphere settings={settings} />
        <span>Three possible destinations</span>
      </header>
      <main className="route-expansion-layout">
        <section className="decision-reading">
          <h1>Explore a destination</h1>
          <p>
            Open a destination to see its routes, then open a route to reveal the courses and
            possible job steps along it.
          </p>
          <p>Other destinations stay within reach. You can return to the overview at any time.</p>
          <div className="decision-caution">
            <strong>Job steps need offers.</strong>
            <p>A role on a trail is not an available vacancy or an accepted offer.</p>
          </div>
          <details className="decision-disclosure">
            <summary>About this example</summary>
            <p>
              All three targets and their route structures are fictional. Dates illustrate the
              sequence; time to readiness, costs and hours have not been assessed.
            </p>
            <p>
              The data targets share a foundation course and some job steps. Opening a route shows
              each of its shared steps once.
            </p>
            <a href="?id=design-proposal-p01-decision--review&viewMode=story">
              Return to the actual P01 proposal
            </a>
          </details>
        </section>
        <section className="decision-map" aria-label="Expandable routes">
          <RouteExplorer targets={expansionTargets} startLabel="Your starting point" />
        </section>
      </main>
    </div>
  );
}

export const ThreeTargets: Story = { render: () => <ThreeTargetExample /> };
