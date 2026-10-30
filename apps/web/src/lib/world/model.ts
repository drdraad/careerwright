// What the world shows, from what the API computed: nothing here guesses. The person's light is
// lit once they have given any answer; the destinations are the targets they chose themselves,
// in title order (position is layout only, never rank). Skills and openings arrive with the
// chapters that compute them (the You chapter's first moments, Roles); until then the world
// draws none, and the ground between the person and each destination stays in shadow.
import type { ProfileOut } from "@/generated/api";
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

export function worldFromProfile(profile: ProfileOut | undefined): WorldInput {
  if (profile === undefined) return EMPTY_WORLD;
  const targets = profile.document.target_titles;
  const titles =
    targets.state === "provided" && Array.isArray(targets.value)
      ? [...new Set(targets.value.map((title) => title.trim()).filter(Boolean))].sort(byTitle)
      : [];
  return {
    lit: hasAnswered(profile),
    destinations: titles.map((title) => ({ id: `target:${title}`, title, shared: [] })),
    skills: [],
    openings: 0,
  };
}
