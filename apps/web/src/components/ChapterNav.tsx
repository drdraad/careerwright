"use client";
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

const COMPLETED: Record<ChapterId, string> = {
  you: "Direction chosen",
  roles: "Role reviewed",
  skills: "Questions answered",
  options: "Ready for routes",
  routes: "Route found",
  plan: "Plan saved",
};

function ChapterItem({
  id,
  label,
  workspaceId,
  current,
  progress,
  menu = false,
  onChoose,
}: {
  id: ChapterId;
  label: string;
  workspaceId: string;
  current: ChapterId;
  progress: ChapterProgress;
  menu?: boolean;
  onChoose?(): void;
}) {
  const className = menu ? "menu-chapter" : "rail-chapter";
  const words =
    progress === "complete" ? COMPLETED[id] : progress === "locked" ? "Locked" : "Available";
  const content = (
    <>
      <span className="landmark" aria-hidden="true" />
      {label} <span className="chapter-later">{words}</span>
    </>
  );
  if (progress === "locked" && id !== current)
    return (
      <span className={className} data-progress="locked" aria-disabled="true">
        {content}
      </span>
    );
  return (
    <Link
      className={className}
      href={chapterHref(workspaceId, id)}
      data-progress={progress}
      aria-label={`${label}, ${words.toLowerCase()}`}
      aria-current={id === current ? "page" : undefined}
      onClick={onChoose}
    >
      {content}
    </Link>
  );
}

export function ChapterRail({ workspaceId, current, progress }: Props) {
  return (
    <div className="rail" data-covers-world>
      <Link className="rail-mark" href="/">
        <span className="sr-only">Careerwright: your workspaces</span>
        <Glyph name="mark" />
        <span aria-hidden="true">Careerwright</span>
      </Link>
      <nav aria-label="Chapters">
        <ul className="rail-chapters">
          {CHAPTERS.map(({ id, label }) => (
            <li key={id}>
              <ChapterItem
                id={id}
                label={label}
                workspaceId={workspaceId}
                current={current}
                progress={progress[id] ?? "available"}
              />
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
      <Popover.Portal>
        <Popover.Content className="popover on-space" align="start" sideOffset={8}>
          <nav aria-label="Chapters">
            <ul>
              {CHAPTERS.map(({ id, label: itemLabel }) => (
                <li key={id}>
                  <ChapterItem
                    id={id}
                    label={itemLabel}
                    workspaceId={workspaceId}
                    current={current}
                    progress={progress[id] ?? "available"}
                    menu
                    onChoose={() => setOpen(false)}
                  />
                </li>
              ))}
            </ul>
          </nav>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
