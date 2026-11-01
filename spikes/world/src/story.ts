// The story so far: what the person has done, and when. Directions turn it into a scene; the DOM
// layer turns it into words. Times are seconds on the page's performance clock.
import { ROLES, type Role } from "./data.ts";
import {
  type Connection,
  type Destination,
  destinationsFor,
  unexpectedConnection,
} from "./model.ts";

export type Phase = "ask" | "grown" | "revealed";

export const TIMING = {
  /** The revelation follows the first answer after this beat (seconds). */
  revealDelay: 2.4,
  /** The revelation is staged over this long, then settles (plan section 4: 0.6–1.8 s). */
  revealLength: 1.8,
  /** Travel between views (plan section 4: up to 600 ms). */
  travel: 0.6,
} as const;

export const now = (): number => performance.now() / 1000;

export class Story {
  phase: Phase = "ask";
  role: Role | null = null;
  connection: Connection | null = null;
  destinations: Destination[] = [];
  /** Skills the person said they have done, with when they said it. */
  readonly said = new Map<string, number>();
  /** When the person kept the revealed destination in view, or null. */
  kept: number | null = null;
  igniteAt = -1e6;
  revealAt = -1e6;
  /** The measurement scene: 100 made-up openings around the destinations. */
  busy = false;
  /** The destination the person is pointing at or has focused: it shows its shared skills. */
  focus: string | null = null;
  focusAt = -1e6;

  answer(role: Role, at = now()): void {
    this.role = role;
    this.connection = unexpectedConnection(role, ROLES);
    this.destinations = destinationsFor(
      role,
      ROLES,
      new Set(this.connection ? [this.connection.role.id] : []),
    );
    this.said.clear();
    this.kept = null;
    this.focus = null;
    this.phase = "grown";
    this.igniteAt = at;
    this.revealAt = -1e6;
  }

  /** Stages the revelation, if there is one to show. A revelation with no source is not shown. */
  reveal(at = now()): void {
    if (this.phase !== "grown" || !this.connection) return;
    this.phase = "revealed";
    this.revealAt = at;
  }

  isRevealing(at = now()): boolean {
    return this.phase === "revealed" && at < this.revealAt + TIMING.revealLength;
  }

  /** Any input completes a revelation at once. */
  completeReveal(at = now()): void {
    if (!this.isRevealing(at)) return;
    this.revealAt = at - TIMING.revealLength;
  }

  toggleSaid(skill: string, at = now()): void {
    if (this.said.has(skill)) this.said.delete(skill);
    else this.said.set(skill, at);
  }

  keep(at = now()): void {
    if (this.phase !== "revealed") return;
    this.kept = at;
  }

  undoKeep(): void {
    this.kept = null;
  }

  /** Returns true when what the person points at changed. */
  point(destination: string | null, at = now()): boolean {
    if (destination === this.focus) return false;
    this.focus = destination;
    this.focusAt = at;
    return true;
  }

  reset(): void {
    this.phase = "ask";
    this.role = null;
    this.connection = null;
    this.destinations = [];
    this.said.clear();
    this.kept = null;
    this.focus = null;
    this.igniteAt = -1e6;
    this.revealAt = -1e6;
    this.busy = false;
  }

  /** Jumps straight to the settled, busiest state (measurement and screenshots only). */
  preset(role: Role, options: { busy: boolean; kept: boolean }, at = now()): void {
    this.answer(role, at - 30);
    this.reveal(at - 30 + TIMING.revealDelay);
    if (options.kept) this.kept = at - 20;
    this.busy = options.busy;
  }

  /** Replays the revelation's staging without changing what it says (measurement only). */
  replayReveal(at = now()): void {
    if (this.phase !== "revealed") return;
    this.revealAt = at;
  }
}
