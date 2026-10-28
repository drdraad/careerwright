// The six persistent chapters (spec section 3). They are navigable states, not a wizard, so
// none is numbered and none is locked.

export const CHAPTERS = [
  { id: "you", label: "You", surface: "reading" },
  { id: "roles", label: "Roles", surface: "space" },
  { id: "skills", label: "Skills", surface: "reading" },
  { id: "options", label: "Options", surface: "reading" },
  { id: "routes", label: "Routes", surface: "space" },
  { id: "plan", label: "Plan", surface: "reading" },
] as const;

export type ChapterId = (typeof CHAPTERS)[number]["id"];

/** "done": decisions are recorded for it. Derived from server state, never stored separately. */
export type ChapterProgress = "done" | "todo";

export function isChapter(value: string): value is ChapterId {
  return CHAPTERS.some((chapter) => chapter.id === value);
}

export function chapterHref(workspaceId: string, chapter: ChapterId): string {
  return `/w/${encodeURIComponent(workspaceId)}/${chapter}`;
}
