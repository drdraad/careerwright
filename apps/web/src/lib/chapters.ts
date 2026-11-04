// The six places in one workspace. Their availability follows saved decisions and inputs.

export const CHAPTERS = [
  { id: "you", label: "You" },
  { id: "roles", label: "Roles" },
  { id: "skills", label: "Skills" },
  { id: "options", label: "Options" },
  { id: "routes", label: "Routes" },
  { id: "plan", label: "Plan" },
] as const;

export type ChapterId = (typeof CHAPTERS)[number]["id"];

export type ChapterProgress = "complete" | "available" | "locked";

export function isChapter(value: string): value is ChapterId {
  return CHAPTERS.some((chapter) => chapter.id === value);
}

export function chapterHref(workspaceId: string, chapter: ChapterId): string {
  return `/w/${encodeURIComponent(workspaceId)}/${chapter}`;
}
