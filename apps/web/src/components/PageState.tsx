// Whole-page states before a workspace can show: loading, refused, missing or unreachable.
// Each says what happened and what to do next; none is a blank page.
import type { ReactNode } from "react";
import { ApiError } from "@/lib/api";
import { ERROR_STATEMENT } from "@/lib/vocabulary";
import { Alert } from "./Alert";
import { LoadingState } from "./LoadingState";

export function PageFrame({ children }: { children: ReactNode }) {
  return (
    <main id="main" className="on-reading grid min-h-dvh place-items-center bg-reading p-16">
      <div className="card grid w-full max-w-[560px] gap-16">{children}</div>
    </main>
  );
}

export function PageLoading({ stage }: { stage: string }) {
  return (
    <PageFrame>
      <LoadingState stage={stage} />
    </PageFrame>
  );
}

/**
 * A refused request in the person's words and its state's tone: the code's statement, never
 * the raw message. Only real failures are red and announced as alerts.
 */
export function RequestFailure({ error, actions }: { error: unknown; actions?: ReactNode }) {
  if (error instanceof ApiError && error.body !== null) {
    const statement = ERROR_STATEMENT[error.body.code];
    return (
      <Alert tone={statement.tone} title={statement.title} actions={actions}>
        <p>{statement.action}</p>
        <p className="muted">Reference {error.body.correlation_id}</p>
      </Alert>
    );
  }
  return (
    <Alert
      tone="error"
      glyph="unavailable"
      title="Nessa's service isn't reachable"
      actions={actions}
    >
      <p>Nothing you saved is lost. If Nessa is restarting, try again in a moment.</p>
    </Alert>
  );
}
