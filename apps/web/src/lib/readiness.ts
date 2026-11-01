// Which answers a planned chapter uses, and what their states mean for it (spec section 3:
// "shows which downstream results depend on missing facts"). Unknown, Skipped and Prefer not
// to say are answers: they make a result less precise and never block a chapter. Only an
// answer that was never asked, where the chapter cannot start without one, asks the person
// to answer first.
import type { ProfileDocument } from "@/generated/api";
import type { ChapterId } from "./chapters";
import type { ProfileFieldName } from "./vocabulary";

type Needs = {
  /** The chapter starts from these (a target, a work area). */
  start: ProfileFieldName[];
  /** These refine it; without them the result is less precise. */
  refine: ProfileFieldName[];
};

export const CHAPTER_NEEDS: Record<Exclude<ChapterId, "you" | "routes">, Needs> = {
  roles: { start: ["target_titles", "cities"], refine: [] },
  skills: { start: ["target_titles"], refine: ["current_role"] },
  options: {
    start: ["target_titles"],
    refine: ["weekly_study_hours", "direct_spend_cap", "monthly_payment_cap"],
  },
  plan: { start: [], refine: [] },
};

export type ChapterNeeds = {
  /** Every answer the chapter uses, in order. */
  uses: ProfileFieldName[];
  /** Starting answers never asked: the chapter needs them first. */
  notAsked: ProfileFieldName[];
  /** Starting answers given as Unknown, Skipped or Prefer not to say: nothing to start from. */
  withoutStart: ProfileFieldName[];
  /** Refining answers not given (any state but answered): the result is less precise. */
  lessPrecise: ProfileFieldName[];
};

export function chapterNeeds(
  chapter: keyof typeof CHAPTER_NEEDS,
  document: ProfileDocument,
): ChapterNeeds {
  const { start, refine } = CHAPTER_NEEDS[chapter];
  return {
    uses: [...start, ...refine],
    notAsked: start.filter((name) => document[name].state === "unasked"),
    withoutStart: start.filter(
      (name) => document[name].state !== "unasked" && document[name].state !== "provided",
    ),
    lessPrecise: refine.filter((name) => document[name].state !== "provided"),
  };
}
