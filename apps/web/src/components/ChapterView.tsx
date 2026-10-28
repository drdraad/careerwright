"use client";
// What each chapter shows in this build. You edits the real profile; Routes shows the labelled
// fixture preview in the fixture workspace; the other chapters say what they will hold, which
// answers they depend on, and what to do next (spec section 3: useful, honest empty states).
import Link from "next/link";
import type { ProfileOut } from "@/generated/api";
import { type ChapterId, chapterHref } from "@/lib/chapters";
import type { RoutePreview as Preview } from "@/lib/fixtures/trace";
import { describeField } from "@/lib/profile";
import { PROFILE_FIELDS, type ProfileFieldName } from "@/lib/vocabulary";
import { EmptyState } from "./EmptyState";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";
import { ProfileEditor } from "./ProfileEditor";
import { RoutePreview } from "./RoutePreview";
import { StatusBadge } from "./Status";
import { useWorkspaceData } from "./WorkspaceShell";

type Planned = {
  title: string;
  needs: ProfileFieldName[];
  /** What the chapter will hold, in one or two sentences. */
  purpose: string;
  /** Why it is empty now, when nothing it needs is missing. */
  notYet: string;
};

const PLANNED: Record<Exclude<ChapterId, "you" | "routes">, Planned> = {
  roles: {
    title: "Roles",
    needs: ["target_titles", "cities"],
    purpose:
      "Role cards and a map of employers and listings for your targets in your work areas, with the sources checked and their coverage.",
    notYet:
      "Role research isn't part of this build yet, so no listings have been searched. When it arrives, a search that finds nothing will say which sources it checked.",
  },
  skills: {
    title: "Skills",
    needs: ["target_titles", "current_role"],
    purpose:
      "What each target requires, what you have shown, what is planned and what is still unresolved, with the evidence behind each.",
    notYet:
      "The skills matrix isn't part of this build yet. Nothing has been assessed, so nothing is marked missing.",
  },
  options: {
    title: "Options",
    needs: ["target_titles", "weekly_study_hours", "direct_spend_cap", "monthly_payment_cap"],
    purpose:
      "Courses, work routes and funding for each gap, with provider, dates, cost and evidence to review.",
    notYet:
      "Option research isn't part of this build yet. No courses or funding have been searched.",
  },
  plan: {
    title: "Plan",
    needs: [],
    purpose:
      "The route you choose, as a dated plan with its conditions, costs and one next action.",
    notYet: "No plan has been chosen. A plan starts from a route you select in Routes.",
  },
};

function Needs({ profile, needs }: { profile: ProfileOut; needs: ProfileFieldName[] }) {
  if (needs.length === 0) return null;
  return (
    <div className="grid gap-8">
      <p className="section-title">Uses these answers from You</p>
      <dl className="kv">
        {needs.map((name) => (
          <div key={name} className="contents">
            <dt>{PROFILE_FIELDS[name].label}</dt>
            <dd>{describeField(profile.document[name])}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function PlannedChapter({
  id,
  profile,
  workspaceId,
}: {
  id: keyof typeof PLANNED;
  profile: ProfileOut;
  workspaceId: string;
}) {
  const planned = PLANNED[id];
  const missing = planned.needs.filter((name) => profile.document[name].state !== "provided");
  const you = (
    <Link className="btn btn-secondary" href={chapterHref(workspaceId, "you")}>
      Review what we know
    </Link>
  );
  return (
    <>
      <h1 className="page-title">{planned.title}</h1>
      <p className="measure">{planned.purpose}</p>
      {missing.length > 0 ? (
        <EmptyState
          state="blocked_missing_information"
          title="Needs answers in You first"
          next={you}
        >
          <p>
            Not answered yet:{" "}
            {missing.map((name) => PROFILE_FIELDS[name].label.toLowerCase()).join(", ")}. Each can
            also be marked Unknown; the result is then less precise, never filled in with a guess.
          </p>
          <Needs profile={profile} needs={planned.needs} />
        </EmptyState>
      ) : (
        <EmptyState state="notStarted" title={`No ${planned.title.toLowerCase()} yet`} next={you}>
          <p>{planned.notYet}</p>
          <Needs profile={profile} needs={planned.needs} />
        </EmptyState>
      )}
    </>
  );
}

export function ChapterView({
  chapter,
  routePreview,
}: {
  chapter: ChapterId;
  routePreview: Preview | null;
}) {
  const { workspace, profile, profileError } = useWorkspaceData();
  const surface = chapter === "roles" || chapter === "routes" ? "on-space" : "on-reading";

  let body: React.ReactNode;
  if (profile === undefined && profileError) body = <RequestFailure error={profileError} />;
  else if (profile === undefined) body = <LoadingState stage="Loading what we know" />;
  else if (chapter === "you") {
    body = (
      <>
        <h1 className="page-title">You</h1>
        <section className="grid gap-12" aria-labelledby="conversation">
          <h2 id="conversation" className="section-title">
            Conversation
          </h2>
          <StatusBadge state="notStarted" detail="the interview isn't part of this build yet" />
          <p className="small measure">
            Answer directly below instead. Later, Nessa will ask one question at a time and propose
            changes here for you to accept, edit or undo.
          </p>
        </section>
        <ProfileEditor
          key={workspace.workspace_id}
          workspaceId={workspace.workspace_id}
          profile={profile}
        />
      </>
    );
  } else if (chapter === "routes") {
    body = (
      <>
        <h1 className="page-title">Routes</h1>
        {workspace.fixture && routePreview !== null ? (
          <RoutePreview preview={routePreview} />
        ) : (
          <EmptyState
            state="notStarted"
            title="No routes yet"
            next={
              <Link className="btn btn-secondary" href={chapterHref(workspace.workspace_id, "you")}>
                Review what we know
              </Link>
            }
          >
            <p>
              Routes are compared once your options are reviewed. Nessa's route search isn't part of
              this build yet, so no route has been computed for this workspace.
            </p>
          </EmptyState>
        )}
      </>
    );
  } else {
    body = <PlannedChapter id={chapter} profile={profile} workspaceId={workspace.workspace_id} />;
  }

  return <div className={`chapter ${surface}`}>{body}</div>;
}
