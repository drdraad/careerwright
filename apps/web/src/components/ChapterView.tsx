"use client";
// What each chapter shows in this build, as its place in the world (plan section 4). You holds
// the conversation, what we know and the directions to explore; the other chapters are places
// not built yet, and say so plainly in a short card: where the place is, why it is empty and
// what to do next, with what it will hold and which answers it depends on one step away (spec
// section 3: useful, honest empty states). The fixture route preview left the person's path
// (the audit's ruling): it stays in Storybook and the design review until Routes is built.
import Link from "next/link";
import type { ReactNode } from "react";
import type { ProfileOut } from "@/generated/api";
import { CHAPTERS, type ChapterId, chapterHref } from "@/lib/chapters";
import { describeField } from "@/lib/profile";
import { type ChapterNeeds, chapterNeeds } from "@/lib/readiness";
import { PROFILE_FIELDS, type ProfileFieldName } from "@/lib/vocabulary";
import { PLACES } from "@/lib/world/places";
import { Button } from "./Button";
import { Glyph } from "./Glyph";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";
import { useWorkspaceData } from "./WorkspaceShell";
import { YouChapter } from "./YouChapter";

type Planned = {
  title: string;
  /** What the chapter will hold, in one or two sentences (one step away, under "More"). */
  purpose: string;
  /** Why it is empty now, when nothing it starts from is missing: one sentence on the card. */
  notYet: string;
  /** The one action's label, saying what it is for. */
  next: string;
};

const PLANNED: Record<Exclude<ChapterId, "you" | "routes">, Planned> = {
  roles: {
    title: "Roles",
    purpose:
      "Role cards and a map of employers and listings for your targets in your work areas, with the sources checked and their coverage. A search that finds nothing will say which sources it checked.",
    notYet: "Role research isn't ready yet, so no listings have been searched.",
    next: "Review what we know",
  },
  skills: {
    title: "Skills",
    purpose:
      "What each target requires, what you have shown, what is planned and what is still unresolved, with the evidence behind each.",
    notYet: "Skills checking isn't ready yet, so nothing has been assessed or marked missing.",
    next: "Review what we know",
  },
  options: {
    title: "Options",
    purpose:
      "Courses, work routes and funding for each gap, with provider, dates, cost and evidence to review.",
    notYet: "Option research isn't ready yet, so no courses or funding have been searched.",
    next: "Review what we know",
  },
  plan: {
    title: "Plan",
    purpose:
      "The route you choose, as a dated plan with its conditions, costs and one next action.",
    // V-06: the limitation in words, and never a hint that a fixture preview becomes a plan.
    notYet:
      "Plan selection isn't ready yet, so no plan has been made. When it is, a plan will start from a route Careerwright computes from your answers, never from a fixture preview.",
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

/**
 * A place not built yet, as the design reference draws it: the honest state, the place's
 * name, where it is in the world, one sentence on why it is empty and the one action. What it
 * will hold and the answers it uses are one step away, under "More about this place".
 */
function NotBuiltYet({
  id,
  title,
  why,
  next,
  more,
}: {
  id: ChapterId;
  title: string;
  why: ReactNode;
  next: ReactNode;
  more: ReactNode;
}) {
  return (
    <>
      <p className="place-kicker">
        <Glyph name="blocked" />
        Not built yet
      </p>
      <h1 className="page-title">{title}</h1>
      <p className="place-where">{PLACES[id].where}</p>
      <p className="measure small muted">{why}</p>
      <div className="flex flex-wrap gap-8">{next}</div>
      <details className="place-more">
        <summary>More about this place</summary>
        <div className="grid gap-12 pt-12">{more}</div>
      </details>
    </>
  );
}

/** A chapter whose feature belongs to a later sprint: its place, and why it is empty. */
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
  // A starting answer never asked is the reason it cannot start; otherwise, the build.
  const why =
    needs.notAsked.length > 0
      ? `Needs answers in You first. Not asked yet: ${labels(needs.notAsked)}.`
      : planned.notYet;
  return (
    <NotBuiltYet
      id={id}
      title={planned.title}
      why={why}
      next={you}
      more={
        <>
          <p className="small">{planned.purpose}</p>
          {needs.notAsked.length > 0 && (
            <p className="small">
              This chapter starts from {labels(needs.notAsked)}. Unknown is an answer too: it is
              never filled in with a guess.
            </p>
          )}
          {needs.withoutStart.length > 0 && (
            <p className="small">
              Your answer for {labels(needs.withoutStart)} is not a specific one, so there is
              nothing to start from yet. Helping you choose arrives with the interview.
            </p>
          )}
          <Needs profile={profile} needs={needs} />
        </>
      }
    />
  );
}

export function ChapterView({ chapter }: { chapter: ChapterId }) {
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
  } else if (chapter === "routes") {
    shape = "place";
    body = (
      <NotBuiltYet
        id="routes"
        title="Routes"
        why="Route search isn't ready yet, so no route has been worked out for this workspace."
        next={
          <Link className="btn btn-secondary" href={chapterHref(workspace.workspace_id, "you")}>
            Review what we know
          </Link>
        }
        more={
          <p className="small">
            Routes are compared once your options are reviewed: every way to a destination, with how
            long it takes and what it costs.
          </p>
        }
      />
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
