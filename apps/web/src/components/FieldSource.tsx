"use client";
// The evidence drawer's body for one profile answer. It reads the profile and its source
// references live (the drawer stores only which answer it shows), so it moves from loading to
// the record when they arrive, and after a save it looks again before it ever says that an
// answer has no source record.
import { useEffect, useState } from "react";
import type { ProfileDocument } from "@/generated/api";
import { describeField } from "@/lib/profile";
import { useProfile, useSources } from "@/lib/queries";
import { PROFILE_FIELDS, type ProfileFieldName } from "@/lib/vocabulary";
import { SourceEvidence } from "./SourceEvidence";

type Props = {
  workspaceId: string;
  name: ProfileFieldName;
  /** The answer as the editor had it when the drawer opened; the saved profile wins once loaded. */
  shown: ProfileDocument[ProfileFieldName];
};

export function FieldSource({ workspaceId, name, shown }: Props) {
  const profile = useProfile(workspaceId);
  const sources = useSources(workspaceId);
  const field = profile.data?.document[name] ?? shown;
  const wanted = field.source_ref_id ?? null;
  const source = sources.data?.find((item) => item.source_ref_id === wanted);
  // An answer saved a moment ago may cite a source the loaded list predates: look once more.
  const [lookedAgainFor, setLookedAgainFor] = useState<string | null>(null);
  const notInList = sources.isSuccess && wanted !== null && source === undefined;
  const refetch = sources.refetch;
  useEffect(() => {
    if (notInList && wanted !== null && lookedAgainFor !== wanted) {
      setLookedAgainFor(wanted);
      void refetch();
    }
  }, [notInList, wanted, lookedAgainFor, refetch]);
  const settled = !notInList || (lookedAgainFor === wanted && !sources.isFetching);

  return (
    <SourceEvidence
      fieldLabel={PROFILE_FIELDS[name].label}
      value={describeField(field, name)}
      lessPrecise={PROFILE_FIELDS[name].lessPrecise}
      source={source}
      loading={sources.isPending || !settled}
      failed={sources.isError && source === undefined}
    />
  );
}
