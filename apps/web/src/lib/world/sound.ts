// Three short cues the product owner asked for at session W1, "subtle and evocative, not
// cheesy": a swell when the person's light comes on, a chime, and a tick when a skill is
// picked. Off until the person turns sound on (from a click, so the browser lets audio start).
// Synthesised in the browser: no audio files and no requests.

export type Cue = "swell" | "chime" | "tick";

/**
 * Only the swell has a trigger so far (the person's light coming on, World.tsx). The chime was
 * made for a connection lighting up, which is dropped (the product owner, 1 November 2026:
 * shared skills are "Always a plain line"), so it has no trigger unless Task M gives it
 * another; the tick has none until picking a skill exists. Until then both play only from the
 * `World / Three sounds` story.
 */
export const CUES: readonly Cue[] = ["swell", "chime", "tick"];

/** Kept low: the cues sit under the world, never over the person's own thoughts. */
const MASTER_GAIN = 0.5;

type Partial = {
  readonly frequency: number;
  readonly start: number;
  readonly attack: number;
  readonly length: number;
  readonly peak: number;
  readonly type?: OscillatorType;
  /** A slow glide to this frequency over the partial's length. */
  readonly glideTo?: number;
};

/** Each cue as partials (seconds and linear gain), and how bright its filter opens. */
const SCORE: Record<
  Cue,
  { partials: readonly Partial[]; filter: readonly [number, number]; space: number }
> = {
  // A breath of light: low fifths rising slowly through an opening filter.
  swell: {
    partials: [
      { frequency: 110, start: 0, attack: 0.9, length: 2.8, peak: 0.09, glideTo: 112 },
      { frequency: 164.81, start: 0.05, attack: 1.0, length: 2.6, peak: 0.05 },
      { frequency: 220, start: 0.1, attack: 1.1, length: 2.4, peak: 0.04, type: "triangle" },
      { frequency: 440, start: 0.35, attack: 0.9, length: 1.9, peak: 0.012 },
    ],
    filter: [260, 1500],
    space: 0.18,
  },
  // A soft bell, then its fifth: two things joined.
  chime: {
    partials: [
      { frequency: 659.25, start: 0, attack: 0.006, length: 1.8, peak: 0.05 },
      { frequency: 1318.5, start: 0, attack: 0.006, length: 0.9, peak: 0.016 },
      { frequency: 1819.5, start: 0, attack: 0.004, length: 0.5, peak: 0.008 },
      { frequency: 987.77, start: 0.13, attack: 0.006, length: 1.6, peak: 0.035 },
      { frequency: 1975.5, start: 0.13, attack: 0.006, length: 0.7, peak: 0.01 },
    ],
    filter: [4200, 3200],
    space: 0.3,
  },
  // A small glass tick.
  tick: {
    partials: [
      { frequency: 2093, start: 0, attack: 0.002, length: 0.08, peak: 0.035 },
      { frequency: 3136, start: 0, attack: 0.002, length: 0.05, peak: 0.012 },
    ],
    filter: [6000, 6000],
    space: 0.08,
  },
};

/** The shared output: the master level, and one soft echo fed back once or twice for space. */
type Bus = { readonly out: GainNode; readonly echo: DelayNode };

function createBus(ctx: AudioContext): Bus {
  const out = ctx.createGain();
  out.gain.value = MASTER_GAIN;
  out.connect(ctx.destination);
  const echo = ctx.createDelay(1);
  echo.delayTime.value = 0.21;
  const feedback = ctx.createGain();
  feedback.gain.value = 0.28;
  echo.connect(out);
  echo.connect(feedback).connect(echo);
  return { out, echo };
}

export class Sound {
  private context: AudioContext | null = null;
  private bus: Bus | null = null;
  private enabled = false;

  constructor(private readonly createContext: () => AudioContext = () => new AudioContext()) {}

  get on(): boolean {
    return this.enabled;
  }

  /** Call from the control's click, so the browser allows audio to start. */
  setEnabled(on: boolean): void {
    this.enabled = on;
    if (on && this.context === null) {
      this.context = this.createContext();
      this.bus = createBus(this.context);
    }
    if (on) void this.context?.resume();
    else void this.context?.suspend();
  }

  /** Releases the audio context; sound starts again only from another click. */
  close(): void {
    void this.context?.close();
    this.context = null;
    this.bus = null;
    this.enabled = false;
  }

  play(cue: Cue): void {
    const ctx = this.context;
    const bus = this.bus;
    if (!this.enabled || ctx === null || bus === null) return;
    const { partials, filter, space } = SCORE[cue];
    const t = ctx.currentTime + 0.01;
    const length = Math.max(...partials.map((p) => p.start + p.length));

    const tone = ctx.createBiquadFilter();
    tone.type = "lowpass";
    tone.Q.value = 0.4;
    tone.frequency.setValueAtTime(filter[0], t);
    tone.frequency.exponentialRampToValueAtTime(filter[1], t + length * 0.6);
    tone.connect(bus.out);
    const wet = ctx.createGain();
    wet.gain.value = space;
    tone.connect(wet).connect(bus.echo);

    for (const p of partials) {
      const osc = ctx.createOscillator();
      const env = ctx.createGain();
      osc.type = p.type ?? "sine";
      osc.frequency.setValueAtTime(p.frequency, t + p.start);
      if (p.glideTo !== undefined) {
        osc.frequency.exponentialRampToValueAtTime(p.glideTo, t + p.start + p.length);
      }
      env.gain.setValueAtTime(0.0001, t + p.start);
      env.gain.exponentialRampToValueAtTime(p.peak, t + p.start + p.attack);
      env.gain.exponentialRampToValueAtTime(0.0001, t + p.start + p.length);
      osc.connect(env).connect(tone);
      osc.start(t + p.start);
      osc.stop(t + p.start + p.length + 0.05);
    }
  }
}
