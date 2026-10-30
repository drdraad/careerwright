"use client";
// What each chapter shows in this build, as its place in the world (plan section 4). You holds
// the conversation, what we know and the directions to explore; Routes shows the labelled
// fixture preview in the fixture workspace; the other chapters are places not built yet, and
// say so plainly: what the place is, what it will hold, which answers it depends on and what
// to do next (spec section 3: useful, honest empty states).
import Link from "next/link";
import type { ReactNode } from "react";
import type { ProfileOut } from "@/generated/api";
import { CHAPTERS, type ChapterId, chapterHref } from "@/lib/chapters";
import type { RoutePreview as Preview } from "@/lib/fixtures/trace";
import { describeField } from "@/lib/profile";
import { type ChapterNeeds, chapterNeeds } from "@/lib/readiness";
import { PROFILE_FIELDS, type ProfileFieldName } from "@/lib/vocabulary";
import { PLACES } from "@/lib/world/places";
import { Button } from "./Button";
import { EmptyState } from "./EmptyState";
import { Glyph } from "./Glyph";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";
import { RoutePreview } from "./RoutePreview";
import { useWorkspaceData } from "./WorkspaceShell";
import { YouChapter } from "./YouChapter";

type Planned = {
  title: string;
  /** What the chapter will hold, in one or two sentences. */
  purpose: string;
  /** Why it is empty now, when nothing it starts from is missing. */
  notYet: string;
  /** The one action's label, saying what it is for. */
  next: string;
};

const PLANNED: Record<Exclude<ChapterId, "you" | "routes">, Planned> = {
  roles: {
    title: "Roles",
    purpose:
      "Role cards and a map of employers and listings for your targets in your work areas, with the sources checked and their coverage.",
    notYet:
      "Role research isn't part of this build yet, so no listings have been searched. When it arrives, a search that finds nothing will say which sources it checked.",
    next: "Review what we know",
  },
  skills: {
    title: "Skills",
    purpose:
      "What each target requires, what you have shown, what is planned and what is still unresolved, with the evidence behind each.",
    notYet:
      "The skills matrix isn't part of this build yet. Nothing has been assessed, so nothing is marked missing.",
    next: "Review what we know",
  },
  options: {
    title: "Options",
    purpose:
      "Courses, work routes and funding for each gap, with provider, dates, cost and evidence to review.",
    notYet:
      "Option research isn't part of this build yet. No courses or funding have been searched.",
    next: "Review what we know",
  },
  plan: {
    title: "Plan",
    purpose:
      "The route you choose, as a dated plan with its conditions, costs and one next action.",
    // V-06: the limitation in words, and never a hint that a fixture preview becomes a plan.
    notYet:
      "Plan selection isn't part of this build yet, so no plan has been made. When it is, a plan will start from a route Careerwright computes from your answers, never from a fixture preview.",
    next: "Review your answers in You",
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

/** The head of a place not built yet: the honest state first, then where it is in the world. */
function NotBuiltYet({ id, title }: { id: ChapterId; title: string }) {
  return (
    <>
      <p className="place-kicker">
        <Glyph name="blocked" />
        Not built yet
      </p>
      <h1 className="page-title">{title}</h1>
      <p className="place-where">{PLACES[id].where}</p>
    </>
  );
}

/** A chapter whose feature belongs to a later sprint: its purpose and the answers it uses. */
export function PlannedChapter({
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
      {planned.next}
    </Link>
  );
  return (
    <>
      <NotBuiltYet id={id} title={planned.title} />
      <p className="measure small muted">{planned.purpose}</p>
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
  const { workspace, profile, profileError, retryProfile } = useWorkspaceData();

  // While loading or after a failed load the page still says which chapter it is.
  const label = CHAPTERS.find((item) => item.id === chapter)?.label ?? "";
  const title = <h1 className="page-title">{label}</h1>;
  // A built chapter reads on a glass panel; a place not built yet is a small card in the world.
  let shape: "panel" | "place" = "panel";
  let body: ReactNode;
  if (profile === undefined && profileError) {
    shape = "place";
    body = (
      <>
        {title}
        <RequestFailure
          error={profileError}
          actions={
            <Button variant="secondary" onClick={retryProfile}>
              Try again
            </Button>
          }
        />
      </>
    );
  } else if (profile === undefined) {
    shape = "place";
    body = (
      <>
        {title}
        <LoadingState stage="Loading what we know" />
      </>
    );
  } else if (chapter === "you") {
    body = <YouChapter workspace={workspace} profile={profile} />;
  } else if (chapter === "routes" && workspace.fixture && routePreview !== null) {
    body = (
      <>
        <h1 className="page-title">Routes</h1>
        <RoutePreview preview={routePreview} />
      </>
    );
  } else if (chapter === "routes") {
    shape = "place";
    body = (
      <>
        <NotBuiltYet id="routes" title="Routes" />
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
            Routes are compared once your options are reviewed. Careerwright's route search isn't
            part of this build yet, so no route has been computed for this workspace.
          </p>
        </EmptyState>
      </>
    );
  } else {
    shape = "place";
    body = <PlannedChapter id={chapter} profile={profile} workspaceId={workspace.workspace_id} />;
  }

  return (
    <div
      className={`chapter on-reading chapter-${shape}${chapter === "you" ? " chapter-you" : ""}`}
      data-covers-world
      data-world-panel
    >
      {body}
    </div>
  );
}
