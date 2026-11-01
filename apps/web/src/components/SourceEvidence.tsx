// Drawer content for one profile answer: the source reference the server assigned to it.
// A fixture source says so in words and with the synthetic label; it is never real evidence.
import type { SourceOut } from "@/generated/api";
import { Alert } from "./Alert";
import { LoadingState } from "./LoadingState";
import { StatusBadge, SyntheticLabel } from "./Status";

const dateTime = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "long",
  timeStyle: "short",
  timeZone: "UTC",
});

type Props = {
  fieldLabel: string;
  value: string;
  lessPrecise: string;
  source: SourceOut | undefined;
  loading: boolean;
  failed: boolean;
};

export function SourceEvidence({ fieldLabel, value, lessPrecise, source, loading, failed }: Props) {
  return (
    <>
      <p className="section-title">
        {fieldLabel}: {value}
      </p>
      {loading && <LoadingState stage="Loading the source record" lines={2} />}
      {failed && (
        <Alert tone="error" title="The source record couldn't be loaded">
          The answer itself is saved. Try opening this again in a moment.
        </Alert>
      )}
      {!loading && !failed && source === undefined && (
        <StatusBadge state="unknown" detail="no source record was found for this answer" />
      )}
      {source !== undefined && (
        <>
          {source.kind === "fixture" ? (
            <div className="grid gap-8">
              <SyntheticLabel text="Synthetic fixture" />
              <p className="small">
                From the supplied fixture pack, pinned by its SHA-256. It is test data, not evidence
                about you or anyone else.
              </p>
            </div>
          ) : (
            <p className="small">
              You entered this directly. It has not been checked against a document.
            </p>
          )}
          <dl className="kv">
            <dt>Source</dt>
            <dd>{source.label}</dd>
            {source.locator !== null && (
              <>
                <dt>File</dt>
                <dd>{source.locator}</dd>
              </>
            )}
            {source.content_sha256 !== null && (
              <>
                <dt>SHA-256</dt>
                <dd className="text-12">{source.content_sha256}</dd>
              </>
            )}
            <dt>Observed</dt>
            <dd>{dateTime.format(new Date(source.observed_at))} UTC</dd>
          </dl>
        </>
      )}
      <div className="grid gap-4">
        <p className="section-title">If it were missing</p>
        <p className="small">{lessPrecise}</p>
      </div>
    </>
  );
}
