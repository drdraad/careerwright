// The motion vocabulary's timings in seconds, for the moving world (plan section 4). They are
// the design tokens' values (`--motion-*` in src/design/tokens/tokens.css); `motion.test.ts`
// holds the two to each other.
export const MOTION = {
  /** Travel between places: the world stays, the view moves. */
  travel: 0.6,
  /** Growth: a new possibility grows its trail. */
  grow: 0.65,
  /** Ignition: new evidence lights the person's light. */
  ignite: 1.4,
  /** One slow breath of light (atmosphere). */
  breathe: 7,
} as const;

/** How long after a keystroke the person still counts as typing (ambient motion holds still). */
export const TYPING_HOLD_SECONDS = 1.5;

/** Seconds on the page's clock. */
export const now = (): number => performance.now() / 1000;
