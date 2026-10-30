// The six persistent chapters (spec section 3). They are navigable states, not a wizard, so
// none is numbered and none is locked. Each is a place in the one world (plan section 4).

export const CHAPTERS = [
  { id: "you", label: "You" },
  { id: "roles", label: "Roles" },
  { id: "skills", label: "Skills" },
  { id: "options", label: "Options" },
  { id: "routes", label: "Routes" },
  { id: "plan", label: "Plan" },
] as const;

export type ChapterId = (typeof CHAPTERS)[number]["id"];

/**
 * How the rail marks a chapter besides "current" (docs/design/README.md: visited, current or
 * not started). Visited means opened in this browser session, or You once answers are saved;
 * it is drawn as a ring, never as the filled mark of a completed chapter (V-09).
 */
export type ChapterProgress = "visited" | "todo";

export function isChapter(value: string): value is ChapterId {
  return CHAPTERS.some((chapter) => chapter.id === value);
}

export function chapterHref(workspaceId: string, chapter: ChapterId): string {
  return `/w/${encodeURIComponent(workspaceId)}/${chapter}`;
}
