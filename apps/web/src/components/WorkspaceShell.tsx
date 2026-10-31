"use client";
// The six-chapter shell around one workspace (spec section 3, UI-09): one persistent world
// behind everything (plan section 4), with the chapter rail or menu, the workspace strip and
// its world controls, the chapter's place and the evidence drawer over it. While the calm
// support panel shows, the world is still (ADR 0007, plan section 4). It owns the session
// checks (signed in, invited, workspace visible) and the workspace's live status events;
// chapters read the same server state through `useWorkspaceData`.
import { usePathname, useRouter, useSelectedLayoutSegment } from "next/navigation";
import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";
import type { ProfileOut, WorkspaceOut } from "@/generated/api";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { type ChapterId, type ChapterProgress, isChapter } from "@/lib/chapters";
import type { StreamStatus } from "@/lib/events";
import {
  firstLoadFailed,
  refreshFailed,
  useMe,
  useProfile,
  useWorkspace,
  useWorkspaceEvents,
  useWorkspaces,
} from "@/lib/queries";
import { worldFromProfile } from "@/lib/world/model";
import { SupportShown, useWorldSettings } from "@/lib/world/settings";
import { ChapterMenu, ChapterRail } from "./ChapterNav";
import { ConversationTone } from "./ConversationTone";
import { EvidenceDrawer, useEvidence } from "./EvidenceDrawer";
import { NotInvited, PageFrame, PageLoading, RequestFailure } from "./PageState";
import { SyntheticLabel } from "./Status";
import { WorkspaceStrip } from "./WorkspaceStrip";
import { World } from "./World";
import { CalmMode, StillWhileSupport, WorldControls } from "./WorldControls";

type WorkspaceData = {
  workspace: WorkspaceOut;
  profile: ProfileOut | undefined;
  profileError: unknown;
  /** Load the profile again after a failed load, in place (V-02). */
  retryProfile(): void;
  events: StreamStatus;
};

const WorkspaceContext = createContext<WorkspaceData | null>(null);

export function useWorkspaceData(): WorkspaceData {
  const value = useContext(WorkspaceContext);
  if (value === null) throw new Error("useWorkspaceData outside WorkspaceShell");
  return value;
}

/**
 * Chapters opened in this browser session, per workspace (a per-viewer convenience, so
 * session storage; unavailable storage only forgets the marks).
 */
function useVisited(workspaceId: string, chapter: ChapterId): ReadonlySet<ChapterId> {
  const key = `careerwright.visited.${workspaceId}`;
  const [visited, setVisited] = useState<ReadonlySet<ChapterId>>(new Set([chapter]));
  useEffect(() => {
    let stored: ChapterId[] = [];
    try {
      stored = (JSON.parse(window.sessionStorage.getItem(key) ?? "[]") as string[]).filter(
        isChapter,
      );
    } catch {
      // Blocked or corrupt storage: start with the current chapter only.
    }
    const next = new Set<ChapterId>([...stored, chapter]);
    setVisited(next);
    try {
      window.sessionStorage.setItem(key, JSON.stringify([...next]));
    } catch {
      // As above.
    }
  }, [key, chapter]);
  return visited;
}

function progressOf(
  visited: ReadonlySet<ChapterId>,
  profile: ProfileOut | undefined,
): Partial<Record<ChapterId, ChapterProgress>> {
  const progress: Partial<Record<ChapterId, ChapterProgress>> = {};
  for (const chapter of visited) progress[chapter] = "visited";
  if (profile !== undefined && profile.version > 0) progress.you = "visited";
  return progress;
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
  const { evidence, close } = useEvidence();
  const world = useWorldSettings();
  // The calm support panel is showing (the conversation reports it): the world stays still.
  const [supportShown, setSupportShown] = useState(false);
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
  const visited = useVisited(workspaceId, chapter);
  const worldInput = useMemo(
    () => (profile.data === undefined ? null : worldFromProfile(profile.data)),
    [profile.data],
  );

  if (auth.state.status !== "signed_in") return <PageLoading stage="Checking your sign-in" />;
  // Only a first load that fails replaces the shell. A failed refresh (Careerwright restarting) keeps
  // what was last loaded on screen and says so in the strip; the next event refreshes it.
  if (firstLoadFailed(me, workspace)) {
    const error = me.error ?? workspace.error;
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

  const progress = progressOf(visited, profile.data);
  const data: WorkspaceData = {
    workspace: workspace.data,
    profile: profile.data,
    profileError: profile.error,
    retryProfile: () => void profile.refetch(),
    events: events.status,
  };

  return (
    <WorkspaceContext.Provider value={data}>
      <SupportShown.Provider value={setSupportShown}>
        <a
          className="on-space btn btn-primary sr-only focus:not-sr-only focus:absolute focus:left-16 focus:top-16 focus:z-40"
          href="#main"
        >
          Skip to the chapter
        </a>
        <div className="app" data-drawer={evidence === null ? "closed" : "open"}>
          <ChapterRail workspaceId={workspaceId} current={chapter} progress={progress} />
          <div className="topbar on-space" data-covers-world>
            <ChapterMenu workspaceId={workspaceId} current={chapter} progress={progress} />
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
            controls={<WorldControls settings={world} supportShown={supportShown} />}
            settings={
              // Calm mode is this viewer's; the tone, under its own heading, this workspace's.
              <>
                <CalmMode settings={world} />
                <ConversationTone workspaceId={workspaceId} />
              </>
            }
            onSignOut={() => void auth.signOut()}
          />
          <main id="main" tabIndex={-1} className="workarea">
            {children}
          </main>
          <EvidenceDrawer />
        </div>
        <World
          place={chapter}
          input={worldInput}
          calm={world.calm}
          paused={world.paused}
          distress={supportShown}
          sound={world.sound}
        />
      </SupportShown.Provider>
    </WorkspaceContext.Provider>
  );
}
