"use client";
// What each chapter shows in this build. You edits the real profile; Routes shows the labelled
// fixture preview in the fixture workspace; the other chapters say what they will hold, which
// answers they depend on, and what to do next (spec section 3: useful, honest empty states).
import Link from "next/link";
import type { ProfileOut } from "@/generated/api";
import { CHAPTERS, type ChapterId, chapterHref } from "@/lib/chapters";
import type { RoutePreview as Preview } from "@/lib/fixtures/trace";
import { describeField } from "@/lib/profile";
import { type ChapterNeeds, chapterNeeds } from "@/lib/readiness";
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
  /** What the chapter will hold, in one or two sentences. */
  purpose: string;
  /** Why it is empty now, when nothing it starts from is missing. */
  notYet: string;
};

const PLANNED: Record<Exclude<ChapterId, "you" | "routes">, Planned> = {
  roles: {
    title: "Roles",
    purpose:
      "Role cards and a map of employers and listings for your targets in your work areas, with the sources checked and their coverage.",
    notYet:
      "Role research isn't part of this build yet, so no listings have been searched. When it arrives, a search that finds nothing will say which sources it checked.",
  },
  skills: {
    title: "Skills",
    purpose:
      "What each target requires, what you have shown, what is planned and what is still unresolved, with the evidence behind each.",
    notYet:
      "The skills matrix isn't part of this build yet. Nothing has been assessed, so nothing is marked missing.",
  },
  options: {
    title: "Options",
    purpose:
      "Courses, work routes and funding for each gap, with provider, dates, cost and evidence to review.",
    notYet:
      "Option research isn't part of this build yet. No courses or funding have been searched.",
  },
  plan: {
    title: "Plan",
    purpose:
      "The route you choose, as a dated plan with its conditions, costs and one next action.",
    notYet: "No plan has been chosen. A plan starts from a route you select in Routes.",
  },
};

const labels = (names: ProfileFieldName[]) =>
  names.map((name) => PROFILE_FIELDS[name].label.toLowerCase()).join(", ");

function Needs({ profile, needs }: { profile: ProfileOut; needs: ChapterNeeds }) {
  if (needs.uses.length === 0) return null;
  return (
    <div className="grid gap-8">
      <p className="section-title">Uses these answers from You</p>
      <dl className="kv">
        {needs.uses.map((name) => (
          <div key={name} className="contents">
            <dt>{PROFILE_FIELDS[name].label}</dt>
            <dd>{describeField(profile.document[name])}</dd>
          </div>
        ))}
      </dl>
      {needs.lessPrecise.map((name) => (
        <p key={name} className="small">
          Less precise without {PROFILE_FIELDS[name].label.toLowerCase()} (
          {describeField(profile.document[name])}): {PROFILE_FIELDS[name].lessPrecise}
        </p>
      ))}
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
  const needs = chapterNeeds(id, profile.document);
  const you = (
    <Link className="btn btn-secondary" href={chapterHref(workspaceId, "you")}>
      Review what we know
    </Link>
  );
  return (
    <>
      <h1 className="page-title">{planned.title}</h1>
      <p className="measure">{planned.purpose}</p>
      {needs.notAsked.length > 0 ? (
        <EmptyState
          state="blocked_missing_information"
          title="Needs answers in You first"
          next={you}
        >
          <p>
            Not asked yet: {labels(needs.notAsked)}. This chapter starts from them. Unknown is an
            answer too: it is never filled in with a guess.
          </p>
          <Needs profile={profile} needs={needs} />
        </EmptyState>
      ) : (
        <EmptyState state="notStarted" title={`No ${planned.title.toLowerCase()} yet`} next={you}>
          <p>{planned.notYet}</p>
          {needs.withoutStart.length > 0 && (
            <p>
              Your answer for {labels(needs.withoutStart)} is not a specific one, so there is
              nothing to start from yet. Helping you choose arrives with the interview.
            </p>
          )}
          <Needs profile={profile} needs={needs} />
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

  // While loading or after a failed load the page still says which chapter it is.
  const title = (
    <h1 className="page-title">{CHAPTERS.find((item) => item.id === chapter)?.label}</h1>
  );
  let body: React.ReactNode;
  if (profile === undefined && profileError) {
    body = (
      <>
        {title}
        <RequestFailure error={profileError} />
      </>
    );
  } else if (profile === undefined) {
    body = (
      <>
        {title}
        <LoadingState stage="Loading what we know" />
      </>
    );
  } else if (chapter === "you") {
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
