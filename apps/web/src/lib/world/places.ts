// The six chapters are places in one world (plan section 4): moving between them is travel,
// the world stays and the view moves. These are the words each place uses for itself.
import type { ChapterId } from "@/lib/chapters";

export type Place = {
  /** Where the chapter is in the world, in a few plain words. */
  readonly where: string;
};

export const PLACES: Record<ChapterId, Place> = {
  you: { where: "Your light, where every journey starts." },
  roles: { where: "The horizon: places you could head for." },
  skills: { where: "The ground between you and a destination." },
  options: { where: "Bridges across the dark stretches: courses, work routes and funding." },
  routes: { where: "Whole journeys from you to a destination, compared on time and cost." },
  plan: { where: "The path you choose, made solid, with your next move glowing at its start." },
};
