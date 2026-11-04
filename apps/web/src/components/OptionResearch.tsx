"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import {
  useOptionResearchEstimate,
  useOptionResearchList,
  useReadOptionPages,
  useStartOptionResearch,
} from "@/lib/optionResearchQueries";
import { useCancelRun, useCredentials, useProfile } from "@/lib/queries";
import { OptionResearchView } from "./OptionResearchView";
import { RequestFailure } from "./PageState";

export function OptionResearch({ workspaceId, target }: { workspaceId: string; target: string }) {
  const queries = useQueryClient();
  const profile = useProfile(workspaceId);
  const credentials = useCredentials(workspaceId);
  const estimate = useOptionResearchEstimate(workspaceId, true);
  const researches = useOptionResearchList(workspaceId, true);
  const start = useStartOptionResearch(workspaceId);
  const read = useReadOptionPages(workspaceId);
  const cancel = useCancelRun(workspaceId);
  const [chosenCity, setChosenCity] = useState("");
  const askedToRead = useRef(new Set<string>());
  const refreshed = useRef<string | null>(null);
  const cities =
    profile.data?.document.cities.state === "provided"
      ? (profile.data.document.cities.value ?? [])
      : [];
  const city = cities.includes(chosenCity) ? chosenCity : (cities[0] ?? "");
  const research =
    researches.data?.find((item) => item.target === target && item.city === city) ?? null;

  // One search choice starts one bounded reading automatically; a failed start can be retried
  // with the same idempotency key from the visible recovery action.
  useEffect(() => {
    if (research?.status === "ready_to_read" && !askedToRead.current.has(research.research_id)) {
      askedToRead.current.add(research.research_id);
      read.mutate(research.research_id);
    }
  }, [research?.status, research?.research_id, read]);
  useEffect(() => {
    if (
      (research?.status === "completed" || research?.status === "reading_stopped") &&
      refreshed.current !== research.research_id
    ) {
      refreshed.current = research.research_id;
      void queries.invalidateQueries({ queryKey: ["ws", workspaceId, "planning"] });
    }
  }, [research?.status, research?.research_id, queries, workspaceId]);

  return (
    <>
      {profile.error != null && <RequestFailure error={profile.error} />}
      {credentials.error != null && <RequestFailure error={credentials.error} />}
      <OptionResearchView
        target={target}
        cities={cities}
        city={city}
        onCity={setChosenCity}
        keyReady={credentials.data !== undefined}
        canWrite={credentials.data?.some((item) => item.active) ?? false}
        estimate={estimate.data ?? null}
        estimateLoading={estimate.isPending}
        estimateError={estimate.error}
        research={research}
        researchLoading={researches.isPending}
        researchError={researches.error}
        starting={start.isPending}
        reading={read.isPending}
        cancelling={cancel.isPending}
        startError={start.error}
        readError={read.error}
        cancelError={cancel.error}
        onStart={() => {
          if (profile.data && city)
            start.mutate({ expected_profile_version: profile.data.version, target, city });
        }}
        onRead={() => {
          if (research) read.mutate(research.research_id);
        }}
        onCancel={(runId) => cancel.mutate(runId)}
      />
    </>
  );
}
