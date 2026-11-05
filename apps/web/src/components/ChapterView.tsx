"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { ReactNode } from "react";
import { CHAPTERS, type ChapterId, chapterHref } from "@/lib/chapters";
import type { Journey } from "@/lib/journey";
import { Button } from "./Button";
import { LoadingState } from "./LoadingState";
import { OptionsChapter } from "./OptionsChapter";
import { RequestFailure } from "./PageState";
import { PlanChapter } from "./PlanChapter";
import { RolesChapter } from "./RolesChapter";
import { RoutesChapter } from "./RoutesChapter";
import { SkillsChapter } from "./SkillsChapter";
import { useWorkspaceData } from "./WorkspaceShell";
import { YouChapter } from "./YouChapter";

function BlockedChapter({
  chapter,
  journey,
  workspaceId,
}: {
  chapter: ChapterId;
  journey: Journey;
  workspaceId: string;
}) {
  const target = journey.progress.you === "complete";
  const returnTo: ChapterId = !target
    ? "you"
    : chapter === "routes" || journey.progress.routes === "locked"
      ? "options"
      : "routes";
  const reason = !target
    ? "Choose a direction in You first. If you are unsure, explore suggestions there."
    : chapter === "routes" || journey.progress.routes === "locked"
      ? "Routes needs the planning answers shown under ‘Before a route search’ in Options."
      : "Search for a route in Routes and choose one before making a Plan.";
  return (
    <div className="grid gap-16">
      <h1 className="page-title">
        {CHAPTERS.find((item) => item.id === chapter)?.label} needs an earlier step
      </h1>
      <p>{reason}</p>
      <div>
        <Link className="btn btn-primary" href={chapterHref(workspaceId, returnTo)}>
          Open {CHAPTERS.find((item) => item.id === returnTo)?.label}
        </Link>
      </div>
    </div>
  );
}

export function ChapterView({ chapter }: { chapter: ChapterId }) {
  const search = useSearchParams().toString();
  const { workspace, profile, profileError, retryProfile, journey, planCandidate } =
    useWorkspaceData();
  const label = CHAPTERS.find((item) => item.id === chapter)?.label ?? "";
  let body: ReactNode;
  if (profile === undefined && profileError) {
    body = (
      <>
        <h1 className="page-title">{label}</h1>
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
    body = (
      <>
        <h1 className="page-title">{label}</h1>
        <LoadingState stage="Loading what we know" />
      </>
    );
  } else if (
    journey.progress[chapter] === "locked" &&
    chapter === "plan" &&
    planCandidate === null
  ) {
    body = <LoadingState stage="Checking your route choice" />;
  } else if (journey.progress[chapter] === "locked") {
    body = (
      <BlockedChapter chapter={chapter} journey={journey} workspaceId={workspace.workspace_id} />
    );
  } else if (chapter === "you") {
    body = <YouChapter workspace={workspace} profile={profile} />;
  } else {
    body =
      chapter === "skills" ? (
        <SkillsChapter workspaceId={workspace.workspace_id} />
      ) : chapter === "options" ? (
        <OptionsChapter workspaceId={workspace.workspace_id} />
      ) : chapter === "routes" ? (
        <RoutesChapter key={search} workspaceId={workspace.workspace_id} />
      ) : chapter === "plan" ? (
        <PlanChapter key={search} workspaceId={workspace.workspace_id} />
      ) : (
        <RolesChapter workspaceId={workspace.workspace_id} profile={profile} />
      );
  }
  const blocked = profile === undefined || journey.progress[chapter] === "locked";
  return (
    <div className="chapter-frame on-reading" data-covers-world data-world-panel>
      {blocked ? <section className="chapter-reading">{body}</section> : body}
    </div>
  );
}
