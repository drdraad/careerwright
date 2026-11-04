"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getOccupation,
  getOccupationEvidence,
  type JobPage,
  listJobs,
  type OccupationEvidenceOut,
  type OccupationOut,
} from "@/generated/api";

export function useOccupation(conceptId: string | null) {
  return useQuery({
    queryKey: ["occupation", conceptId],
    queryFn: async (): Promise<OccupationOut> => {
      if (conceptId === null) throw new Error("An occupation must be selected.");
      return (await getOccupation({ path: { concept_id: conceptId }, throwOnError: true })).data;
    },
    enabled: conceptId !== null,
  });
}

export function useOccupationEvidence(workspaceId: string, conceptId: string | null) {
  return useQuery({
    queryKey: ["ws", workspaceId, "occupation-evidence", conceptId],
    queryFn: async (): Promise<OccupationEvidenceOut> => {
      if (conceptId === null) throw new Error("An occupation must be selected.");
      return (
        await getOccupationEvidence({
          path: { workspace_id: workspaceId, concept_id: conceptId },
          throwOnError: true,
        })
      ).data;
    },
    enabled: conceptId !== null,
  });
}

/** The first 100 stored adverts. The API reports the full count and whether more remain. */
export function useRoleJobs(workspaceId: string) {
  return useQuery({
    queryKey: ["ws", workspaceId, "jobs", "roles"],
    queryFn: async (): Promise<JobPage> =>
      (
        await listJobs({
          path: { workspace_id: workspaceId },
          query: { limit: 100 },
          throwOnError: true,
        })
      ).data,
  });
}
