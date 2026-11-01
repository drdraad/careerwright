import type { StorybookConfig } from "@storybook/nextjs-vite";

// Component states for design review (plan section 4: "implement their components in
// Storybook"). Local only: telemetry off, served on 127.0.0.1 (`pnpm storybook`).
const config: StorybookConfig = {
  framework: { name: "@storybook/nextjs-vite", options: {} },
  stories: ["../src/stories/**/*.stories.tsx"],
  addons: ["@storybook/addon-a11y"],
  core: { disableTelemetry: true, disableWhatsNewNotifications: true },
  viteFinal: (vite) => ({
    ...vite,
    build: {
      ...vite.build,
      // Storybook's own manager bundle (axe included) is large by design; it is never shipped.
      chunkSizeWarningLimit: 2048,
      rolldownOptions: {
        ...vite.build?.rolldownOptions,
        onwarn(warning, warn) {
          // "use client" marks Next.js client components; it means nothing in a story bundle.
          if (warning.code === "MODULE_LEVEL_DIRECTIVE") return;
          warn(warning);
        },
      },
    },
  }),
};

export default config;
