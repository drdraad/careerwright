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
export function RequestFailure({
  error,
  actions,
  announce,
}: {
  error: unknown;
  actions?: ReactNode;
  /** False when another notice already announces this failure (one announcement each). */
  announce?: boolean;
}) {
  if (error instanceof ApiError && error.body !== null) {
    const statement = ERROR_STATEMENT[error.body.code];
    return (
      <Alert tone={statement.tone} title={statement.title} actions={actions} announce={announce}>
        <p>{statement.action}</p>
        <p className="muted">Reference {error.body.correlation_id}</p>
      </Alert>
    );
  }
  return (
    <Alert
      tone="error"
      glyph="unavailable"
      title="Careerwright's service isn't reachable"
      actions={actions}
      announce={announce}
    >
      <p>Nothing you saved is lost. If Careerwright is restarting, try again in a moment.</p>
    </Alert>
  );
}

/**
 * The refused-account page (NOT_INVITED, V-10): the cause is the page's one headline, and the
 * notice under it holds only the recovery and the reference, so the cause is not said twice.
 */
export function NotInvited({ error, actions }: { error: ApiError; actions: ReactNode }) {
  const statement = ERROR_STATEMENT.NOT_INVITED;
  return (
    <>
      <h1 className="page-title">{statement.title}</h1>
      <Alert tone={statement.tone} actions={actions}>
        <p>{statement.action}</p>
        {error.body !== null && <p className="muted">Reference {error.body.correlation_id}</p>}
      </Alert>
    </>
  );
}
