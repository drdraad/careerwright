// Sound is off until the person turns it on (session W1), and each of the three cues stays
// quiet: "subtle and evocative, not cheesy". The audio graph is faked at the system edge.
import { describe, expect, it, vi } from "vitest";
import { CUES, Sound } from "./sound";

type Ramp = { value: number; at: number };

function fakeContext() {
  const peaks: number[] = [];
  const oscillators: { type: string; frequency: number }[] = [];
  /** An audio parameter; a gain's ramps are recorded as the levels it reaches. */
  const param = (initial: number, gain: boolean) => {
    const ramps: Ramp[] = [];
    return {
      value: initial,
      setValueAtTime: (value: number, at: number) => ramps.push({ value, at }),
      exponentialRampToValueAtTime: (value: number, at: number) => {
        ramps.push({ value, at });
        if (gain) peaks.push(value);
      },
    };
  };
  const node = () => ({ connect: (next: unknown) => next });
  const context = {
    currentTime: 0,
    destination: {},
    resume: vi.fn(async () => {}),
    suspend: vi.fn(async () => {}),
    createGain: () => ({ ...node(), gain: param(1, true) }),
    createDelay: () => ({ ...node(), delayTime: param(0, false) }),
    createBiquadFilter: () => ({
      ...node(),
      type: "",
      Q: param(0, false),
      frequency: param(0, false),
    }),
    createOscillator: () => {
      const osc = {
        ...node(),
        type: "sine",
        frequency: {
          ...param(0, false),
          setValueAtTime: (value: number) => {
            oscillators.push({ type: osc.type, frequency: value });
          },
          exponentialRampToValueAtTime: () => {},
        },
        start: vi.fn(),
        stop: vi.fn(),
      };
      return osc;
    },
  };
  return { context, peaks, oscillators };
}

describe("[UI-05] the world's sound", () => {
  it("is off by default and makes no audio context until turned on", () => {
    const create = vi.fn();
    const sound = new Sound(create);
    expect(sound.on).toBe(false);
    sound.play("swell");
    expect(create).not.toHaveBeenCalled();
  });

  it.each(CUES)("plays the %s quietly once turned on, and not after turning off", (cue) => {
    const fake = fakeContext();
    const sound = new Sound(() => fake.context as unknown as AudioContext);
    sound.setEnabled(true);
    expect(fake.context.resume).toHaveBeenCalled();
    sound.play(cue);
    expect(fake.oscillators.length).toBeGreaterThan(0);
    // Every partial's envelope peaks well under full scale (and the master level halves it).
    expect(Math.max(...fake.peaks)).toBeLessThanOrEqual(0.1);

    const before = fake.oscillators.length;
    sound.setEnabled(false);
    expect(fake.context.suspend).toHaveBeenCalled();
    sound.play(cue);
    expect(fake.oscillators.length).toBe(before);
  });

  it("has exactly the three cues the product owner chose", () => {
    expect([...CUES]).toEqual(["swell", "chime", "tick"]);
  });
});
