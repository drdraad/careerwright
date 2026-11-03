"use client";
// "Research this role" (Task 6e, S2.9; ADR 0015 decision 2): for a title no list holds, the
// person's own words or a title Careerwright thought of and hasn't found. One bounded search,
// told only the title and "England", then up to twenty of its pages read and checked by code.
// The API decides every state and count; this only words them (R11). Live workspaces only: a
// demo workspace never searches.
import { useEffect, useState } from "react";
import type { ProfileOut, RoleResearchOut } from "@/generated/api";
import { inputOf } from "@/lib/profile";
import {
  useCancelRun,
  useReadRolePages,
  useRoleResearch,
  useSaveProfile,
  useStartRoleResearch,
} from "@/lib/queries";
import { ROLE_RESEARCH, SEARCH_EMPTY_REASON } from "@/lib/vocabulary";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";
import { RunEstimate } from "./RunEstimate";

export type ResearchTitle = { title: string; why: keyof typeof ROLE_RESEARCH.why };

const readOn = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});
const same = (a: string, b: string) =>
  a.trim().replace(/\s+/g, " ").toLowerCase() === b.trim().replace(/\s+/g, " ").toLowerCase();
const RUNNING = new Set(["searching", "ready_to_read", "reading"]);

/** The latest research of a title, if any (the list is newest first). */
export function latestFor(
  researches: readonly RoleResearchOut[],
  title: string,
): RoleResearchOut | undefined {
  return researches.find((research) => same(research.title, title));
}

/** Every title no list holds that the person can research, one block each. */
export function RoleResearchList({
  workspaceId,
  profile,
  titles,
  canWrite,
}: {
  workspaceId: string;
  profile: ProfileOut;
  titles: readonly ResearchTitle[];
  /** Whether a run may start (a key is stored). */
  canWrite: boolean;
}) {
  const researches = useRoleResearch(workspaceId, titles.length > 0);
  if (titles.length === 0) return null;
  return (
    <section className="grid gap-12" aria-labelledby="role-research">
      <h3 id="role-research" className="section-title">
        {ROLE_RESEARCH.heading}
      </h3>
      <p className="small measure">
        {ROLE_RESEARCH.intro} {ROLE_RESEARCH.sends}
      </p>
      {researches.error !== null && <RequestFailure error={researches.error} />}
      {titles.map((item) => (
        <RoleResearch
          key={item.title}
          workspaceId={workspaceId}
          profile={profile}
          item={item}
          research={latestFor(researches.data ?? [], item.title)}
          canWrite={canWrite}
        />
      ))}
    </section>
  );
}

function RoleResearch({
  workspaceId,
  profile,
  item,
  research,
  canWrite,
}: {
  workspaceId: string;
  profile: ProfileOut;
  item: ResearchTitle;
  research: RoleResearchOut | undefined;
  canWrite: boolean;
}) {
  const start = useStartRoleResearch(workspaceId);
  const read = useReadRolePages(workspaceId);
  const cancel = useCancelRun(workspaceId);
  const state = research?.state;
  // The search is done and its pages aren't being read yet: read them, once per research (the
  // API answers a second request with the same reading).
  const [asked, setAsked] = useState<string | null>(null);
  const readable = research !== undefined && state === "ready_to_read";
  useEffect(() => {
    if (readable && research !== undefined && asked !== research.research_id) {
      setAsked(research.research_id);
      read.mutate(research.research_id);
    }
  }, [readable, research, asked, read]);

  const running = state !== undefined && RUNNING.has(state);
  const activeRun = running ? (research?.reading ?? research?.search) : undefined;
  const begin = () =>
    start.mutate({ expected_profile_version: profile.version, title: item.title });
  return (
    <article className="suggestion grid gap-8" aria-label={item.title}>
      <h4 className="font-semibold">{item.title}</h4>
      <p className="small muted">{ROLE_RESEARCH.why[item.why]}</p>
      {research === undefined ? (
        <div className="grid gap-8">
          <RunEstimate workspaceId={workspaceId} kind="source_search" />
          <div>
            <Button
              variant="secondary"
              onClick={begin}
              disabledReason={
                !canWrite ? ROLE_RESEARCH.noKey : start.isPending ? "Starting…" : undefined
              }
            >
              {ROLE_RESEARCH.start}
            </Button>
          </div>
        </div>
      ) : (
        <ResearchResult
          workspaceId={workspaceId}
          profile={profile}
          item={item}
          research={research}
        />
      )}
      {activeRun !== undefined && activeRun.cancel_requested_at === null && (
        <div>
          <Button variant="secondary" onClick={() => cancel.mutate(activeRun.run_id)}>
            {ROLE_RESEARCH.cancel}
          </Button>
        </div>
      )}
      {research !== undefined &&
        (state === "search_stopped" || state === "no_pages" || state === "reading_stopped") && (
          <div>
            <Button
              variant="secondary"
              onClick={begin}
              disabledReason={!canWrite ? ROLE_RESEARCH.noKey : undefined}
            >
              {ROLE_RESEARCH.again}
            </Button>
          </div>
        )}
      {[start.error, read.error, cancel.error].map(
        (error, n) => error !== null && <RequestFailure key={String(n)} error={error} />,
      )}
    </article>
  );
}

function ResearchResult({
  workspaceId,
  profile,
  item,
  research,
}: {
  workspaceId: string;
  profile: ProfileOut;
  item: ResearchTitle;
  research: RoleResearchOut;
}) {
  const unread = research.pages.filter((page) => page.title_verified === null).length;
  const settled = research.state === "found" || research.state === "not_yet_found";
  return (
    <div className="grid gap-8" aria-live="polite">
      <p className="small">{ROLE_RESEARCH.state[research.state]}</p>
      {research.state === "found" && (
        <p className="small">{ROLE_RESEARCH.found(research.sources, research.official)}</p>
      )}
      {research.state === "not_yet_found" && research.not_yet_found_reason !== null && (
        <p className="small">{ROLE_RESEARCH.notYetFound[research.not_yet_found_reason]}</p>
      )}
      {research.state === "no_pages" && (
        <p className="small">
          {research.empty_reason !== null
            ? `${SEARCH_EMPTY_REASON[research.empty_reason].title}. `
            : ""}
          {ROLE_RESEARCH.noPagesDetail}
        </p>
      )}
      {settled && unread > 0 && <p className="small">{ROLE_RESEARCH.unread(unread)}</p>}
      {research.pages.length > 0 && (
        <details className="details">
          <summary>{ROLE_RESEARCH.pages}</summary>
          <ul className="plain-list small grid gap-8 mt-12">
            {research.pages.map((page) => (
              <li key={page.position}>
                {page.url !== null ? (
                  <a href={page.url} rel="noopener noreferrer nofollow" target="_blank">
                    {page.host ?? page.url}
                  </a>
                ) : (
                  page.host
                )}
                {": "}
                {page.title_verified === null
                  ? ROLE_RESEARCH.pageUnread
                  : page.title_verified
                    ? ROLE_RESEARCH.pageVerified
                    : ROLE_RESEARCH.pageNotVerified}
                {page.retrieved_at !== null &&
                  `. ${ROLE_RESEARCH.read(readOn.format(new Date(page.retrieved_at)))}.`}
                {page.quote !== null && <blockquote className="mt-4">“{page.quote}”</blockquote>}
              </li>
            ))}
          </ul>
          <p className="small muted mt-12">{ROLE_RESEARCH.checkedOnly}</p>
        </details>
      )}
      {research.state === "found" && item.why === "idea" && (
        <MakeTarget workspaceId={workspaceId} profile={profile} title={item.title} />
      )}
    </div>
  );
}

/** A title idea found in independent sources is the person's to choose: it becomes a target
 *  only by their click, through the profile's own write path. */
function MakeTarget({
  workspaceId,
  profile,
  title,
}: {
  workspaceId: string;
  profile: ProfileOut;
  title: string;
}) {
  const save = useSaveProfile(workspaceId);
  const held = profile.document.target_titles;
  const targets = held.state === "provided" && Array.isArray(held.value) ? held.value : [];
  if (targets.some((target) => same(target, title))) {
    return <p className="small">{ROLE_RESEARCH.targetSaved}</p>;
  }
  const choose = () => {
    const input = inputOf(profile.document);
    save.mutate({
      expectedVersion: profile.version,
      profile: {
        ...input,
        target_titles: { state: "provided", value: [...targets, title] },
      },
      idempotencyKey: crypto.randomUUID(),
    });
  };
  return (
    <div className="grid gap-8">
      <div>
        <Button
          variant="secondary"
          onClick={choose}
          disabledReason={save.isPending ? "Saving…" : undefined}
        >
          {ROLE_RESEARCH.makeTarget}
        </Button>
      </div>
      {save.error !== null && <RequestFailure error={save.error} />}
    </div>
  );
}
