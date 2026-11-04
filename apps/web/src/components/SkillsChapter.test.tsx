import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { SkillsOut } from "@/generated/api";
import { fakeApi, type Sent } from "@/test/fakeApi";
import { skillsData, target } from "@/test/skillsData";
import { SkillsChapter } from "./SkillsChapter";

const change = {
  version: 1,
  questions_stopped: false,
  recorded_id: "record-1",
  matrix_version: null,
  definition_version: null,
};

function shown(data: SkillsOut = skillsData): Sent[] {
  const sent = fakeApi([
    { method: "GET", path: /\/capability\/skills$/, answer: data },
    {
      method: "POST",
      path: /\/capability\/(evidence|statements|advert-spans)$/,
      status: 201,
      answer: change,
    },
    { method: "PUT", path: /\/capability\/questions\/state$/, answer: change },
    { method: "POST", path: /\/research\/pasted$/, status: 201, answer: { job: {}, claims: [] } },
  ]);
  const queries = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: Infinity } },
  });
  render(
    <QueryClientProvider client={queries}>
      <SkillsChapter workspaceId="w-skills" />
    </QueryClientProvider>,
  );
  return sent;
}

describe("[MAP1-01][PROF-13][RDY1-03] Skills reads facts without guessing readiness", () => {
  it("shows the role's requirements and expected grades as conditional, never as already shown", async () => {
    shown();
    await screen.findByRole("heading", { name: "Lab technician" });

    expect(screen.getByText("Not assessed yet. Here is what this role asks for.")).toBeVisible();
    const already = screen.getByRole("region", { name: "What you can already show" });
    expect(already).toHaveTextContent("Nothing checked yet");
    expect(already).not.toHaveTextContent("A levels");
    expect(
      within(screen.getByRole("region", { name: "What this role asks for" })).getByText(
        "Your A levels: if you get your grades.",
      ),
    ).toBeVisible();
    expect(
      screen.queryByText("Skills usual in your role, not confirmed yet"),
    ).not.toBeInTheDocument();
  });

  it("shows a marked ESCO skill as not part of the person's job, never as evidence", async () => {
    shown();
    await screen.findByRole("heading", { name: "Lab technician" });
    await userEvent.click(screen.getByText(/Skills in the European job skills list/));
    expect(screen.getByText(/operate test equipment.*not part of your job/)).toBeVisible();
    expect(screen.getByText("Not assessed yet. Here is what this role asks for.")).toBeVisible();
  });

  it("names a target outside the pack and keeps readiness unresolved", async () => {
    const data: SkillsOut = {
      ...skillsData,
      targets: [
        {
          ...target,
          pack_target: null,
          requirements: [],
          seed: "none_of_these",
          esco_listed: [],
          not_assessed_reason: "no_rubric",
        },
      ],
    };
    shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    expect(screen.getByText(/no reviewed course or role pack/)).toBeVisible();
    expect(screen.getByText(/no checked requirements for this target yet/)).toHaveTextContent(
      /Add an example advert below/,
    );
    expect(screen.queryByText(/ready now/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Review current openings" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Explore options" })).toHaveAttribute(
      "href",
      "/w/w-skills/options",
    );
  });

  it("offers current openings for a modelled ready-now result with employer checks still due", async () => {
    const data = structuredClone(skillsData);
    const chosen = data.targets[0];
    if (!chosen) throw new Error("The Skills fixture needs a target.");
    chosen.assessment_state = "assessed";
    chosen.not_assessed_reason = null;
    chosen.rubric_review = "proposed";
    chosen.readiness = {
      target_key: chosen.target_key,
      target_title: chosen.target_title,
      matrix_version: chosen.matrix_version,
      definition_version: chosen.definition_version,
      evidence_version: 1,
      pack_version: data.pack.pack_version,
      reference_version: data.reference.reference_version,
      synthetic: true,
      scenario: "current",
      completed: [],
      state: "ready_now_for_modelled_requirements",
      primary_action: "review_current_postings_and_apply",
      training_required: false,
      show_route_chart: false,
      qualifications: ["self_reported_evidence"],
      rows: [],
      blockers: [],
      gaps: [],
      actions: [],
      employer_checks: [],
      optional_development: [],
      not_modelled_rows: 0,
    };
    shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    expect(screen.getByRole("link", { name: "Review current openings" })).toHaveAttribute(
      "href",
      "/w/w-skills/roles",
    );
    expect(screen.queryByRole("link", { name: "Explore options" })).not.toBeInTheDocument();
    expect(
      screen.getByText(/has not checked a current opening or every employer requirement/),
    ).toBeVisible();
  });

  it("asks for a target when none was chosen", async () => {
    const data = { ...skillsData, targets: [] };
    shown(data);
    expect(await screen.findByRole("link", { name: "Choose a target" })).toHaveAttribute(
      "href",
      "/w/w-skills/you",
    );
  });
});

describe("[ASSESS-02][SEC-09] Skills writes only the answer the person chose", () => {
  it("labels a proposed rubric even when the question's matrix row is reviewed", async () => {
    const data = structuredClone(skillsData);
    const row = data.questions.prompts[0]?.rows[0];
    if (!row) throw new Error("The Skills fixture needs a rubric question.");
    row.review_state = "reviewed";
    shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    await userEvent.click(screen.getByLabelText("I have done this independently"));
    expect(screen.getByText("This checklist is still a draft.")).toBeVisible();
  });

  it("offers one voluntary question when coverage is enough but a prompt remains", async () => {
    const data: SkillsOut = {
      ...skillsData,
      questions: { ...skillsData.questions, state: "enough" },
    };
    shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    expect(screen.getByText(/You have answered enough for now/)).toBeVisible();
    const summary = screen.getByText("Answer another question");
    expect(summary.closest("details")).not.toHaveAttribute("open");
    await userEvent.click(summary);
    expect(summary.closest("details")).toHaveAttribute("open");
    expect(screen.getAllByRole("form", { name: "One skills question" })).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Save answer" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Pause questions" })).not.toBeInTheDocument();
  });

  it("does not offer another question when no prompts remain", async () => {
    const data: SkillsOut = {
      ...skillsData,
      questions: { ...skillsData.questions, state: "enough", prompts: [], initial: [] },
    };
    shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    expect(screen.queryByText("Answer another question")).not.toBeInTheDocument();
  });

  it("sends a self assessment against the shown rubric and current version", async () => {
    const sent = shown();
    await screen.findByRole("heading", { name: "Lab technician" });
    await userEvent.click(screen.getByLabelText("I have done this independently"));
    await userEvent.selectOptions(
      screen.getByLabelText("Which description matches what you did?"),
      "2",
    );
    await userEvent.type(
      screen.getByLabelText("An example, in your words"),
      "I prepared samples on my placement.",
    );
    await userEvent.type(screen.getByLabelText("When did you last do this?"), "2026-10");
    await userEvent.click(screen.getByRole("button", { name: "Save answer" }));
    await waitFor(() =>
      expect(sent.some((request) => request.path.endsWith("/capability/evidence"))).toBe(true),
    );
    expect(
      sent.find((request) => request.path.endsWith("/capability/evidence"))?.body,
    ).toMatchObject({
      expected_version: 0,
      subject: "samples",
      answer: "done_independently",
      rubric_version: "rubric-1",
      self_assessed_level: 2,
      example: "I prepared samples on my placement.",
      last_done: "2026-10",
    });
  });

  it("keeps an unknown registration visible with a way to change it and its source", async () => {
    const data = structuredClone(skillsData);
    const row = data.targets[0]?.requirements[0];
    if (!row) throw new Error("The Skills fixture needs a requirement.");
    row.latest_holding = "unknown";
    row.source_urls = ["https://example.org/registration-advert"];
    row.gate = {
      gate_key: "nmc-registration",
      kind: "legal_practice",
      protected: true,
      modelled: true,
      label: "NMC registration",
      issuing_body: "Nursing and Midwifery Council (NMC)",
      jurisdiction: "GB",
      verification: "Your own entry on the NMC register",
      acceptable_proof: ["register entry"],
      notes: [],
    };
    data.questions.state = "only_unresolved";
    data.questions.prompts = [];
    data.questions.initial = [];
    const sent = shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    expect(screen.getByRole("link", { name: "Check the NMC register" })).toHaveAttribute(
      "href",
      "https://www.nmc.org.uk/registration/search-the-register/",
    );
    expect(screen.getByRole("link", { name: "Source advert" })).toHaveAttribute(
      "href",
      "https://example.org/registration-advert",
    );
    await userEvent.click(screen.getByText("Change your answer"));
    expect(screen.getByLabelText("Not sure")).toBeChecked();
    await userEvent.click(screen.getByLabelText("Not yet"));
    await userEvent.click(screen.getByRole("button", { name: "Save changed answer" }));
    await waitFor(() =>
      expect(sent.some((request) => request.path.endsWith("/capability/statements"))).toBe(true),
    );
    expect(
      sent.find((request) => request.path.endsWith("/capability/statements"))?.body,
    ).toMatchObject({ subject: "levels:lab", holding: "not_held", verified: false });
  });

  it("does not save a skill without an answer or a level against its checklist", async () => {
    const sent = shown();
    await screen.findByRole("heading", { name: "Lab technician" });
    await userEvent.click(screen.getByRole("button", { name: "Save answer" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Choose what you have done so far.");
    await userEvent.click(screen.getByLabelText("I have done this independently"));
    await userEvent.click(screen.getByRole("button", { name: "Save answer" }));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Choose the description that matches what you have done.",
    );
    await userEvent.selectOptions(
      screen.getByLabelText("Which description matches what you did?"),
      "2",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save answer" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Give a concrete example of what you did.");
    await userEvent.type(screen.getByLabelText("An example, in your words"), "Prepared samples.");
    await userEvent.click(screen.getByRole("button", { name: "Save answer" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Choose when you last did this.");
    expect(sent.filter((request) => request.method === "POST")).toHaveLength(0);
  });

  it("keeps the shown rubric when a person changes a skill answer to unsure", async () => {
    const sent = shown();
    await screen.findByRole("heading", { name: "Lab technician" });
    await userEvent.click(screen.getByLabelText("I am not sure"));
    await userEvent.click(screen.getByRole("button", { name: "Save answer" }));
    await waitFor(() =>
      expect(sent.some((request) => request.path.endsWith("/capability/evidence"))).toBe(true),
    );
    expect(
      sent.find((request) => request.path.endsWith("/capability/evidence"))?.body,
    ).toMatchObject({ subject: "samples", answer: "unsure", rubric_version: "rubric-1" });
  });

  it("lets a returning person correct a saved skill level to unsure", async () => {
    const data = structuredClone(skillsData);
    const row = data.targets[0]?.requirements[1];
    if (!row) throw new Error("The Skills fixture needs a modelled skill.");
    row.latest_skill = {
      answer: "done_independently",
      self_assessed_level: 2,
      example: "I prepared samples on placement.",
      last_done: "2026-10",
    };
    data.questions = { ...data.questions, state: "enough", prompts: [], initial: [] };
    const sent = shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    await userEvent.click(screen.getByText("Correct your skill answer"));
    const correction = screen.getByRole("form", { name: "Correct your skill answer" });
    expect(within(correction).getByLabelText("I have done this independently")).toBeChecked();
    expect(within(correction).getByLabelText("An example, in your words")).toHaveValue(
      "I prepared samples on placement.",
    );
    await userEvent.click(within(correction).getByLabelText("I am not sure"));
    await userEvent.click(within(correction).getByRole("button", { name: "Save correction" }));
    await waitFor(() =>
      expect(sent.some((request) => request.path.endsWith("/capability/evidence"))).toBe(true),
    );
    expect(
      sent.find((request) => request.path.endsWith("/capability/evidence"))?.body,
    ).toMatchObject({
      subject: "samples",
      answer: "unsure",
      rubric_version: "rubric-1",
      self_assessed_level: null,
      example: null,
      last_done: null,
    });
  });

  it("saves a protected requirement as held only when the person says they checked its source", async () => {
    const data = structuredClone(skillsData);
    const gate = {
      gate_key: "gate-1",
      kind: "legal_practice" as const,
      protected: true as const,
      modelled: true,
      label: "Registration",
      issuing_body: "NMC",
      jurisdiction: "England",
      verification: "Register",
      acceptable_proof: ["register entry"],
    };
    const firstTarget = data.targets[0];
    const firstRequirement = firstTarget?.requirements[0];
    const firstPrompt = data.questions.prompts[0];
    if (!firstRequirement || !firstPrompt)
      throw new Error("The Skills fixture needs a requirement and a question.");
    firstRequirement.gate = gate;
    data.questions.prompts = [
      {
        ...firstPrompt,
        prompt_id: "question-gate",
        kind: "requirement",
        subject: "levels:lab",
        label: "Registration",
        rows: [],
        gate,
      },
    ];
    data.questions.initial = ["question-gate"];
    const sent = shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    await userEvent.click(screen.getByLabelText("Yes"));
    await userEvent.click(screen.getByLabelText("I checked this at its source"));
    await userEvent.type(
      screen.getByLabelText("Where did you check it? (optional)"),
      "NMC register",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save answer" }));
    await waitFor(() =>
      expect(sent.some((request) => request.path.endsWith("/capability/statements"))).toBe(true),
    );
    expect(
      sent.find((request) => request.path.endsWith("/capability/statements"))?.body,
    ).toMatchObject({
      expected_version: 0,
      subject: "levels:lab",
      holding: "held",
      verified: true,
      verification_note: "NMC register",
    });
  });

  it("keeps the advert's chosen UTF-16 spans and adds only selected words", async () => {
    const data = structuredClone(skillsData);
    const example = data.targets[0]?.examples[0];
    if (!example) throw new Error("The Skills fixture needs an example advert.");
    example.text = "🧪 Three A levels or equivalent. Prepare samples safely.";
    example.spans = [];
    const sent = shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    await userEvent.click(screen.getByText("Example advert for Lab technician"));
    const box = screen.getByLabelText("Select the words to keep") as HTMLTextAreaElement;
    const start = example.text.indexOf("Prepare samples");
    act(() => box.setSelectionRange(start, start + "Prepare samples".length));
    await userEvent.click(screen.getByRole("button", { name: "Keep selected words" }));
    await waitFor(() =>
      expect(sent.some((request) => request.path.endsWith("/capability/advert-spans"))).toBe(true),
    );
    expect(
      sent.find((request) => request.path.endsWith("/capability/advert-spans"))?.body,
    ).toMatchObject({
      expected_version: 0,
      target: "Lab technician",
      job_id: "job-1",
      spans: [{ start, end: start + 15 }],
    });
  });
});

describe("[MAP1-01][RDY1-03] Skills connects requirements to saved evidence", () => {
  it("shows a saved example as the person's answer without marking the requirement met", async () => {
    const data = structuredClone(skillsData);
    const requirement = data.targets[0]?.requirements[1];
    if (!requirement) throw new Error("The Skills fixture needs a skill requirement.");
    requirement.latest_skill = {
      answer: "done_independently",
      self_assessed_level: 2,
      example: "I prepared samples on placement.",
      last_done: "2026-10",
    };
    shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    expect(screen.getByText("Self-reported evidence")).toBeVisible();
    const landscape = within(
      screen.getByRole("complementary", { name: "Your evidence, connected" }),
    );
    expect(
      landscape.getByRole("link", { name: /Prepare samples safely Your answer, not verified/ }),
    ).toBeVisible();
    await userEvent.click(screen.getByText("Read your saved example"));
    expect(
      screen.getByText("I prepared samples on placement.", { selector: "blockquote" }),
    ).toBeVisible();
    expect(screen.getByRole("region", { name: "What you can already show" })).toHaveTextContent(
      "Nothing checked yet",
    );
    expect(screen.getByText("Last used: October 2026.")).toBeVisible();
  });

  it("opens a hidden requirement, focuses its evidence and keeps its branch selected until another is inspected", async () => {
    const data = structuredClone(skillsData);
    const selected = data.targets[0];
    const original = selected?.requirements[0];
    if (!selected || !original) throw new Error("The Skills fixture needs a requirement.");
    selected.requirements.push(
      { ...original, row_id: "third", label: "Third requirement" },
      { ...original, row_id: "fourth", label: "Fourth requirement" },
    );
    shown(data);
    await screen.findByRole("heading", { name: "Lab technician" });
    const details = screen.getByText("See all 4 requirements").closest("details");
    expect(details).not.toHaveAttribute("open");
    const landscape = within(
      screen.getByRole("complementary", { name: "Your evidence, connected" }),
    );
    const fourth = landscape.getByRole("link", { name: /Fourth requirement/ });
    const third = landscape.getByRole("link", { name: /Third requirement/ });
    expect(landscape.queryByRole("link", { current: true })).not.toBeInTheDocument();
    await userEvent.click(fourth);
    expect(details).toHaveAttribute("open");
    expect(document.getElementById("skill-row-fourth")).toHaveFocus();
    expect(fourth).not.toHaveFocus();
    expect(fourth).toHaveAttribute("aria-current", "true");
    await userEvent.click(third);
    expect(document.getElementById("skill-row-third")).toHaveFocus();
    expect(third).toHaveAttribute("aria-current", "true");
    expect(fourth).not.toHaveAttribute("aria-current");
  });
});
