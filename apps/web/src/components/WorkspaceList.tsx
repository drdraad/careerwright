"use client";
// The signed-in home: the person's workspaces, and a new one when they have none. A demo
// workspace is always synthetic (the API enforces it too); a synthetic one is labelled for good.
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useId, useState } from "react";
import type { DataMode } from "@/generated/api";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { chapterHref } from "@/lib/chapters";
import { useCreateWorkspace, useMe, useWorkspaces } from "@/lib/queries";
import { DATA_MODE } from "@/lib/vocabulary";
import { Button } from "./Button";
import { EmptyState } from "./EmptyState";
import { LoadingState } from "./LoadingState";
import { NotInvited, RequestFailure } from "./PageState";
import { SyntheticLabel } from "./Status";

const updated = new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" });

/** What each mode means, beside the select (V-05): a native option label cannot wrap. */
const MODE_HINT: Record<Extract<DataMode, "demo" | "live_assisted">, string> = {
  demo: "Synthetic data only. Nothing leaves this computer.",
  live_assisted:
    "Uses your Meta API key for the interview and suggestions, so what you write is sent to Meta's model.",
};

export function CreateWorkspace({ onCreated }: { onCreated(id: string): void }) {
  const create = useCreateWorkspace();
  const [name, setName] = useState("");
  const [mode, setMode] = useState<Extract<DataMode, "demo" | "live_assisted">>("demo");
  const [synthetic, setSynthetic] = useState(true);
  const id = useId();
  return (
    <form
      className="grid gap-12"
      onSubmit={(event) => {
        event.preventDefault();
        create.mutate(
          { name: name.trim(), data_mode: mode, synthetic: mode === "demo" ? true : synthetic },
          { onSuccess: (workspace) => onCreated(workspace.workspace_id) },
        );
      }}
    >
      <h2 className="section-title">New workspace</h2>
      <div className="grid gap-4">
        <label htmlFor={`${id}-name`} className="field-label">
          Name
        </label>
        <input
          id={`${id}-name`}
          className="input"
          value={name}
          maxLength={120}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
      <div className="grid gap-4">
        <label htmlFor={`${id}-mode`} className="field-label">
          Data mode
        </label>
        <select
          id={`${id}-mode`}
          className="select"
          value={mode}
          aria-describedby={`${id}-mode-hint`}
          onChange={(e) => setMode(e.target.value as typeof mode)}
        >
          <option value="demo">{DATA_MODE.demo}</option>
          <option value="live_assisted">{DATA_MODE.live_assisted}</option>
        </select>
        <p id={`${id}-mode-hint`} className="field-hint">
          {MODE_HINT[mode]}
        </p>
      </div>
      {mode === "live_assisted" && (
        <label className="flex items-center gap-8 small">
          <input
            type="checkbox"
            checked={synthetic}
            onChange={(e) => setSynthetic(e.target.checked)}
          />
          This workspace holds synthetic test data only (it stays labelled synthetic for good)
        </label>
      )}
      {create.error !== null && <RequestFailure error={create.error} />}
      <div>
        <Button
          type="submit"
          variant="primary"
          disabledReason={
            create.isPending ? "Creating…" : name.trim() === "" ? "Enter a name first." : undefined
          }
        >
          Create workspace
        </Button>
      </div>
    </form>
  );
}

export function WorkspaceList() {
  const auth = useAuth();
  const router = useRouter();
  const signedIn = auth.state.status === "signed_in";
  const me = useMe(signedIn);
  const workspaces = useWorkspaces(signedIn && me.isSuccess);

  useEffect(() => {
    if (auth.state.status === "signed_out") router.replace("/sign-in");
  }, [auth.state.status, router]);

  if (!signedIn || me.isPending) return <LoadingState stage="Checking your sign-in" />;
  if (me.isError) {
    const signOut = (
      <button type="button" className="btn btn-secondary" onClick={() => void auth.signOut()}>
        Sign out
      </button>
    );
    if (me.error instanceof ApiError && me.error.code === "NOT_INVITED") {
      return <NotInvited error={me.error} actions={signOut} />;
    }
    return (
      <>
        <h1 className="page-title">Careerwright can't load your account</h1>
        <RequestFailure error={me.error} actions={signOut} />
      </>
    );
  }
  const open = (id: string) => router.push(chapterHref(id, "you"));
  return (
    <>
      <div className="flex flex-wrap items-baseline justify-between gap-12">
        <h1 className="page-title">Your workspaces</h1>
        <button type="button" className="btn btn-quiet" onClick={() => void auth.signOut()}>
          Sign out {me.data.email}
        </button>
      </div>
      {workspaces.isPending && <LoadingState stage="Loading your workspaces" />}
      {workspaces.isError && <RequestFailure error={workspaces.error} />}
      {workspaces.data !== undefined &&
        (workspaces.data.length === 0 ? (
          <EmptyState state="notStarted" title="No workspaces yet">
            <p>
              A workspace holds one person's answers, research and plans. Create one below to start.
            </p>
          </EmptyState>
        ) : (
          <ul className="grid gap-12">
            {workspaces.data.map((workspace) => (
              <li key={workspace.workspace_id}>
                <Link
                  className="card grid gap-4 no-underline"
                  href={chapterHref(workspace.workspace_id, "you")}
                >
                  <span className="font-semibold">{workspace.name}</span>
                  <span className="flex flex-wrap items-center gap-8 small text-fg-muted">
                    {workspace.synthetic && <SyntheticLabel />}
                    {DATA_MODE[workspace.data_mode]}, updated{" "}
                    {updated.format(new Date(workspace.updated_at))}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ))}
      <CreateWorkspace onCreated={open} />
    </>
  );
}
