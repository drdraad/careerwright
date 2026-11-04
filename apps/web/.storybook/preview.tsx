import type { Preview } from "@storybook/nextjs-vite";
import { EvidenceDrawer, EvidenceProvider } from "../src/components/EvidenceDrawer";
import "../src/design/tokens/tokens.css";
import "../src/app/globals.css";

// Every story renders on the surface it belongs to: `parameters.surface` is "space" (ink, the
// default for exploration) or "reading" (light canvas). The drawer is mounted beside it so
// stories that open evidence show the real drawer.
const preview: Preview = {
  parameters: {
    layout: "fullscreen",
    a11y: { test: "error" },
  },
  decorators: [
    (Story, context) => {
      if (context.parameters.designProposal) return <Story />;
      const surface = context.parameters.surface === "reading" ? "reading" : "space";
      return (
        <EvidenceProvider>
          <div
            className={`on-${surface} min-h-dvh p-32 ${surface === "reading" ? "bg-reading" : "bg-space"}`}
          >
            <Story />
          </div>
          <EvidenceDrawer />
        </EvidenceProvider>
      );
    },
  ],
};

export default preview;
