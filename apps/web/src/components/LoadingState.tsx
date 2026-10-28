import { Glyph } from "./Glyph";

type Props = {
  /** The actual stage in words ("Loading your profile"); never an invented percentage. */
  stage: string;
  lines?: number;
};

export function LoadingState({ stage, lines = 3 }: Props) {
  return (
    <div className="grid gap-12" role="status" aria-busy="true">
      <span className="status">
        <Glyph name="running" />
        <span>{stage}</span>
      </span>
      <div className="grid gap-8" aria-hidden="true">
        {Array.from({ length: lines }, (_, index) => (
          <span key={String(index)} className="skeleton" style={{ width: `${88 - index * 18}%` }} />
        ))}
      </div>
    </div>
  );
}
