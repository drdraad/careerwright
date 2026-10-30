// The product's fixed icon set: the glyphs drawn for the Sprint 0 design references (simple
// SVG paths authored for this project, so no third-party licence applies), plus the few
// interface glyphs the shell needs, drawn in the same 24-unit, 1.8-stroke style.
// Status is never colour alone: each state has its own shape (docs/design/README.md).
import type { ReactNode } from "react";

const stroke = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round",
  strokeLinejoin: "round",
} as const;

const PATHS = {
  mark: (
    <>
      <circle cx="9" cy="15" r="5.2" {...stroke} strokeWidth={1.6} />
      <path d="M12.6 11.3C14.6 8.6 16 7.3 18.4 6.2" {...stroke} strokeWidth={1.6} />
      <circle cx="19.6" cy="5.6" r="1.9" {...stroke} strokeWidth={1.6} />
    </>
  ),
  complete: (
    <>
      <circle cx="12" cy="12" r="9" {...stroke} />
      <path d="M7.8 12.4l2.8 2.8 5.6-6" {...stroke} />
    </>
  ),
  conditional: (
    <>
      <path d="M12 3.2L20.8 12 12 20.8 3.2 12z" {...stroke} />
      <circle cx="12" cy="12" r="2" fill="currentColor" />
    </>
  ),
  stale: (
    <>
      <circle cx="12" cy="12" r="9" {...stroke} />
      <path d="M12 7v5.2l3.4 2" {...stroke} />
    </>
  ),
  error: (
    <>
      <path d="M12 3.5L21.5 20h-19z" {...stroke} />
      <path d="M12 9.5v5" {...stroke} />
      <circle cx="12" cy="17.3" r="1.1" fill="currentColor" />
    </>
  ),
  unknown: (
    <>
      <circle cx="12" cy="12" r="9" {...stroke} />
      <path
        d="M9.6 9.6a2.5 2.5 0 1 1 3.6 2.2c-.8.4-1.2.9-1.2 1.7v.4"
        {...stroke}
        strokeWidth={1.7}
      />
      <circle cx="12" cy="16.9" r="1" fill="currentColor" />
    </>
  ),
  synthetic: (
    <>
      <path
        d="M9.5 3.5h5M10.5 3.5v5.8L5.6 17.8a2 2 0 0 0 1.7 3h9.4a2 2 0 0 0 1.7-3l-4.9-8.5V3.5"
        {...stroke}
        strokeWidth={1.7}
      />
      <path d="M7.8 14.5h8.4" {...stroke} strokeWidth={1.7} />
    </>
  ),
  source: (
    <>
      <path d="M7 3.5h7l4 4v13H7z" {...stroke} strokeWidth={1.7} />
      <path d="M14 3.5v4h4M9.5 12h6M9.5 15.5h6" {...stroke} strokeWidth={1.7} />
    </>
  ),
  close: <path d="M6.5 6.5l11 11M17.5 6.5l-11 11" {...stroke} />,
  menu: <path d="M4 7h16M4 12h16M4 17h10" {...stroke} />,
  expand: <path d="M7 14.5l5-5 5 5" {...stroke} />,
  collapse: <path d="M7 9.5l5 5 5-5" {...stroke} />,
  // Interface glyphs added in Task 4, same construction.
  draft: (
    <>
      <path d="M5 19l1-4L15.5 5.5a2.1 2.1 0 0 1 3 3L9 18z" {...stroke} />
      <path d="M13.5 7.5l3 3" {...stroke} />
    </>
  ),
  queued: (
    <>
      <circle cx="12" cy="12" r="9" {...stroke} />
      <circle cx="8" cy="12" r="1.1" fill="currentColor" />
      <circle cx="12" cy="12" r="1.1" fill="currentColor" />
      <circle cx="16" cy="12" r="1.1" fill="currentColor" />
    </>
  ),
  running: (
    <>
      <path d="M12 3a9 9 0 1 1-9 9" {...stroke} />
      <path d="M12 7.5V12l3 1.8" {...stroke} />
    </>
  ),
  partial: (
    <>
      <circle cx="12" cy="12" r="9" {...stroke} />
      <path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" />
    </>
  ),
  cancelled: (
    <>
      <circle cx="12" cy="12" r="9" {...stroke} />
      <path d="M8.5 8.5l7 7" {...stroke} />
    </>
  ),
  blocked: (
    <>
      <circle cx="12" cy="12" r="9" {...stroke} />
      <path d="M7.5 12h9" {...stroke} />
    </>
  ),
  coverage: (
    <>
      <circle cx="12" cy="12" r="9" {...stroke} />
      <circle cx="12" cy="12" r="4.5" {...stroke} />
    </>
  ),
  unavailable: (
    <>
      <path d="M8 4v4M16 4v4M6 8h12v3a6 6 0 0 1-12 0z" {...stroke} />
      <path d="M12 17v3.5M4 4l16 16" {...stroke} />
    </>
  ),
  signOut: (
    <>
      <path d="M14 4.5H6.5v15H14" {...stroke} />
      <path d="M10.5 12h9M16.5 8.5L20 12l-3.5 3.5" {...stroke} />
    </>
  ),
  live: (
    <>
      <circle cx="12" cy="12" r="3.2" fill="currentColor" />
      <circle cx="12" cy="12" r="7.5" {...stroke} />
    </>
  ),
  route: (
    <>
      <circle cx="6" cy="17.5" r="2.5" {...stroke} />
      <circle cx="18" cy="6.5" r="2.5" {...stroke} />
      <path d="M8.3 16.3c4-1.6 3.4-5.7 7.4-8.6" {...stroke} />
    </>
  ),
  // The world's controls (Sprint W), same construction.
  pause: (
    <>
      <circle cx="12" cy="12" r="9" {...stroke} />
      <path d="M10 8.5v7M14 8.5v7" {...stroke} />
    </>
  ),
  calm: (
    <>
      <path d="M3.5 9.5c2.8-2 5.7-2 8.5 0s5.7 2 8.5 0" {...stroke} />
      <path d="M3.5 15.5h17" {...stroke} />
    </>
  ),
  sound: (
    <>
      <path d="M4.5 9.5h3.2L12 5.5v13l-4.3-4H4.5z" {...stroke} />
      <path d="M15.5 9a4.2 4.2 0 0 1 0 6M18 6.5a7.8 7.8 0 0 1 0 11" {...stroke} />
    </>
  ),
  // The calm support panel's own glyph, a lifebuoy (docs/design: never "not known yet").
  support: (
    <>
      <circle cx="12" cy="12" r="8.5" {...stroke} />
      <circle cx="12" cy="12" r="3.8" {...stroke} />
      <path d="M6 6l3.3 3.3M18 6l-3.3 3.3M6 18l3.3-3.3M18 18l-3.3-3.3" {...stroke} />
    </>
  ),
} satisfies Record<string, ReactNode>;

export type GlyphName = keyof typeof PATHS;

type Props = {
  name: GlyphName;
  /** Accessible name when the glyph carries meaning on its own; omit when words sit beside it. */
  label?: string;
  className?: string;
};

export function Glyph({ name, label, className }: Props) {
  if (label !== undefined) {
    return (
      <svg viewBox="0 0 24 24" className={className ?? "glyph"} role="img" aria-label={label}>
        <title>{label}</title>
        {PATHS[name]}
      </svg>
    );
  }
  // Decorative: the words beside it carry the meaning, so it is hidden from assistive tech.
  return (
    <svg viewBox="0 0 24 24" className={className ?? "glyph"} aria-hidden="true" focusable="false">
      {PATHS[name]}
    </svg>
  );
}
