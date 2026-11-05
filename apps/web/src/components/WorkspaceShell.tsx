"use client";
// One workspace session and atmosphere across all six chapters. Chapters share the same server
// state, account controls and evidence drawer; support stills the world while it is shown.
import { usePathname, useRouter, useSearchParams, useSelectedLayoutSegment } from "next/navigation";
import { createContext, type ReactNode, useContext, useEffect } from "react";
import type { ProfileOut, WorkspaceOut } from "@/generated/api";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { type ChapterId, isChapter } from "@/lib/chapters";
import type { StreamStatus } from "@/lib/events";
import { type Journey, journeyOf } from "@/lib/journey";
import { readPlanCandidate, useCurrentPlan } from "@/lib/planQueries";
import {
  refreshFailed,
  useCheckpoint,
  useMe,
  useProfile,
  useWorkspace,
  useWorkspaceEvents,
  useWorkspaces,
} from "@/lib/queries";
import { useLatestRouteSolve } from "@/lib/routeQueries";
import { useSkills } from "@/lib/skillQueries";
import { worldFromProfile } from "@/lib/world/model";
import { SupportShown, useSupportPanels, useWorldSettings } from "@/lib/world/settings";
import { Button } from "./Button";
import { ChapterMenu, ChapterRail } from "./ChapterNav";
import { ConversationTone } from "./ConversationTone";
import { DecisionAtmosphere } from "./DecisionAtmosphere";
import { EvidenceDrawer, useEvidence } from "./EvidenceDrawer";
import { MetaKeySetting } from "./KeySetup";
import { ModelSpending } from "./ModelSpending";
import { NotInvited, PageFrame, PageLoading, RequestFailure } from "./PageState";
import { SyntheticLabel } from "./Status";
import { WorkspaceStrip } from "./WorkspaceStrip";
import { CalmMode, StillWhileSupport, WorldControls } from "./WorldControls";

type WorkspaceData = {
  workspace: WorkspaceOut;
  profile: ProfileOut | undefined;
  profileError: unknown;
  /** Load the profile again after a failed load, in place (V-02). */
  retryProfile(): void;
  events: StreamStatus;
  journey: Journey;
  planCandidate: boolean | null;
};

const WorkspaceContext = createContext<WorkspaceData | null>(null);

export function useWorkspaceData(): WorkspaceData {
  const value = useContext(WorkspaceContext);
  if (value === null) throw new Error("useWorkspaceData outside WorkspaceShell");
  return value;
}

export function WorkspaceShell({
  workspaceId,
  children,
}: {
  workspaceId: string;
  children: ReactNode;
}) {
  const segment = useSelectedLayoutSegment();
  const chapter: ChapterId = segment !== null && isChapter(segment) ? segment : "you";
  const auth = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const search = useSearchParams();
  const planCandidate = chapter === "plan" && readPlanCandidate(search.toString()) !== null;
  const { evidence, close } = useEvidence();
  const world = useWorldSettings();
  // A calm support panel is showing (each panel reports itself): the world stays still.
  const [supportShown, reportSupport] = useSupportPanels();
  const signedIn = auth.state.status === "signed_in";

  useEffect(() => {
    if (auth.state.status === "signed_out") {
      router.replace(`/sign-in?next=${encodeURIComponent(pathname)}`);
    }
  }, [auth.state.status, pathname, router]);

  // A drawer belongs to the chapter that opened it.
  // biome-ignore lint/correctness/useExhaustiveDependencies: close only when the chapter changes
  useEffect(() => close(), [chapter]);

  const me = useMe(signedIn);
  // Loaded once is enough to keep going: a failed refresh must not stop the event stream,
  // which is what notices the API is back.
  const invited = signedIn && me.data !== undefined;
  const workspace = useWorkspace(workspaceId, invited);
  const opened = invited && workspace.data !== undefined;
  const profile = useProfile(workspaceId, opened);
  const workspaces = useWorkspaces(invited);
  const events = useWorkspaceEvents(workspaceId, {
    enabled: opened,
    startAfter: workspace.data?.last_event_seq,
    token: auth.token,
    session: auth.state.status === "signed_in" ? auth.state.uid : "",
  });
  const target = profile.data?.document.target_titles.value?.[0] ?? "";
  const hasTarget = profile.data?.document.target_titles.state === "provided" && target !== "";
  const skills = useSkills(workspaceId, opened && hasTarget);
  const checkpoint = useCheckpoint(workspaceId, opened && hasTarget);
  const latestRoute = useLatestRouteSolve(workspaceId, hasTarget ? null : "");
  const currentPlan = useCurrentPlan(workspaceId, opened);
  const shownRoute =
    latestRoute.data?.latest?.run.status === "complete"
      ? latestRoute.data.latest
      : latestRoute.data?.kept;
  const journey = journeyOf({
    profile: profile.data,
    skills: skills.data,
    checkpoint: checkpoint.data,
    routeFound: (shownRoute?.result?.schedules.length ?? 0) > 0,
    planSaved: currentPlan.data !== null && currentPlan.data !== undefined,
    planCandidate: planCandidate === true && chapter === "plan",
  });

  if (auth.state.status !== "signed_in") return <PageLoading stage="Checking your sign-in" />;
  // Only a first load that fails replaces the shell. A failed refresh (Careerwright restarting) keeps
  // what was last loaded on screen and says so in the strip; the next event refreshes it.
  const prerequisite =
    chapter === "routes" && hasTarget ? checkpoint : chapter === "plan" ? currentPlan : null;
  const required = [me, workspace, ...(prerequisite === null ? [] : [prerequisite])];
  const failed = required.find((load) => load.isError && load.data === undefined);
  if (failed) {
    const error = failed.error;
    const signOut = (
      <button type="button" className="btn btn-secondary" onClick={() => void auth.signOut()}>
        Sign out
      </button>
    );
    if (error instanceof ApiError && error.code === "NOT_INVITED") {
      return (
        <PageFrame>
          <NotInvited error={error} actions={signOut} />
        </PageFrame>
      );
    }
    return (
      <PageFrame>
        <h1 className="page-title">This workspace can't be shown</h1>
        <RequestFailure
          error={error}
          actions={
            <>
              <Button onClick={() => void Promise.all(required.map((load) => load.refetch()))}>
                Try again
              </Button>
              <a className="btn btn-secondary" href="/">
                Your workspaces
              </a>
              {signOut}
            </>
          }
        />
      </PageFrame>
    );
  }
  if (workspace.data === undefined) return <PageLoading stage="Opening your workspace" />;
  if (prerequisite !== null && prerequisite.data === undefined) {
    return (
      <PageLoading
        stage={chapter === "plan" ? "Checking your saved plan" : "Checking what the routes need"}
      />
    );
  }

  const data: WorkspaceData = {
    workspace: workspace.data,
    profile: profile.data,
    profileError: profile.error,
    retryProfile: () => void profile.refetch(),
    events: events.status,
    journey,
    planCandidate,
  };

  return (
    <WorkspaceContext.Provider value={data}>
      <SupportShown.Provider value={reportSupport}>
        <a
          className="on-space btn btn-primary sr-only focus:not-sr-only focus:absolute focus:left-16 focus:top-16 focus:z-40"
          href="#main"
        >
          Skip to the chapter
        </a>
        <div
          className="app career-workspace"
          data-drawer={evidence === null ? "closed" : "open"}
          data-still={world.reduced || world.calm || world.paused || supportShown}
        >
          <DecisionAtmosphere
            settings={world}
            distress={supportShown}
            showControl={false}
            lit={profile.data === undefined ? null : worldFromProfile(profile.data).lit}
          />
          <ChapterRail workspaceId={workspaceId} current={chapter} progress={journey.progress} />
          <div className="topbar on-space" data-covers-world>
            <ChapterMenu workspaceId={workspaceId} current={chapter} progress={journey.progress} />
            {supportShown && <StillWhileSupport />}
            {workspace.data.synthetic && <SyntheticLabel />}
          </div>
          <WorkspaceStrip
            workspace={workspace.data}
            profile={profile.data}
            profileFailed={profile.isError}
            workspaces={workspaces.data ?? [workspace.data]}
            workspacesFailed={workspaces.isError}
            events={events.status}
            onReconnect={events.restart}
            refreshFailed={refreshFailed(me, workspace, profile)}
            email={auth.state.email}
            controls={<WorldControls settings={world} />}
            status={supportShown && <StillWhileSupport />}
            settings={
              // Calm mode is this viewer's, and below a desktop's width the world's controls
              // join it; the tone, the model spending and the stored Meta key (session W2: no
              // longer under every conversation), under the preferences heading, are this
              // workspace's.
              <>
                <div className="menu-world">
                  <WorldControls settings={world} />
                </div>
                <CalmMode settings={world} />
                <ConversationTone workspaceId={workspaceId} />
                <ModelSpending
                  workspaceId={workspaceId}
                  demo={workspace.data.data_mode === "demo"}
                />
                <MetaKeySetting workspace={workspace.data} />
              </>
            }
            onSignOut={() => void auth.signOut()}
          />
          <main id="main" tabIndex={-1} className="workarea">
            {children}
          </main>
          <EvidenceDrawer />
        </div>
      </SupportShown.Provider>
    </WorkspaceContext.Provider>
  );
}
