"use client";
// How the world moves and sounds for this viewer: calm mode (kept between visits, a per-viewer
// convenience), pausing ambient motion and sound (both for this visit only: sound is off until
// the person turns it on, every visit). The system's reduced-motion setting always wins. And
// whether the calm support panel is showing, which stills the world while it does.
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { Sound } from "./sound";

const CALM_KEY = "careerwright.calm";

/**
 * Tells the workspace shell that the calm support panel is showing: the world is drawn still
 * while it does (plan section 4, ADR 0007). Outside a shell nothing listens.
 */
export const SupportShown = createContext<(shown: boolean) => void>(() => {});

/** Called by the support panel itself: shown while it is mounted. */
export function useSupportShown(): void {
  const report = useContext(SupportShown);
  useEffect(() => {
    report(true);
    return () => report(false);
  }, [report]);
}

/** For the shell: whether any support panel shows, and the report each panel makes. Panels
 *  are counted: the first question's stays until dismissed, so it can show beside a message's
 *  or What we know's, and the world stays still until the last goes. */
export function useSupportPanels(): [boolean, (shown: boolean) => void] {
  const [count, setCount] = useState(0);
  const report = useCallback(
    (shown: boolean) => setCount((n) => Math.max(0, n + (shown ? 1 : -1))),
    [],
  );
  return [count > 0, report];
}

export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(query.matches);
    const changed = () => setReduced(query.matches);
    query.addEventListener("change", changed);
    return () => query.removeEventListener("change", changed);
  }, []);
  return reduced;
}

export type WorldSettings = {
  /** The system asks for less motion: the world is drawn still and calm mode is implied. */
  reduced: boolean;
  calm: boolean;
  setCalm(calm: boolean): void;
  paused: boolean;
  setPaused(paused: boolean): void;
  soundOn: boolean;
  setSoundOn(on: boolean): void;
  sound: Sound;
};

export function useWorldSettings(): WorldSettings {
  const reduced = useReducedMotion();
  const [calm, setCalmState] = useState(false);
  const [paused, setPaused] = useState(false);
  const [soundOn, setSoundOnState] = useState(false);
  const sound = useRef<Sound | null>(null);
  sound.current ??= new Sound();
  // The audio context goes with the shell: browsers hold only a few.
  useEffect(() => () => sound.current?.close(), []);

  useEffect(() => {
    try {
      setCalmState(window.localStorage.getItem(CALM_KEY) === "true");
    } catch {
      // Private mode or blocked storage: calm mode simply starts off.
    }
  }, []);
  useEffect(() => {
    document.documentElement.dataset.calm = String(calm);
  }, [calm]);

  const setCalm = (next: boolean) => {
    setCalmState(next);
    try {
      window.localStorage.setItem(CALM_KEY, String(next));
    } catch {
      // As above: the choice holds for this page only.
    }
  };
  const setSoundOn = (on: boolean) => {
    // Called from the control's click, so the browser lets audio start.
    sound.current?.setEnabled(on);
    setSoundOnState(on);
  };
  return { reduced, calm, setCalm, paused, setPaused, soundOn, setSoundOn, sound: sound.current };
}
