"use client";
// Chapter navigation: the slim rail on desktop and tablet, a chapter menu on phones. Both are
// lists of links in a labelled `nav`, so every chapter is a Tab stop and the current one is
// `aria-current="page"`.
import * as Popover from "@radix-ui/react-popover";
import Link from "next/link";
import { useState } from "react";
import { CHAPTERS, type ChapterId, type ChapterProgress, chapterHref } from "@/lib/chapters";
import { Glyph } from "./Glyph";

type Props = {
  workspaceId: string;
  current: ChapterId;
  progress: Partial<Record<ChapterId, ChapterProgress>>;
};

/** The mark in words; the current chapter is announced by `aria-current` instead. */
function Mark({ progress, current }: { progress: ChapterProgress | undefined; current: boolean }) {
  if (current) return null;
  return <span className="sr-only">{progress === "visited" ? ", visited" : ", not started"}</span>;
}

export function ChapterRail({ workspaceId, current, progress }: Props) {
  return (
    <div className="rail">
      <Link className="rail-mark" href="/">
        <span className="sr-only">Careerwright: your workspaces</span>
        <Glyph name="mark" />
        <span aria-hidden="true">Careerwright</span>
      </Link>
      <nav aria-label="Chapters">
        <ul className="rail-chapters">
          {CHAPTERS.map((chapter) => (
            <li key={chapter.id}>
              <Link
                className="rail-chapter"
                href={chapterHref(workspaceId, chapter.id)}
                data-progress={progress[chapter.id] ?? "todo"}
                aria-current={chapter.id === current ? "page" : undefined}
              >
                <span className="landmark" aria-hidden="true" />
                {chapter.label}
                <Mark progress={progress[chapter.id]} current={chapter.id === current} />
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}

export function ChapterMenu({ workspaceId, current, progress }: Props) {
  const [open, setOpen] = useState(false);
  const label = CHAPTERS.find((chapter) => chapter.id === current)?.label ?? "";
  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger className="chapter-menu-button">
        <Glyph name="menu" />
        <span>{label}</span>
        <span className="sr-only">, open chapter menu</span>
      </Popover.Trigger>
      <Popover.Content className="popover on-space" align="start" sideOffset={8}>
        <nav aria-label="Chapters">
          <ul>
            {CHAPTERS.map((chapter) => (
              <li key={chapter.id}>
                <Link
                  className="menu-chapter"
                  href={chapterHref(workspaceId, chapter.id)}
                  data-progress={progress[chapter.id] ?? "todo"}
                  aria-current={chapter.id === current ? "page" : undefined}
                  onClick={() => setOpen(false)}
                >
                  <span className="landmark" aria-hidden="true" />
                  {chapter.label}
                  <Mark progress={progress[chapter.id]} current={chapter.id === current} />
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </Popover.Content>
    </Popover.Root>
  );
}
