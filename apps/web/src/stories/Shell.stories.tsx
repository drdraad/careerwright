// The shell pieces: chapter rail and menu, workspace strip (live, reconnecting, stopped;
// unknown budget; long names), the evidence drawer, and the fixture route preview.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { useEffect } from "react";
import { ChapterMenu, ChapterRail } from "@/components/ChapterNav";
import { useEvidence } from "@/components/EvidenceDrawer";
import { RoutePreview } from "@/components/RoutePreview";
import { SourceEvidence } from "@/components/SourceEvidence";
import { WorkspaceStrip } from "@/components/WorkspaceStrip";
import type { StreamStatus } from "@/lib/events";
import { describeField } from "@/lib/profile";
import {
  directSource,
  failedPreview,
  fixtureSource,
  fixtureWorkspace,
  longDocument,
  longWorkspace,
  p01Document,
  profile,
  routePreview,
  unknownDocument,
} from "./data";

const meta: Meta = { title: "Shell" };
export default meta;
type Story = StoryObj;

export const ChapterRailOnRoutes: Story = {
  parameters: { layout: "fullscreen" },
  render: () => (
    <div className="app">
      <ChapterRail
        workspaceId={fixtureWorkspace.workspace_id}
        current="routes"
        progress={{ you: "visited", roles: "visited" }}
      />
    </div>
  ),
};

export const ChapterMenuOnPhone: Story = {
  render: () => (
    <ChapterMenu
      workspaceId={fixtureWorkspace.workspace_id}
      current="you"
      progress={{ you: "visited" }}
    />
  ),
};

function Strip({
  events,
  document = p01Document,
  long = false,
  refreshFailed = false,
}: {
  events: StreamStatus;
  document?: typeof p01Document;
  long?: boolean;
  refreshFailed?: boolean;
}) {
  return (
    <div className="app">
      <WorkspaceStrip
        workspace={long ? longWorkspace : fixtureWorkspace}
        profile={profile(document, 3)}
        profileFailed={false}
        workspaces={[fixtureWorkspace]}
        workspacesFailed={false}
        events={events}
        onReconnect={() => {}}
        refreshFailed={refreshFailed}
        email="ada@careerwright.test"
        calm={false}
        onCalmChange={() => {}}
        onSignOut={() => {}}
      />
    </div>
  );
}

export const StripLive: Story = { render: () => <Strip events={{ state: "live" }} /> };
export const StripReconnecting: Story = {
  render: () => <Strip events={{ state: "reconnecting", attempt: 2, delayMs: 4000 }} />,
};
export const StripRefreshFailed: Story = {
  render: () => (
    <Strip events={{ state: "reconnecting", attempt: 3, delayMs: 8000 }} refreshFailed />
  ),
};
export const StripStoppedSignedOut: Story = {
  render: () => <Strip events={{ state: "stopped", reason: "signed_out" }} />,
};
export const StripUnknownBudget: Story = {
  render: () => <Strip events={{ state: "live" }} document={unknownDocument} />,
};
export const StripLongNamesThreeTargets: Story = {
  render: () => <Strip events={{ state: "live" }} document={longDocument} long />,
};

function OpenEvidence({
  source,
  failed = false,
}: {
  source: typeof fixtureSource | undefined;
  failed?: boolean;
}) {
  const evidence = useEvidence();
  // biome-ignore lint/correctness/useExhaustiveDependencies: open once when the story mounts
  useEffect(() => {
    evidence.open({
      title: "Where this came from",
      body: (
        <SourceEvidence
          fieldLabel="Total spending limit"
          value={describeField(p01Document.direct_spend_cap)}
          lessPrecise="Which routes are affordable: they are shown without a spending check."
          source={source}
          loading={false}
          failed={failed}
        />
      ),
    });
  }, []);
  return <p className="small">The drawer opens beside the work.</p>;
}

export const DrawerFixtureSource: Story = { render: () => <OpenEvidence source={fixtureSource} /> };
export const DrawerDirectEntry: Story = { render: () => <OpenEvidence source={directSource} /> };
export const DrawerUnknownSource: Story = { render: () => <OpenEvidence source={undefined} /> };
export const DrawerLoadFailed: Story = { render: () => <OpenEvidence source={undefined} failed /> };

export const RoutePreviewFromFixture: Story = {
  render: () => (
    <div className="max-w-[1080px]">
      <RoutePreview preview={routePreview} />
    </div>
  ),
};

export const RoutePreviewFailed: Story = {
  render: () => (
    <div className="max-w-[1080px]">
      <RoutePreview preview={failedPreview} />
    </div>
  ),
};
