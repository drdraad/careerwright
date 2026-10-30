import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ChapterView } from "@/components/ChapterView";
import { CHAPTERS, isChapter } from "@/lib/chapters";
import { webConfig } from "@/lib/config";
import { loadRoutePreview } from "@/lib/fixtures/load";

type Params = { params: Promise<{ workspaceId: string; chapter: string }> };

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { chapter } = await params;
  const label = CHAPTERS.find((item) => item.id === chapter)?.label;
  return { title: label === undefined ? "Careerwright" : `${label} · Careerwright` };
}

export default async function ChapterPage({ params }: Params) {
  const { chapter } = await params;
  if (!isChapter(chapter)) notFound();
  // The fixture adapter runs on the server (it reads the pinned pack); the shell shows its
  // result only in the named fixture workspace.
  const routePreview =
    chapter === "routes" ? await loadRoutePreview(webConfig().fixturesDir) : null;
  return <ChapterView chapter={chapter} routePreview={routePreview} />;
}
