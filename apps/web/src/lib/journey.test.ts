import { describe, expect, it } from "vitest";
import type { CheckpointOut, ProfileOut, SkillsOut } from "@/generated/api";
import { journeyOf } from "./journey";

const profile = (titles: string[]) =>
  ({
    document: {
      target_titles: {
        state: titles.length ? "provided" : "unasked",
        value: titles.length ? titles : null,
      },
    },
  }) as ProfileOut;

const checkpoint = (blocked: boolean) =>
  ({
    targets: [{ target_title: "Data quality analyst" }],
    needs: blocked ? [{ input: "objective_basis", effect: "blocks_a_solve" }] : [],
  }) as CheckpointOut;

describe("saved chapter milestones", () => {
  it("starts a blank person in You and blocks later destinations", () => {
    const journey = journeyOf({
      profile: profile([]),
      skills: undefined,
      checkpoint: undefined,
      routeFound: false,
      planSaved: false,
      planCandidate: false,
    });
    expect(journey.progress).toEqual({
      you: "available",
      roles: "locked",
      skills: "locked",
      options: "locked",
      routes: "locked",
      plan: "locked",
    });
  });

  it("lets a target holder explore roles, skills and options without claiming a chapter was read", () => {
    const journey = journeyOf({
      profile: profile(["Data quality analyst"]),
      skills: undefined,
      checkpoint: checkpoint(true),
      routeFound: false,
      planSaved: false,
      planCandidate: false,
    });
    expect(journey.progress.you).toBe("complete");
    expect(journey.progress.roles).toBe("available");
    expect(journey.progress.skills).toBe("available");
    expect(journey.progress.options).toBe("available");
    expect(journey.progress.routes).toBe("locked");
  });

  it("unlocks Routes only after required planning facts and Plan after a route result", () => {
    const facts = {
      profile: profile(["Data quality analyst"]),
      skills: {
        questions: { state: "enough" },
        targets: [{ readiness: { state: "not_ready", rows: [{ status: "below_required" }] } }],
      } as SkillsOut,
      checkpoint: checkpoint(false),
    };
    const ready = journeyOf({
      ...facts,
      routeFound: false,
      planSaved: false,
      planCandidate: false,
    });
    expect(ready.progress.skills).toBe("complete");
    expect(ready.progress.options).toBe("complete");
    expect(ready.progress.routes).toBe("available");
    expect(ready.progress.plan).toBe("locked");
    const found = journeyOf({ ...facts, routeFound: true, planSaved: false, planCandidate: false });
    expect(found.progress.routes).toBe("complete");
    expect(found.progress.plan).toBe("locked");
    const candidate = journeyOf({
      ...facts,
      routeFound: true,
      planSaved: false,
      planCandidate: true,
    });
    expect(candidate.progress.plan).toBe("available");
    const saved = journeyOf({ ...facts, routeFound: true, planSaved: true, planCandidate: false });
    expect(saved.progress.plan).toBe("complete");
  });

  it("keeps Skills available when an answer leaves a requirement unresolved", () => {
    const journey = journeyOf({
      profile: profile(["Nurse"]),
      skills: {
        questions: { state: "enough" },
        targets: [{ readiness: { state: "not_ready", rows: [{ status: "unresolved" }] } }],
      } as SkillsOut,
      checkpoint: checkpoint(false),
      routeFound: false,
      planSaved: false,
      planCandidate: false,
    });
    expect(journey.progress.skills).toBe("available");
  });

  it("keeps an earlier route result visible when a later edit needs new planning answers", () => {
    const journey = journeyOf({
      profile: profile(["Data quality analyst"]),
      skills: undefined,
      checkpoint: checkpoint(true),
      routeFound: true,
      planSaved: false,
      planCandidate: false,
    });
    expect(journey.progress.routes).toBe("complete");
    expect(journey.progress.options).toBe("available");
  });
});
