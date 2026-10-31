// Discovery's facts in words (Task 6d slice A; ruling R11): the API serves what each search or
// match did, and the web words it. One test per fixed sentence checks its words: each is the
// sentence the API composed before (from the backend tests that checked it then), unless the
// sentence rule changed it, which the test says.
import { describe, expect, it } from "vitest";
import type {
  AiResilienceFilterOut,
  SalaryFloorOut,
  SlateOut,
  SuggestionOut,
} from "@/generated/api";
import {
  aiFilterWords,
  fewerReason,
  floorWords,
  RESEARCH_STATUS,
  slateNote,
  suggestionReason,
  suggestionWords,
  TARGET_COVERAGE,
  titleIdeasWords,
} from "./vocabulary";

type Note = SlateOut["notes"][number];
type Fewer = SlateOut["fewer_reasons"][number];
type Reason = SuggestionOut["reasons"][number];

const mainName = "main name of a skill ESCO lists as essential holds all the words of";
const commonOnly = "only common words, which Careerwright doesn't search for";
const noWork = (
  answer: string,
  searches: [string, "read_main_names" | "only_common_words" | "no_shared_occupation"][],
  ownWords: boolean,
): Note => ({
  reason: "answer_found_no_work",
  outcome: "found_none",
  answer,
  own_words: ownWords,
  searches: searches.map(([text, did]) => ({ text, did })),
  min_shared: 3,
});
const bridges = "writing inspection reports for bridges";
const general = (narrower: string[]): Note => ({
  reason: "too_general",
  outcome: "found_none",
  search: "write reports",
  answers: [bridges],
  own_words: false,
  by: "occupations",
  occupations: 217,
  skills: 17,
  narrower_for: narrower,
});

describe("[DIV1-06][DIV1-02] how the slate searched, in words", () => {
  it.each<[string, Note, string]>([
    [
      "a changed release",
      { reason: "release_changed", searched: "esco-v1.1.1-en-csv", held: "esco-v1.2.1-en-csv" },
      "These searches were chosen when ESCO esco-v1.1.1-en-csv was held; this slate uses esco-v1.2.1-en-csv, so some occupations may have changed.",
    ],
    [
      "one-word work styles",
      {
        reason: "one_word_work_style",
        outcome: "not_searched",
        answers: ["structured", "practical"],
      },
      "How you like to work (“structured”, “practical”) isn't searched on its own, because a single word matches too loosely. Careerwright searches a longer answer, such as “working outdoors”.",
    ],
    [
      "an answer searched in its own words",
      noWork("taking pictures", [["taking pictures", "read_main_names"]], true),
      `No ${mainName} “taking pictures”, so it found no work.`,
    ],
    [
      "an answer of only common words",
      noWork("all of it", [["all of it", "only_common_words"]], true),
      `“All of it” has ${commonOnly}, so it found no work.`,
    ],
    [
      "a model's several searches of one answer",
      noWork(
        "fixing things",
        [
          ["repair machinery", "read_main_names"],
          ["fix equipment", "read_main_names"],
        ],
        false,
      ),
      `“Fixing things” found no work: no ${mainName} any of its searches “repair machinery” and “fix equipment”.`,
    ],
    [
      "a model's one search",
      noWork("tidying stockrooms", [["organise stock", "read_main_names"]], false),
      `“Tidying stockrooms” found no work: no ${mainName} its search “organise stock”.`,
    ],
    [
      "searches that did three things",
      noWork(
        "fixing things",
        [
          ["repair machinery", "read_main_names"],
          ["the other", "only_common_words"],
          ["warehouse manager", "no_shared_occupation"],
        ],
        false,
      ),
      `“Fixing things” found no work: no ${mainName} its search “repair machinery”, and its search “the other” has ${commonOnly}, and Careerwright found no other occupation in ESCO that shares 3 or more essential skills with its search “warehouse manager”, your own title.`,
    ],
    [
      "a model's search too general, its answer waiting",
      general([bridges]),
      `The search “write reports” (from “${bridges}”) reached 217 occupations in ESCO through the main names of their essential skills, too many to choose from on its own. Careerwright would need a narrower search to find work from “${bridges}”.`,
    ],
    [
      "a model's search too general, its answer found work elsewhere",
      general([]),
      `The search “write reports” (from “${bridges}”) reached 217 occupations in ESCO through the main names of their essential skills, too many to choose from on its own.`,
    ],
    [
      "the person's own words too general",
      {
        reason: "too_general",
        outcome: "found_none",
        search: "training staff",
        answers: ["training staff"],
        own_words: true,
        by: "skills",
        occupations: 17,
        skills: 10,
        narrower_for: [],
      },
      "“Training staff” matched the main names of 10 different essential skills in ESCO, none of them just those words, so it's too general to choose work from on its own. Say more about it, such as what it's about or who it's for.",
    ],
    [
      "what a join keeps",
      {
        reason: "join_kept_best",
        outcome: "found_work",
        title: "data analyst",
        found: 47,
        kept: 30,
        min_shared: 3,
      },
      "Careerwright found 47 other occupations in ESCO that share 3 or more essential skills with “data analyst”, and keeps the 30 with the largest share of essential skills in common.",
    ],
    [
      "a small pool",
      { reason: "small_pool", outcome: "found_work", pool_size: 12, pool_target: 60 },
      "Careerwright chose these from 12 occupations that match your answers closely. It aims for at least 60, but doesn't add weaker matches to get there.",
    ],
    [
      "the broader view",
      { reason: "casting_wider" },
      "Casting wider: a lower bar for relevance and one suggestion per kind of work.",
    ],
    [
      "the deeper view",
      { reason: "more_depth", family_limit: 4 },
      "Showing up to 4 from one kind of work, because you asked for more depth.",
    ],
  ])("words %s", (_, note, words) => {
    expect(slateNote(note)).toBe(words);
  });
});

describe("[DIV1-06][DIV1-03] why there are fewer than six, in words", () => {
  it.each<[string, Fewer, string]>([
    [
      "nothing found",
      { reason: "nothing_found", outcome: "found_none" },
      "None of your answers found work to suggest yet.",
    ],
    [
      "one matched",
      { reason: "few_matched", count: 1 },
      "Only 1 occupation matched your answers closely enough to suggest. Careerwright doesn't fill the rest with weaker matches.",
    ],
    [
      "three matched",
      { reason: "few_matched", count: 3 },
      "Only 3 occupations matched your answers closely enough to suggest. Careerwright doesn't fill the rest with weaker matches.",
    ],
    [
      "kinds of work already shown",
      { reason: "kinds_of_work_shown", count: 1, family_limit: 2 },
      "1 more is in kinds of work already shown 2 times; ask for more depth to see them.",
    ],
    [
      "exclusions",
      { reason: "exclusions_removed", count: 2 },
      "Your exclusions removed 2 occupations.",
    ],
    [
      "a title matched to none",
      { reason: "title_not_matched", outcome: "not_matched", title: "Registered nurse" },
      "Careerwright couldn't match “Registered nurse” to an occupation in ESCO, so it can't join other work to that title by shared skills. Choose the ESCO occupation closest to it.",
    ],
    [
      "a title matched to several",
      {
        reason: "title_matched_several",
        outcome: "matched_several",
        title: "bus operator",
        occupations: 2,
      },
      "Careerwright matched “bus operator” to 2 occupations in ESCO, so it can't join other work to that title by shared skills until you choose which one you mean.",
    ],
    // Changed by the sentence rule: "with a cook" needed an article rule for ESCO's titles;
    // the title is quoted instead, as the join's other lines do.
    [
      "a join that found nothing",
      { reason: "no_shared_occupation", outcome: "found_none", title: "cook", min_shared: 3 },
      "Careerwright found no other occupation in ESCO that shares 3 or more essential skills with “cook”.",
    ],
  ])("words %s", (_, fact, words) => {
    expect(fewerReason(fact)).toBe(words);
  });
});

describe("[REC1-05][DIV1-06] why a suggestion could suit you, in words", () => {
  it.each<[string, Reason, string]>([
    [
      "a join by shared skills",
      {
        reason: "joined_by_shared_skills",
        outcome: "found_work",
        field: "current_role",
        answer: "data analyst",
        shared: 12,
      },
      "Your current role: “data analyst”. ESCO lists 12 of the same essential skills for both, so Careerwright joined them by those skills.",
    ],
    [
      "a search through a skill",
      {
        reason: "searched_through_skill",
        outcome: "found_work",
        field: "enjoyed_tasks",
        answer: "working outdoors",
        search: "working outdoors",
        skill: "work in outdoor conditions",
      },
      "What you enjoy: “working outdoors”. Careerwright searched for “working outdoors”, and ESCO lists “work in outdoor conditions” as an essential skill for this work.",
    ],
    [
      "a title idea matched",
      {
        reason: "title_idea_matched",
        outcome: "matched",
        field: "enjoyed_tasks",
        answer: "looking after dogs",
        title: "dog groomer",
      },
      "What you enjoy: “looking after dogs”. Careerwright thought of the title “dog groomer” from it and matched that title to this occupation in ESCO.",
    ],
    [
      "the person's own title matched",
      {
        reason: "own_title_matched",
        outcome: "matched",
        field: "current_role",
        answer: "Warehouse managers",
      },
      "Your current role: “Warehouse managers”. Careerwright matched it to this occupation in ESCO.",
    ],
  ])("words %s", (_, reason, words) => {
    expect(suggestionReason(reason)).toBe(words);
  });

  const facts = (changes: Partial<SuggestionOut>) =>
    suggestionWords({
      essential_skill_count: 9,
      essential_skills: ["repair bicycles", "tune bicycles", "sell bicycles"],
      regulated: false,
      different_kind_of_work: false,
      ...changes,
    } as SuggestionOut);

  it("words what might not suit, the entry gate, a small test and what isn't researched", () => {
    expect(facts({})).toEqual({
      mightNot: [
        "ESCO lists 9 essential skills, not yet compared with your experience, including: repair bicycles, tune bicycles, sell bicycles.",
      ],
      entryGate: "Entry requirements aren't researched yet.",
      // Changed by the sentence rule: "someone who works as a bicycle mechanic" needed article
      // and plural rules for ESCO's titles; the line needs no title.
      tryIt: [
        "Talk to someone who does this work about a typical week (an informational interview).",
        "Try one of its tasks on a small scale: repair bicycles.",
      ],
      evidenceGap:
        "Pay, demand and listings in your work areas aren't researched yet. Finding no listings later would be a demand signal, not proof this work doesn't exist.",
    });
  });

  it("words a regulated profession and a different kind of work, and unknown is not regulated", () => {
    const regulated = facts({ regulated: true, different_kind_of_work: true });
    expect(regulated.mightNot.slice(1)).toEqual([
      "ESCO marks this as a regulated profession in at least one European country. Whether England requires registration isn't checked yet.",
      "It's a different kind of work from what you've told Careerwright about, so it may need new experience.",
    ]);
    expect(regulated.entryGate).toBe("Registration may be required. Not checked yet.");
    expect(facts({ regulated: null }).entryGate).toBe("Entry requirements aren't researched yet.");
    expect(facts({ essential_skills: [], essential_skill_count: 0 }).tryIt).toHaveLength(1);
  });
});

describe("[DIV1-07][AIR1-05] the hard filters and the title ideas, in words", () => {
  it("gives every count of the salary floor, so they add up", () => {
    const floor: SalaryFloorOut = {
      amount: { minor_units: 2_600_000, currency: "GBP" },
      period: "year",
      basis: "gross",
      left_out: 1,
      meets: 2,
      kept_pay_unknown: 7,
      kept_by_reason: [
        { reason: "no_reviewed_mapping", count: 3 },
        { reason: "not_published", count: 4 },
      ],
    };
    expect(floorWords(floor)).toBe(
      "Your minimum salary of £26,000 a year (gross) is applied: 1 left out because their official pay is below it; 2 meet it; 3 kept because no reviewed UK occupation code links them to pay data; 4 kept because the official figure is not published for your regions. Unknown pay is never treated as below it.",
    );
  });

  it("words the AI Resilience filter only away from its default, and a synthetic range says so", () => {
    const filter: AiResilienceFilterOut = {
      basis: "lower_bound",
      minimum: null,
      include_unscored: true,
      scored: 0,
      below_minimum: 0,
      unscored: 4,
      unscored_excluded: 0,
      synthetic: false,
      pack_version: "l0-2026-10-29",
      pack_dated: "2026-10-29",
    };
    expect(aiFilterWords(filter)).toBeNull();
    expect(aiFilterWords({ ...filter, minimum: 5, scored: 1, synthetic: true })).toBe(
      "AI Resilience Score filter, 5 or more on the lower end of each range (a synthetic fixture range here, not a real assessment): 0 left out below it; 4 unscored kept.",
    );
    expect(
      aiFilterWords({ ...filter, minimum: 3, include_unscored: false, unscored_excluded: 4 }),
    ).toBe(
      "AI Resilience Score filter, 3 or more on the lower end of each reviewed range: 0 left out below it; 4 unscored left out.",
    );
  });

  it("names the title ideas it couldn't match, and none it matched", () => {
    const idea = (title: string, outcome: SlateOut["title_ideas"][number]["outcome"]) => ({
      title,
      based_on: [],
      outcome,
      occupations: outcome === "matched" ? 1 : 0,
    });
    expect(titleIdeasWords([idea("dog groomer", "matched")])).toBeNull();
    expect(
      titleIdeasWords([idea("orbital gardener", "not_matched"), idea("dog groomer", "matched")]),
    ).toBe(
      "Titles Careerwright thought of but couldn't match to an occupation in ESCO, so not suggested: orbital gardener.",
    );
  });
});

describe("[STATE-05][PROF-10] the sketch's words and a target's coverage", () => {
  it("words a target ESCO names", () => {
    expect(RESEARCH_STATUS.esco).toBe(
      "Requirements from ESCO; not yet compared with your experience.",
    );
  });

  it("says plainly what Careerwright can do for each target", () => {
    expect(TARGET_COVERAGE.pack_target(false)).toBe(
      "Careerwright can check skills, options and routes for this role.",
    );
    expect(TARGET_COVERAGE.not_covered(true)).toBe(
      "Careerwright can show what this work usually asks for. It can't check skills, options or routes for it yet.",
    );
    expect(TARGET_COVERAGE.not_covered(false)).toBe(
      "Careerwright can't check skills, options or routes for this role yet.",
    );
  });
});
