"use client";
// The six-chapter shell around one workspace (spec section 3, UI-09): chapter rail or menu,
// workspace strip, the chapter's work area and the evidence drawer. It owns the session
// checks (signed in, invited, workspace visible) and the workspace's live status events;
// chapters read the same server state through `useWorkspaceData`.
import { usePathname, useRouter, useSelectedLayoutSegment } from "next/navigation";
import { createContext, type ReactNode, useContext, useEffect, useState } from "react";
import type { ProfileOut, WorkspaceOut } from "@/generated/api";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CHAPTERS, type ChapterId, type ChapterProgress, isChapter } from "@/lib/chapters";
import type { StreamStatus } from "@/lib/events";
import { useMe, useProfile, useWorkspace, useWorkspaceEvents, useWorkspaces } from "@/lib/queries";
import { ChapterMenu, ChapterRail } from "./ChapterNav";
import { EvidenceDrawer, useEvidence } from "./EvidenceDrawer";
import { PageFrame, PageLoading, RequestFailure } from "./PageState";
import { SyntheticLabel } from "./Status";
import { WorkspaceStrip } from "./WorkspaceStrip";

type WorkspaceData = {
  workspace: WorkspaceOut;
  profile: ProfileOut | undefined;
  profileError: unknown;
  events: StreamStatus;
};

const WorkspaceContext = createContext<WorkspaceData | null>(null);

export function useWorkspaceData(): WorkspaceData {
  const value = useContext(WorkspaceContext);
  if (value === null) throw new Error("useWorkspaceData outside WorkspaceShell");
  return value;
}

const CALM_KEY = "nessa.calm";

/** Calm mode is a per-viewer convenience; storage may be unavailable, which only loses it. */
function useCalmMode(): [boolean, (calm: boolean) => void] {
  const [calm, setCalm] = useState(false);
  useEffect(() => {
    try {
      setCalm(window.localStorage.getItem(CALM_KEY) === "true");
    } catch {
      // Private mode or blocked storage: calm mode simply starts off.
    }
  }, []);
  useEffect(() => {
    document.documentElement.dataset.calm = String(calm);
  }, [calm]);
  const update = (next: boolean) => {
    setCalm(next);
    try {
      window.localStorage.setItem(CALM_KEY, String(next));
    } catch {
      // As above: the choice holds for this page only.
    }
  };
  return [calm, update];
}

/**
 * Chapters opened in this browser session, per workspace (a per-viewer convenience, so
 * session storage; unavailable storage only forgets the marks).
 */
function useVisited(workspaceId: string, chapter: ChapterId): ReadonlySet<ChapterId> {
  const key = `nessa.visited.${workspaceId}`;
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
  const [calm, setCalm] = useCalmMode();
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
  const events = useWorkspaceEvents(workspaceId, opened, workspace.data?.last_event_seq);
  const visited = useVisited(workspaceId, chapter);
  // "Showing what was last loaded" only when something was loaded and its refresh failed.
  const refreshFailed =
    (me.isError && me.data !== undefined) ||
    (workspace.isError && workspace.data !== undefined) ||
    (profile.isError && profile.data !== undefined);

  if (auth.state.status !== "signed_in") return <PageLoading stage="Checking your sign-in" />;
  // Only a first load that fails replaces the shell. A failed refresh (Nessa restarting) keeps
  // what was last loaded on screen and says so in the strip; the next event refreshes it.
  if (
    (me.isError && me.data === undefined) ||
    (workspace.isError && workspace.data === undefined)
  ) {
    const error = me.error ?? workspace.error;
    const notInvited = error instanceof ApiError && error.code === "NOT_INVITED";
    return (
      <PageFrame>
        <h1 className="page-title">
          {notInvited ? "This account isn't invited" : "This workspace can't be shown"}
        </h1>
        <RequestFailure
          error={error}
          actions={
            <>
              {!notInvited && (
                <a className="btn btn-secondary" href="/">
                  Your workspaces
                </a>
              )}
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => void auth.signOut()}
              >
                Sign out
              </button>
            </>
          }
        />
      </PageFrame>
    );
  }
  if (workspace.data === undefined) return <PageLoading stage="Opening your workspace" />;

  const surface = CHAPTERS.find((item) => item.id === chapter)?.surface ?? "reading";
  const progress = progressOf(visited, profile.data);
  const data: WorkspaceData = {
    workspace: workspace.data,
    profile: profile.data,
    profileError: profile.error,
    events: events.status,
  };

  return (
    <WorkspaceContext.Provider value={data}>
      <a
        className="on-space btn btn-primary sr-only focus:not-sr-only focus:absolute focus:left-16 focus:top-16 focus:z-40"
        href="#main"
      >
        Skip to the chapter
      </a>
      <div className="app" data-drawer={evidence === null ? "closed" : "open"}>
        <ChapterRail workspaceId={workspaceId} current={chapter} progress={progress} />
        <div className="topbar on-space">
          <ChapterMenu workspaceId={workspaceId} current={chapter} progress={progress} />
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
          refreshFailed={refreshFailed}
          email={auth.state.email}
          calm={calm}
          onCalmChange={setCalm}
          onSignOut={() => void auth.signOut()}
        />
        <main id="main" tabIndex={-1} className={`workarea on-${surface}`}>
          {children}
        </main>
        <EvidenceDrawer />
      </div>
    </WorkspaceContext.Provider>
  );
}
