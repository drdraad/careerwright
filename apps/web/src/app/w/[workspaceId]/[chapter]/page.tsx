import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ChapterView } from "@/components/ChapterView";
import { CHAPTERS, isChapter } from "@/lib/chapters";

type Params = { params: Promise<{ workspaceId: string; chapter: string }> };

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { chapter } = await params;
  const label = CHAPTERS.find((item) => item.id === chapter)?.label;
  return { title: label === undefined ? "Careerwright" : `${label} · Careerwright` };
}

export default async function ChapterPage({ params }: Params) {
  const { chapter } = await params;
  if (!isChapter(chapter)) notFound();
  return <ChapterView chapter={chapter} />;
}
