// The status vocabulary in the UI: glyph first, then words; only error and stale add a hue.
import type { WorkState } from "@/generated/api";
import { DISPLAY_STATE, type StatePresentation, WORK_STATE } from "@/lib/vocabulary";
import { Glyph } from "./Glyph";

type DisplayState = keyof typeof DISPLAY_STATE;

type Props = {
  state: WorkState | DisplayState;
  /** Words that make the state specific: what is unknown, the condition, the age, the cause. */
  detail?: string;
};

function presentation(state: WorkState | DisplayState): StatePresentation {
  return state in DISPLAY_STATE
    ? DISPLAY_STATE[state as DisplayState]
    : WORK_STATE[state as WorkState];
}

export function StatusBadge({ state, detail }: Props) {
  const { label, glyph, tone } = presentation(state);
  return (
    <span className="status" data-tone={tone} data-state={state}>
      <Glyph name={glyph} />
      <span>
        {label}
        {detail !== undefined && <span className="font-normal">: {detail}</span>}
      </span>
    </span>
  );
}

/** The persistent synthetic-data label (Global Constraint 5): solid pill, flask glyph. */
export function SyntheticLabel({ text = "Synthetic demo" }: { text?: string }) {
  return (
    <span className="synthetic-label">
      <Glyph name="synthetic" />
      {text}
    </span>
  );
}
