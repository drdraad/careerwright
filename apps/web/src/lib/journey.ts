import type { CheckpointOut, ProfileOut, SkillsOut } from "@/generated/api";
import type { ChapterId, ChapterProgress } from "./chapters";

export type Journey = {
  progress: Record<ChapterId, ChapterProgress>;
};

export function journeyOf({
  profile,
  skills,
  checkpoint,
  routeFound,
  planSaved,
  planCandidate,
}: {
  profile: ProfileOut | undefined;
  skills: SkillsOut | undefined;
  checkpoint: CheckpointOut | undefined;
  routeFound: boolean;
  planSaved: boolean;
  planCandidate: boolean;
}): Journey {
  const target =
    profile?.document.target_titles.state === "provided" &&
    (profile.document.target_titles.value?.length ?? 0) > 0;
  const skillsAnswered =
    skills?.questions.state === "enough" &&
    skills.targets.length > 0 &&
    skills.targets.every(
      (item) =>
        item.readiness !== null &&
        item.readiness.state !== "insufficient_coverage" &&
        item.readiness.state !== "not_yet_assessed" &&
        !item.readiness.rows.some((row) =>
          ["unresolved", "no_usable_evidence", "not_modelled"].includes(row.status),
        ),
    );
  const routeReady =
    target &&
    checkpoint !== undefined &&
    checkpoint.targets.length > 0 &&
    !checkpoint.needs.some((need) => need.effect === "blocks_a_solve");
  const optionsSettled = routeReady && checkpoint.needs.length === 0;
  const progress: Record<ChapterId, ChapterProgress> = {
    you: target ? "complete" : "available",
    roles: target ? "available" : "locked",
    skills: !target ? "locked" : skillsAnswered ? "complete" : "available",
    options: !target ? "locked" : optionsSettled ? "complete" : "available",
    routes: !target ? "locked" : routeFound ? "complete" : routeReady ? "available" : "locked",
    plan: planSaved ? "complete" : planCandidate ? "available" : "locked",
  };
  return { progress };
}
