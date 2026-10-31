// What the world shows, from what the API computed: nothing here guesses. The person's light is
// lit once they have given any answer; the destinations are the targets they chose themselves,
// each as it is stored once (its record's key is its identity, so two spellings of one title are
// one destination; Task 6d slice A), in title order (position is layout only, never rank).
// Skills and openings arrive with the chapters that compute them (the You chapter's first
// moments, Roles); until then the world draws none, and the ground between the person and each
// destination stays in shadow.
import type { ProfileOut, TargetRecordOut } from "@/generated/api";
import { PROFILE_FIELD_ORDER } from "@/lib/vocabulary";

export type WorldSkill = {
  readonly id: string;
  readonly label: string;
  readonly state: "usual" | "said";
};

export type WorldDestination = {
  readonly id: string;
  readonly title: string;
  /** Ids of the person's skills this destination also needs (computed elsewhere, never guessed). */
  readonly shared: readonly string[];
};

export type WorldInput = {
  /** The person has given a first answer: their light is lit. */
  readonly lit: boolean;
  /** Places the person chose to head for, in title order. */
  readonly destinations: readonly WorldDestination[];
  /** Skills around the person, each usual in their role or said by them. */
  readonly skills: readonly WorldSkill[];
  /** Openings drawn around the destinations. */
  readonly openings: number;
};

export const EMPTY_WORLD: WorldInput = { lit: false, destinations: [], skills: [], openings: 0 };

const byTitle = (a: string, b: string): number => a.localeCompare(b, "en-GB");

/** Answered, Unknown, Skipped and Prefer not to say are all answers; only "Not asked yet" is not. */
function hasAnswered(profile: ProfileOut): boolean {
  return PROFILE_FIELD_ORDER.some((name) => profile.document[name].state !== "unasked");
}

/** `targets`: the stored records of the profile's targets (`GET .../targets`); none drawn
 *  until they are loaded. */
export function worldFromProfile(
  profile: ProfileOut | undefined,
  targets: readonly TargetRecordOut[] = [],
): WorldInput {
  if (profile === undefined) return EMPTY_WORLD;
  const destinations = [...targets]
    .sort((a, b) => byTitle(a.title, b.title))
    .map((target) => ({ id: `target:${target.key}`, title: target.title, shared: [] }));
  return { lit: hasAnswered(profile), destinations, skills: [], openings: 0 };
}
