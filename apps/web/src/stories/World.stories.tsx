// The world behind every chapter (plan section 4): each place, the waiting world before the
// first answer, the still world, the busiest scene the frame budgets are measured on, and the
// three sounds. People's targets come from the supplied fixture pack (P01, and the strip's
// labelled three-target case); the busiest scene's skills and openings are invented, and say so.
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/Button";
import { SyntheticLabel } from "@/components/Status";
import { World } from "@/components/World";
import { CHAPTERS, type ChapterId } from "@/lib/chapters";
import type { WorldMeasurement } from "@/lib/world/frames";
import { EMPTY_WORLD, type WorldInput, worldFromProfile } from "@/lib/world/model";
import { CUES, type Cue, Sound } from "@/lib/world/sound";
import { longDocument, p01Document, profile } from "./data";

const meta: Meta = { title: "World", parameters: { layout: "fullscreen" } };
export default meta;
type Story = StoryObj;

const p01 = worldFromProfile(profile(p01Document));
const threeTargets = worldFromProfile(profile(longDocument));

/** A place, with the chapter's name where the chapter's panel would be. */
function Place({
  place,
  input,
  calm = false,
}: {
  place: ChapterId;
  input: WorldInput;
  calm?: boolean;
}) {
  const label = CHAPTERS.find((chapter) => chapter.id === place)?.label;
  return (
    <>
      <div className="app">
        <div
          className="chapter on-reading chapter-place"
          data-covers-world
          data-world-panel
          style={{ gridColumn: 2 }}
        >
          <h1 className="page-title">{label}</h1>
          <SyntheticLabel />
        </div>
      </div>
      <World place={place} input={input} calm={calm} paused={false} />
    </>
  );
}

export const WaitingForTheFirstAnswer: Story = {
  render: () => <Place place="you" input={{ ...EMPTY_WORLD }} />,
};

export const YouWithP01: Story = { render: () => <Place place="you" input={p01} /> };
export const RolesWithThreeTargets: Story = {
  render: () => <Place place="roles" input={threeTargets} />,
};
export const SkillsWithThreeTargets: Story = {
  render: () => <Place place="skills" input={threeTargets} />,
};
export const OptionsWithThreeTargets: Story = {
  render: () => <Place place="options" input={threeTargets} />,
};
export const RoutesWithThreeTargets: Story = {
  render: () => <Place place="routes" input={threeTargets} />,
};
export const PlanWithThreeTargets: Story = {
  render: () => <Place place="plan" input={threeTargets} />,
};
export const StillRolesInCalmMode: Story = {
  render: () => <Place place="roles" input={threeTargets} calm />,
};

/** Travel: the same world, the view moving from place to place. */
function Travel() {
  const [place, setPlace] = useState<ChapterId>("you");
  return (
    <>
      <nav className="app on-space" aria-label="Places">
        <div
          className="chapter on-reading chapter-place"
          data-covers-world
          data-world-panel
          style={{ gridColumn: 2 }}
        >
          <h1 className="page-title">Travel between places</h1>
          <div className="flex flex-wrap gap-8">
            {CHAPTERS.map((chapter) => (
              <Button
                key={chapter.id}
                variant="secondary"
                aria-pressed={chapter.id === place}
                onClick={() => setPlace(chapter.id)}
              >
                {chapter.label}
              </Button>
            ))}
          </div>
        </div>
      </nav>
      <World place={place} input={threeTargets} calm={false} paused={false} />
    </>
  );
}

export const TravelBetweenPlaces: Story = { render: () => <Travel /> };

/** Invented for measurement only: 12 skills, 5 destinations sharing some, and 100 openings. */
const BUSIEST: WorldInput = {
  lit: true,
  skills: Array.from({ length: 12 }, (_, i) => ({
    id: `k${i}`,
    label: `Invented skill ${i + 1}`,
    state: i % 3 === 0 ? "said" : "usual",
  })),
  destinations: [
    "Invented role A",
    "Invented role B",
    "Invented role C",
    "Invented role D",
    "Invented role E",
  ].map((title, j) => ({
    id: `d${j}`,
    title,
    shared: Array.from({ length: 12 }, (_, i) => `k${i}`).filter((_, i) => (i + j) % 2 === 0),
  })),
  openings: 100,
};

declare global {
  interface Window {
    __careerwrightWorldFrames?: WorldMeasurement;
  }
}

/**
 * The busiest scene (plan section 4: 100 openings, their trails and the ambient motes), with
 * travel every 3 s and the ignition replayed every 4 s. `?measure` in the story's address
 * samples frame costs for 12 s after 3 s and leaves the result on `window`.
 */
function Busiest() {
  const measuring = new URLSearchParams(window.location.search).has("measure");
  const [place, setPlace] = useState<ChapterId>("roles");
  const [result, setResult] = useState<WorldMeasurement | null>(null);
  const measure = useMemo(
    () =>
      measuring
        ? {
            warmupSeconds: 3,
            seconds: 12,
            igniteEverySeconds: 4,
            onResult: (measured: WorldMeasurement) => {
              window.__careerwrightWorldFrames = measured;
              setResult(measured);
            },
          }
        : undefined,
    [measuring],
  );
  useEffect(() => {
    if (!measuring) return;
    const order: ChapterId[] = ["roles", "routes", "you", "skills", "plan", "options"];
    let i = 0;
    const travel = window.setInterval(() => {
      i = (i + 1) % order.length;
      setPlace(order[i] as ChapterId);
    }, 3000);
    return () => window.clearInterval(travel);
  }, [measuring]);
  return (
    <>
      <div className="app">
        <div
          className="chapter on-reading chapter-place"
          data-covers-world
          data-world-panel
          style={{ gridColumn: 2 }}
        >
          <h1 className="page-title">The busiest scene</h1>
          <p>Invented for measuring frame times: 12 skills, 5 destinations and 100 openings.</p>
          <SyntheticLabel />
          {result !== null && <output data-testid="frames">{JSON.stringify(result)}</output>}
        </div>
      </div>
      <World place={place} input={BUSIEST} calm={false} paused={false} measure={measure} />
    </>
  );
}

export const BusiestScene: Story = { render: () => <Busiest /> };

const CUE_WORDS: Record<Cue, string> = {
  swell: "Swell: your light comes on",
  chime: "Chime: a connection lights up",
  tick: "Tick: you pick a skill",
};

/**
 * The three cues, each played from a click (the browser allows sound only after one). Only the
 * swell has a trigger in the app so far; the chime and the tick have none until W2C.
 */
function Sounds() {
  const sound = useMemo(() => new Sound(), []);
  return (
    <div className="chapter on-reading" style={{ maxWidth: 520 }}>
      <h1 className="page-title">The world's sounds</h1>
      <p>
        Off until the person turns sound on. Each is short and quiet. In the app only the swell
        plays so far (the person's light coming on); the chime and the tick wait for the moments
        that trigger them.
      </p>
      <div className="flex flex-wrap gap-8">
        {CUES.map((cue) => (
          <Button
            key={cue}
            variant="secondary"
            onClick={() => {
              sound.setEnabled(true);
              sound.play(cue);
            }}
          >
            {CUE_WORDS[cue]}
          </Button>
        ))}
      </div>
    </div>
  );
}

export const ThreeSounds: Story = { render: () => <Sounds /> };
