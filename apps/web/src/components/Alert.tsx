import type { ReactNode, Ref } from "react";
import type { Tone } from "@/lib/vocabulary";
import { Glyph, type GlyphName } from "./Glyph";

const GLYPH: Record<Tone, GlyphName> = {
  error: "error",
  stale: "stale",
  unknown: "unknown",
  neutral: "conditional",
};

type Props = {
  tone: Tone;
  title: string;
  children?: ReactNode;
  actions?: ReactNode;
  glyph?: GlyphName;
  /** Errors are announced as they appear; other notices are read in place. */
  announce?: boolean;
  /** A notice given a ref can take focus (tabIndex -1), for moving focus to it. */
  ref?: Ref<HTMLDivElement>;
};

/** Failure has a red edge and a cause, stale is sand with a clock, unknown a question mark. */
export function Alert({
  tone,
  title,
  children,
  actions,
  glyph,
  announce = tone === "error",
  ref,
}: Props) {
  return (
    <div
      ref={ref}
      tabIndex={ref === undefined ? undefined : -1}
      className="alert"
      data-tone={tone}
      role={announce ? "alert" : undefined}
    >
      <Glyph name={glyph ?? GLYPH[tone]} />
      <div className="grid gap-4">
        <p className="alert-title">{title}</p>
        {children !== undefined && <div className="small">{children}</div>}
        {actions !== undefined && <div className="alert-actions">{actions}</div>}
      </div>
    </div>
  );
}
