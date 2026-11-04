"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  getSkills,
  type PasteText,
  pasteText,
  type RecordEvidence,
  type RecordStatement,
  recordRequirementStatement,
  recordSkillEvidence,
  type SelectAdvertSpans,
  type SetQuestions,
  type SkillsOut,
  selectAdvertSpans,
  setCapabilityQuestions,
} from "@/generated/api";
import { ApiError, ChangeKeys } from "./api";
import { keys } from "./queries";

const path = (workspace_id: string) => ({ workspace_id });

export function useSkills(id: string, enabled = true) {
  return useQuery({
    queryKey: [...keys.scope(id), "skills"],
    queryFn: async (): Promise<SkillsOut> =>
      (await getSkills({ path: path(id), throwOnError: true })).data,
    retry: (failures, error) =>
      !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failures < 2,
    enabled,
  });
}

// Every capability write has the same expected-version and idempotency contract.
function useSkillCommand<Body>(id: string, send: (body: Body, key: string) => Promise<unknown>) {
  const queries = useQueryClient();
  const [changes] = useState(() => new ChangeKeys());
  return useMutation({
    mutationFn: (body: Body) => send(body, changes.keyFor(body)),
    onSuccess: () => {
      changes.settled();
      return queries.invalidateQueries({ queryKey: keys.scope(id) });
    },
  });
}

export const useRecordSkill = (id: string) =>
  useSkillCommand(
    id,
    async (body: RecordEvidence, key) =>
      (
        await recordSkillEvidence({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data,
  );

export const useRecordRequirement = (id: string) =>
  useSkillCommand(
    id,
    async (body: RecordStatement, key) =>
      (
        await recordRequirementStatement({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data,
  );

export const useChooseAdvertParts = (id: string) =>
  useSkillCommand(
    id,
    async (body: SelectAdvertSpans, key) =>
      (
        await selectAdvertSpans({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data,
  );

export const usePasteExample = (id: string) =>
  useSkillCommand(
    id,
    async (body: PasteText, key) =>
      (
        await pasteText({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data,
  );

export const useSetSkillQuestions = (id: string) =>
  useSkillCommand(
    id,
    async (body: SetQuestions, key) =>
      (
        await setCapabilityQuestions({
          path: path(id),
          body,
          headers: { "Idempotency-Key": key },
          throwOnError: true,
        })
      ).data,
  );
