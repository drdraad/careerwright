// The six chapters are places in one world (plan section 4): moving between them is travel,
// the world stays and the view moves. These are the words each place uses for itself.
import type { ChapterId } from "@/lib/chapters";

export type Place = {
  /** Where the chapter is in the world, in a few plain words. */
  readonly where: string;
  /** What will happen here once the chapter is built: its one moment. */
  readonly moment: string;
};

export const PLACES: Record<ChapterId, Place> = {
  you: {
    where: "Your light, where every journey starts.",
    moment: "Your first answer lights it, and the first trails grow from it.",
  },
  roles: {
    where: "The horizon: places you could head for.",
    moment:
      "A place you never named lights up, joined to your own work by the skills the two share.",
  },
  skills: {
    where: "The ground between you and a destination.",
    moment: "An answer lights a stretch of trail you didn't know you had already covered.",
  },
  options: {
    where: "Bridges across the dark stretches: courses, work routes and funding.",
    moment: "A gap gets its first bridge you could really cross.",
  },
  routes: {
    where: "Whole journeys from you to a destination, compared on time and cost.",
    moment:
      "The first complete, checked path burns through to somewhere you thought was out of reach.",
  },
  plan: {
    where: "The path you choose, made solid, with your next move glowing at its start.",
    moment:
      "Committing: the world settles around your path, and real progress leaves lasting marks.",
  },
};
