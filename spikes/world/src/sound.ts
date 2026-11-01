// A short, off-by-default sound for ignition and the revelation (plan section 4 lets the spike
// try it; it ships only if the product owner asks). Synthesised: no audio files, no requests.
import type { DirectionId } from "./direction.ts";

type Cue = "ignite" | "reveal" | "touch";

export class Sound {
  private context: AudioContext | null = null;
  enabled = false;
  private readonly direction: DirectionId;

  constructor(direction: DirectionId) {
    this.direction = direction;
  }

  /** Called from the toggle's click, so the browser allows audio to start. */
  setEnabled(on: boolean): void {
    this.enabled = on;
    if (on && !this.context) this.context = new AudioContext();
    if (on) void this.context?.resume();
  }

  play(cue: Cue): void {
    const ctx = this.context;
    if (!this.enabled || !ctx) return;
    const t = ctx.currentTime + 0.01;
    const out = ctx.createGain();
    out.gain.value = 0.16;
    out.connect(ctx.destination);
    const tone = (freq: number, start: number, length: number, type: OscillatorType, peak: number, glideTo?: number) => {
      const osc = ctx.createOscillator();
      const env = ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, t + start);
      if (glideTo) osc.frequency.exponentialRampToValueAtTime(glideTo, t + start + length);
      env.gain.setValueAtTime(0.0001, t + start);
      env.gain.exponentialRampToValueAtTime(peak, t + start + Math.min(0.08, length / 3));
      env.gain.exponentialRampToValueAtTime(0.0001, t + start + length);
      osc.connect(env).connect(out);
      osc.start(t + start);
      osc.stop(t + start + length + 0.05);
    };
    const notes = { growth: [196, 294, 392], horizon: [220, 330, 440], circuit: [440, 660, 880] }[this.direction];
    const wave: OscillatorType = this.direction === "circuit" ? "square" : "sine";
    const [low, mid, high] = notes as [number, number, number];
    if (cue === "touch") {
      tone(high * 1.5, 0, 0.12, "sine", 0.25);
    } else if (cue === "ignite") {
      tone(low / 2, 0, 1.2, "sine", 0.7, low);
      tone(mid, 0.12, 0.9, wave, this.direction === "circuit" ? 0.08 : 0.3);
    } else {
      tone(low, 0, 1.6, "sine", 0.45);
      tone(mid, 0.25, 1.4, "sine", 0.35);
      tone(high, 0.5, 1.3, wave, this.direction === "circuit" ? 0.06 : 0.3);
      tone(high * 1.5, 0.8, 1.0, "sine", 0.2);
    }
  }
}
