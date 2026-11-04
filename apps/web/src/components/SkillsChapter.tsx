"use client";

import Link from "next/link";
import { type FormEvent, type ReactNode, useEffect, useRef, useState } from "react";
import type {
  AdvertExample,
  Answer,
  EntryFact,
  Holding,
  Prompt,
  Qualification,
  ReadinessState,
  Requirement,
  RowStatus,
  SkillsOut,
  TargetSkills,
} from "@/generated/api";
import { chapterHref } from "@/lib/chapters";
import { formatMonth } from "@/lib/dates";
import {
  useChooseAdvertParts,
  usePasteExample,
  useRecordRequirement,
  useRecordSkill,
  useSetSkillQuestions,
  useSkills,
} from "@/lib/skillQueries";
import { Button } from "./Button";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";

const date = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${iso.slice(0, 10)}T12:00:00Z`));

const readinessWords: Record<ReadinessState, string> = {
  ready_now_for_modelled_requirements:
    "Careerwright found the modelled requirements met. Employers may ask for more.",
  conditional_on_assessed_completion:
    "Ready if you complete and pass the assessed step shown below.",
  not_ready: "Careerwright found requirements still to meet.",
  not_yet_assessed: "Not assessed yet. Here is what this role asks for.",
  insufficient_coverage:
    "Too little checked information to say you are ready. Review the requirements below and confirm them with an employer.",
};

const statusWords: Record<RowStatus, string> = {
  met: "You can show this",
  satisfied: "You can show this",
  below_required: "More to show",
  no_usable_evidence: "Not shown yet",
  not_modelled: "Not checked in this model",
  not_held: "Not held yet",
  unresolved: "Not known yet",
  pathway_outside_model: "Beyond the planning model",
  no_modelled_requirements: "Not checked in this model",
};

const qualificationWords: Record<Qualification, string> = {
  provisional_matrix: "The role's requirements are provisional.",
  proposed_records: "Some source records are not reviewed yet.",
  proposed_rubrics: "Some skill checklists are still drafts.",
  self_reported_evidence: "Some evidence is what you told Careerwright.",
  planned_outcome_assumption: "A planned course outcome has not happened yet.",
  user_assumption: "This uses a figure or condition you supplied.",
  missing_outcome_level: "A course outcome does not say what level it reaches.",
  person_confirmed_demonstration: "You confirmed a demonstration; no assessor reviewed it here.",
  person_confirmed_verification:
    "You confirmed a check at its source; Careerwright did not check it.",
  open_conflict: "Two pieces of evidence disagree; this remains unresolved.",
};

function entryWords(fact: EntryFact): string {
  switch (fact.standing) {
    case "expected_not_met":
      return `Your ${fact.qualification}: if you get your grades.`;
    case "achieved_unverified":
      return `Your ${fact.qualification}: you said you have it. Careerwright has not checked it at its source.`;
    case "achieved_stated":
      return `Your ${fact.qualification}: you said you have it.`;
  }
}

function RequirementLine({
  requirement,
  target,
  data,
  workspaceId,
}: {
  requirement: Requirement;
  target: TargetSkills;
  data: SkillsOut;
  workspaceId: string;
}) {
  const row = target.readiness?.rows.find((item) => item.row_id === requirement.row_id);
  const answer = requirement.latest_skill;
  const reported =
    answer && ["done_independently", "done_with_help", "used"].includes(answer.answer);
  return (
    <li
      className="decision-skill-row grid gap-8"
      id={`skill-row-${requirement.row_id}`}
      tabIndex={-1}
    >
      <strong>{requirement.label}</strong>
      {reported && (
        <span className="decision-evidence-label decision-self-reported">
          Self-reported evidence
        </span>
      )}
      {answer?.answer === "not_learned" && (
        <p className="small">You said you have not learned this yet.</p>
      )}
      {reported && (
        <details className="decision-disclosure">
          <summary>Read your saved example</summary>
          <blockquote>{answer.example ?? "No example saved."}</blockquote>
          {answer.last_done && (
            <p className="small">Last used: {formatMonth(`${answer.last_done}-01`)}.</p>
          )}
          <p className="small muted">Your own answer; not independently verified.</p>
        </details>
      )}
      {row !== undefined && <span className="small">{statusWords[row.status]}</span>}
      {row === undefined && !reported && <span className="small muted">Not known yet</span>}
      {requirement.gate?.protected && <span className="small">Must be checked at its source.</span>}
      {requirement.gate?.gate_key === "nmc-registration" && (
        <a
          href="https://www.nmc.org.uk/registration/search-the-register/"
          target="_blank"
          rel="noopener noreferrer"
          className="small"
        >
          Check the NMC register
        </a>
      )}
      {requirement.entry_facts.map((fact) => (
        <span key={`${fact.qualification}-${fact.standing}`} className="small">
          {entryWords(fact)}
        </span>
      ))}
      <details className="place-more">
        <summary>Why Careerwright shows this</summary>
        <p className="small">
          {requirement.review_state === "reviewed" ? "Reviewed" : "Not reviewed yet"}
          {requirement.as_of === null ? "." : ` from its page on ${date(requirement.as_of)}.`}
          {requirement.employer_specific && " This may vary by employer."}
        </p>
        {row?.evidence !== null && row?.evidence !== undefined && (
          <p className="small">
            {row.evidence.basis === "demonstrated"
              ? "A demonstration you confirmed"
              : row.evidence.basis === "self_reported"
                ? "Your own answer"
                : "No usable evidence yet"}
            {row.evidence.level === null ? "." : `, level ${row.evidence.level} on this checklist.`}
          </p>
        )}
        {requirement.source_urls.map((url, index) => (
          <p key={url} className="small">
            <a href={url} target="_blank" rel="noopener noreferrer nofollow">
              {requirement.source_urls.length === 1
                ? "Source advert"
                : `Source advert ${index + 1}`}
            </a>
          </p>
        ))}
      </details>
      {requirement.latest_holding !== null && (
        <details className="place-more">
          <summary>Change your answer</summary>
          <RequirementRevision
            requirement={requirement}
            evidenceVersion={data.questions.evidence_version}
            workspaceId={workspaceId}
          />
        </details>
      )}
      {requirement.latest_skill !== null && (
        <details className="place-more">
          <summary>Correct your skill answer</summary>
          <p className="small pt-12">
            This is your saved answer. Careerwright has not verified it.
          </p>
          <QuestionCard
            key={`${requirement.row_id}-${data.questions.evidence_version}`}
            prompt={requirement}
            data={data}
            workspaceId={workspaceId}
          />
        </details>
      )}
    </li>
  );
}

function RequirementRevision({
  requirement,
  evidenceVersion,
  workspaceId,
}: {
  requirement: Requirement;
  evidenceVersion: number;
  workspaceId: string;
}) {
  const record = useRecordRequirement(workspaceId);
  const [holding, setHolding] = useState<Holding>(requirement.latest_holding ?? "unknown");
  const [verified, setVerified] = useState(false);
  return (
    <form
      className="grid gap-8 pt-12"
      onSubmit={(event) => {
        event.preventDefault();
        record.mutate({
          expected_version: evidenceVersion,
          subject: requirement.subject,
          holding,
          verified: holding === "held" && verified,
        });
      }}
    >
      <fieldset className="grid gap-4">
        <legend className="small">Do you have this?</legend>
        {(
          [
            ["held", "Yes"],
            ["not_held", "Not yet"],
            ["unknown", "Not sure"],
          ] as const
        ).map(([value, label]) => (
          <label key={value} className="flex items-center gap-8">
            <input
              type="radio"
              name={`revise-${requirement.row_id}`}
              checked={holding === value}
              onChange={() => setHolding(value)}
            />
            {label}
          </label>
        ))}
      </fieldset>
      {holding === "held" && requirement.gate !== null && (
        <label className="flex items-center gap-8">
          <input
            type="checkbox"
            checked={verified}
            onChange={(event) => setVerified(event.target.checked)}
          />
          I checked this at its source
        </label>
      )}
      {record.error !== null && <RequestFailure error={record.error} />}
      <div>
        <Button
          type="submit"
          variant="secondary"
          disabledReason={record.isPending ? "Saving…" : undefined}
        >
          Save changed answer
        </Button>
      </div>
    </form>
  );
}

function TargetView({
  target,
  data,
  workspaceId,
  selectedRow,
  nextQuestion,
}: {
  target: TargetSkills;
  data: SkillsOut;
  workspaceId: string;
  selectedRow: string | null;
  nextQuestion: ReactNode;
}) {
  const first = target.requirements.slice(0, 3);
  const rest = target.requirements.slice(3);
  const canShow =
    target.readiness?.rows.filter((row) => row.status === "met" || row.status === "satisfied") ??
    [];
  const readyToApply =
    target.assessment_state === "assessed" &&
    target.readiness?.state === "ready_now_for_modelled_requirements" &&
    target.readiness.primary_action === "review_current_postings_and_apply" &&
    !target.readiness.training_required;
  return (
    <section className="grid gap-16" aria-labelledby="skills-target">
      <div className="grid gap-8">
        <h2 id="skills-target" className="display text-25">
          {target.target_title}
        </h2>
        <p>
          {target.assessment_state === "not_assessed" || target.readiness === null
            ? "Not assessed yet. Here is what this role asks for."
            : readinessWords[target.readiness.state]}
        </p>
        {readyToApply ? (
          <div className="grid gap-8">
            <p className="small">
              Careerwright has not checked a current opening or every employer requirement. Review
              each opening at its source before applying.
            </p>
            <div>
              <Link className="btn btn-primary" href={chapterHref(workspaceId, "roles")}>
                Review current openings
              </Link>
            </div>
          </div>
        ) : (
          <div>
            <Link className="btn btn-secondary" href={chapterHref(workspaceId, "options")}>
              Explore options
            </Link>
          </div>
        )}
        {target.rubric_review === "proposed" && (
          <p className="small muted">This result uses a draft skill checklist.</p>
        )}
        {target.pack_target === null && (
          <p className="small muted">
            Careerwright has no reviewed course or role pack for this target yet.
          </p>
        )}
        {target.readiness !== null && target.readiness.qualifications.length > 0 && (
          <details className="place-more">
            <summary>What this result rests on</summary>
            <ul className="grid gap-4 pt-12">
              {target.readiness.qualifications.map((reason) => (
                <li key={reason} className="small">
                  {qualificationWords[reason]}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
      {nextQuestion}
      {target.readiness?.qualifications.includes("planned_outcome_assumption") && (
        <div className="decision-caution">
          <strong>Planned learning is still an assumption</strong>
          <p>
            A course outcome only counts in a future scenario. It has not changed your current
            evidence.
          </p>
        </div>
      )}
      <section className="grid gap-8" aria-labelledby="skills-can-show">
        <h3 id="skills-can-show" className="section-title">
          What you can already show
        </h3>
        {canShow.length > 0 ? (
          <ul className="grid gap-4">
            {canShow.map((row) => (
              <li key={row.row_id}>{row.label}</li>
            ))}
          </ul>
        ) : (
          <p className="small muted">
            Nothing checked yet. An unanswered requirement stays unknown.
          </p>
        )}
      </section>
      <section className="grid gap-12" aria-labelledby="skills-asks">
        <h3 id="skills-asks" className="section-title">
          What this role asks for
        </h3>
        {target.requirements.length === 0 ? (
          <p className="small">
            Careerwright has no checked requirements for this target yet. Add an example advert
            below to keep what an employer asks for beside your answers.
          </p>
        ) : (
          <>
            <ul className="grid gap-8">
              {first.map((row) => (
                <RequirementLine
                  key={row.row_id}
                  requirement={row}
                  target={target}
                  data={data}
                  workspaceId={workspaceId}
                />
              ))}
            </ul>
            {rest.length > 0 && (
              <details
                className="place-more"
                open={rest.some((row) => row.row_id === selectedRow) || undefined}
              >
                <summary>See all {target.requirements.length} requirements</summary>
                <ul className="grid gap-8 pt-12">
                  {rest.map((row) => (
                    <RequirementLine
                      key={row.row_id}
                      requirement={row}
                      target={target}
                      data={data}
                      workspaceId={workspaceId}
                    />
                  ))}
                </ul>
              </details>
            )}
          </>
        )}
      </section>
      {target.esco_listed.length > 0 && (
        <details className="place-more">
          <summary>
            Skills in the European job skills list, ESCO ({target.esco_listed.length})
          </summary>
          <ul className="grid gap-8 pt-12">
            {target.esco_listed.map((skill) => (
              <li key={skill.skill_id} className="small">
                {skill.label} ({skill.relation})
                {skill.not_part_of_job && ": you marked this not part of your job"}
              </li>
            ))}
          </ul>
        </details>
      )}
      {target.examples.length > 0 && (
        <section className="grid gap-8" aria-labelledby="skills-examples">
          <h3 id="skills-examples" className="section-title">
            Your example adverts
          </h3>
          <p className="small muted">
            Choose the words that say what this role asks for. Careerwright keeps your selection as
            your own example.
          </p>
          {target.examples.map((example) => (
            <AdvertParts
              key={example.job_id}
              example={example}
              target={target}
              version={data.version}
              workspaceId={workspaceId}
            />
          ))}
        </section>
      )}
      {target.examples.length < 3 && <AddAdvert target={target} workspaceId={workspaceId} />}
    </section>
  );
}

function AddAdvert({ target, workspaceId }: { target: TargetSkills; workspaceId: string }) {
  const paste = usePasteExample(workspaceId);
  const [text, setText] = useState("");
  const [problem, setProblem] = useState<string | null>(null);
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setProblem(null);
    if (text.trim() === "") return setProblem("Paste the advert's words first.");
    paste.mutate(
      { target: target.target_title, title: `Example advert for ${target.target_title}`, text },
      { onSuccess: () => setText("") },
    );
  };
  return (
    <details className="place-more">
      <summary>Add your own example advert</summary>
      <form className="grid gap-8 pt-12" onSubmit={submit}>
        <label className="grid gap-4">
          <span className="small">Paste the advert's words</span>
          <textarea
            className="input"
            rows={6}
            maxLength={50000}
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        </label>
        <p className="small muted">Careerwright keeps this as your own unreviewed example.</p>
        {problem !== null && <p role="alert">{problem}</p>}
        {paste.error !== null && <RequestFailure error={paste.error} />}
        <div>
          <Button
            variant="secondary"
            type="submit"
            disabledReason={paste.isPending ? "Saving…" : undefined}
          >
            Save example
          </Button>
        </div>
      </form>
    </details>
  );
}

function AdvertParts({
  example,
  target,
  version,
  workspaceId,
}: {
  example: AdvertExample;
  target: TargetSkills;
  version: number;
  workspaceId: string;
}) {
  const box = useRef<HTMLTextAreaElement>(null);
  const choose = useChooseAdvertParts(workspaceId);
  const [problem, setProblem] = useState<string | null>(null);
  const save = (spans: { start: number; end: number }[]) => {
    setProblem(null);
    choose.mutate({
      expected_version: version,
      target: target.target_title,
      job_id: example.job_id,
      spans,
    });
  };
  const add = () => {
    const start = box.current?.selectionStart ?? 0;
    const end = box.current?.selectionEnd ?? 0;
    if (start === end || example.text.slice(start, end).trim() === "")
      return setProblem("Select words in the advert first.");
    if (Array.from(example.text.slice(start, end)).length > 600)
      return setProblem("Choose no more than 600 characters at once.");
    if (example.spans.length >= 12)
      return setProblem("You can choose up to 12 parts of this advert.");
    if (example.spans.some((part) => start < part.end && end > part.start))
      return setProblem("These words overlap a part you already chose.");
    save(
      [
        ...example.spans.map(({ start: from, end: to }) => ({ start: from, end: to })),
        { start, end },
      ].sort((a, b) => a.start - b.start),
    );
  };
  return (
    <details className="card place-more">
      <summary>
        {example.title ?? "Your example advert"}
        {example.employer && `, ${example.employer}`}
      </summary>
      <div className="grid gap-8 pt-12">
        <label className="grid gap-4">
          <span className="small">Select the words to keep</span>
          <textarea ref={box} className="input" readOnly value={example.text} rows={7} />
        </label>
        <div>
          <Button
            variant="secondary"
            onClick={add}
            disabledReason={choose.isPending ? "Saving…" : undefined}
          >
            Keep selected words
          </Button>
        </div>
        {problem !== null && <p role="alert">{problem}</p>}
        {choose.error !== null && <RequestFailure error={choose.error} />}
        {example.spans.length > 0 && (
          <ul className="grid gap-8">
            {example.spans.map((part) => (
              <li key={`${part.start}-${part.end}`} className="grid gap-4">
                <blockquote>“{part.excerpt}”</blockquote>
                {part.entry_facts.map((fact) => (
                  <p key={fact.qualification} className="small">
                    {entryWords(fact)}
                  </p>
                ))}
                <div>
                  <Button
                    variant="quiet"
                    onClick={() =>
                      save(
                        example.spans
                          .filter((other) => other !== part)
                          .map(({ start, end }) => ({ start, end })),
                      )
                    }
                    disabledReason={choose.isPending ? "Saving…" : undefined}
                  >
                    Remove this part
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </details>
  );
}

function UsualSkills({ data, workspaceId }: { data: SkillsOut; workspaceId: string }) {
  const record = useRecordSkill(workspaceId);
  const usual = data.usual_in_role;
  if (usual === null) return null;
  return (
    <details className="place-more">
      <summary>Skills usual in your role, not confirmed yet</summary>
      <div className="grid gap-8 pt-12">
        <p className="small">
          ESCO lists these for {usual.occupation_label}. Careerwright has not treated them as skills
          you have.
        </p>
        <ul className="grid gap-8">
          {usual.skills.map((skill) => (
            <li key={skill.skill_id} className="card grid gap-4">
              <strong>{skill.label}</strong>
              <span className="small">
                {skill.not_part_of_job
                  ? "You marked this not part of your job."
                  : skill.state === "self_reported"
                    ? "You said you have used this."
                    : "Usual in this role, not confirmed yet."}
              </span>
              {skill.state !== "self_reported" && !skill.not_part_of_job && (
                <div>
                  <Button
                    variant="secondary"
                    onClick={() =>
                      record.mutate({
                        expected_version: data.version,
                        subject: skill.subject,
                        answer: "used",
                      })
                    }
                    disabledReason={record.isPending ? "Saving…" : undefined}
                  >
                    I've used this
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ul>
        {record.error !== null && <RequestFailure error={record.error} />}
      </div>
    </details>
  );
}

const ANSWERS: readonly { value: Answer; label: string }[] = [
  { value: "done_independently", label: "I have done this independently" },
  { value: "done_with_help", label: "I have done this with help" },
  { value: "understand_not_tried", label: "I understand it but have not tried it" },
  { value: "not_learned", label: "I have not learned it yet" },
  { value: "unsure", label: "I am not sure" },
];

function QuestionCard({
  prompt,
  data,
  workspaceId,
}: {
  prompt: Prompt | Requirement;
  data: SkillsOut;
  workspaceId: string;
}) {
  const saved = "latest_skill" in prompt ? prompt.latest_skill : null;
  const promptId = "prompt_id" in prompt ? prompt.prompt_id : prompt.row_id;
  const skill = useRecordSkill(workspaceId);
  const requirement = useRecordRequirement(workspaceId);
  const [answer, setAnswer] = useState<Answer | null>(saved?.answer ?? null);
  const [holding, setHolding] = useState<Holding | null>(null);
  const [verified, setVerified] = useState(false);
  const [level, setLevel] = useState(saved?.self_assessed_level?.toString() ?? "");
  const [example, setExample] = useState(saved?.example ?? "");
  const [lastDone, setLastDone] = useState(saved?.last_done ?? "");
  const [verificationNote, setVerificationNote] = useState("");
  const [problem, setProblem] = useState<string | null>(null);
  const shownRubric =
    "rows" in prompt ? prompt.rows.find((row) => row.rubric_version !== null) : undefined;
  const rubric =
    shownRubric ??
    ("rubric_anchors" in prompt && prompt.rubric_version !== null
      ? { rubric_version: prompt.rubric_version, anchors: prompt.rubric_anchors }
      : undefined);
  const draftRubric = shownRubric
    ? data.targets
        .find((target) => target.target_key === shownRubric.target_key)
        ?.requirements.some(
          (row) =>
            row.row_id === shownRubric.row_id &&
            row.rubric_version === shownRubric.rubric_version &&
            row.rubric_review_state === "proposed",
        )
    : "rubric_review_state" in prompt && prompt.rubric_review_state === "proposed";
  const performed = answer === "done_independently" || answer === "done_with_help";
  const anchors = Object.entries(rubric?.anchors ?? {}).filter(([number]) => {
    const n = Number(number);
    return n > 0 && (answer !== "done_with_help" || n <= 1);
  });
  const saving = skill.isPending || requirement.isPending;
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setProblem(null);
    if (prompt.kind === "requirement") {
      if (holding === null) return setProblem("Choose what you know about this requirement.");
      requirement.mutate({
        expected_version: data.questions.evidence_version,
        subject: prompt.subject,
        holding,
        verified: holding === "held" && verified,
        verification_note: holding === "held" && verified ? verificationNote.trim() || null : null,
      });
      return;
    }
    if (answer === null) return setProblem("Choose what you have done so far.");
    if (performed && anchors.length > 0 && level === "")
      return setProblem("Choose the description that matches what you have done.");
    if (performed && anchors.length > 0 && example.trim() === "")
      return setProblem("Give a concrete example of what you did.");
    if (performed && anchors.length > 0 && lastDone === "")
      return setProblem("Choose when you last did this.");
    skill.mutate({
      expected_version: data.questions.evidence_version,
      subject: prompt.subject,
      answer,
      rubric_version: rubric?.rubric_version ?? null,
      self_assessed_level: performed && level !== "" ? Number(level) : null,
      example: performed ? example.trim() || null : null,
      last_done: performed && lastDone !== "" ? lastDone : null,
    });
  };

  return (
    <form
      className="card grid gap-12"
      onSubmit={submit}
      aria-label={saved ? "Correct your skill answer" : "One skills question"}
    >
      <h3 className="section-title">{prompt.label}</h3>
      {"rows" in prompt && prompt.rows.length > 1 && (
        <p className="small muted">This answer can help with more than one target.</p>
      )}
      {prompt.kind === "requirement" ? (
        <>
          <fieldset className="grid gap-8">
            <legend className="small">Do you have this?</legend>
            {(
              [
                ["held", "Yes"],
                ["not_held", "Not yet"],
                ["unknown", "Not sure"],
              ] as const
            ).map(([value, label]) => (
              <label key={value} className="flex items-center gap-8">
                <input
                  type="radio"
                  name={`holding-${promptId}`}
                  checked={holding === value}
                  onChange={() => setHolding(value)}
                />
                {label}
              </label>
            ))}
          </fieldset>
          {holding === "held" && prompt.gate !== null && (
            <label className="flex items-center gap-8">
              <input
                type="checkbox"
                checked={verified}
                onChange={(event) => setVerified(event.target.checked)}
              />
              I checked this at its source
            </label>
          )}
          {holding === "held" && verified && (
            <label className="grid gap-4">
              <span className="small">Where did you check it? (optional)</span>
              <input
                className="input"
                maxLength={300}
                value={verificationNote}
                onChange={(event) => setVerificationNote(event.target.value)}
              />
            </label>
          )}
        </>
      ) : (
        <>
          <fieldset className="grid gap-8">
            <legend className="small">What have you done?</legend>
            {ANSWERS.map(({ value, label }) => (
              <label key={value} className="flex items-center gap-8">
                <input
                  type="radio"
                  name={`answer-${promptId}`}
                  checked={answer === value}
                  onChange={() => {
                    setAnswer(value);
                    setLevel("");
                  }}
                />
                {label}
              </label>
            ))}
          </fieldset>
          {performed && anchors.length > 0 && (
            <div className="grid gap-4">
              <label htmlFor={`skill-level-${promptId}`} className="small">
                Which description matches what you did?
              </label>
              <select
                id={`skill-level-${promptId}`}
                className="input"
                value={level}
                onChange={(event) => setLevel(event.target.value)}
              >
                <option value="">Choose a description</option>
                {anchors.map(([number, words]) => (
                  <option key={number} value={number}>
                    {words}
                  </option>
                ))}
              </select>
              {draftRubric && <span className="small muted">This checklist is still a draft.</span>}
            </div>
          )}
          {performed && anchors.length === 0 && (
            <p className="small muted">
              Careerwright has no level description for this skill yet. Your answer stays your own
              statement.
            </p>
          )}
          {performed && (
            <label className="grid gap-4">
              <span className="small">
                An example, in your words {anchors.length > 0 ? "" : "(optional)"}
              </span>
              <textarea
                className="input"
                maxLength={1000}
                value={example}
                onChange={(event) => setExample(event.target.value)}
              />
            </label>
          )}
          {performed && anchors.length > 0 && (
            <label className="grid gap-4">
              <span className="small">When did you last do this?</span>
              <input
                className="input"
                type="month"
                max={new Date().toISOString().slice(0, 7)}
                value={lastDone}
                onChange={(event) => setLastDone(event.target.value)}
              />
            </label>
          )}
        </>
      )}
      {problem !== null && <p role="alert">{problem}</p>}
      {(skill.error !== null || requirement.error !== null) && (
        <RequestFailure error={skill.error ?? requirement.error} />
      )}
      <div>
        <Button variant="primary" type="submit" disabledReason={saving ? "Saving…" : undefined}>
          {saved ? "Save correction" : "Save answer"}
        </Button>
      </div>
    </form>
  );
}

function SkillsLandscape({
  target,
  selectedRow,
  onInspect,
}: {
  target: TargetSkills;
  selectedRow: string | null;
  onInspect(row: string): void;
}) {
  return (
    <aside className="chapter-landscape skills-landscape" aria-labelledby="skills-landscape-title">
      <header className="chapter-heading">
        <h2 id="skills-landscape-title">Your evidence, connected</h2>
        <p>Each branch is a requirement for this target. Open one to review your answer.</p>
      </header>
      <div className="skill-path">
        <div className="skill-path-origin">
          <span aria-hidden="true" />
          Your answers
        </div>
        <ul className="skill-path-requirements">
          {target.requirements.map((requirement) => {
            const row = target.readiness?.rows.find((item) => item.row_id === requirement.row_id);
            const reported =
              requirement.latest_skill &&
              ["done_independently", "done_with_help", "used"].includes(
                requirement.latest_skill.answer,
              );
            const known = row?.status === "met" || row?.status === "satisfied";
            return (
              <li
                key={requirement.row_id}
                data-evidence={reported ? "self-reported" : known ? "met" : "unresolved"}
              >
                <a
                  className="skill-path-node"
                  href={`#skill-row-${requirement.row_id}`}
                  aria-current={selectedRow === requirement.row_id ? "true" : undefined}
                  onClick={() => onInspect(requirement.row_id)}
                >
                  <span aria-hidden="true">
                    {requirement.gate?.protected ? "◇" : known ? "●" : "○"}
                  </span>
                  <strong>{requirement.label}</strong>{" "}
                  <span>
                    {row
                      ? statusWords[row.status]
                      : reported
                        ? "Your answer, not verified"
                        : "Not known yet"}
                    {row && reported && ". Your answer, not verified"}
                  </span>
                </a>
              </li>
            );
          })}
        </ul>
        <div className="skill-path-destination">
          <span aria-hidden="true" />
          {target.target_title}
        </div>
      </div>
      {target.requirements.length === 0 && (
        <p>No checked requirements yet. Add an example advert to start.</p>
      )}
      <p className="decision-map-note">
        Branches show the evidence Careerwright holds, not distance from a job. Unanswered
        requirements stay unknown.
      </p>
      <div className="skill-evidence-summary">
        <h3>Learning comes next</h3>
        <p>
          Options can help with a gap. Planned learning stays separate until you have completed it
          and shown the outcome.
        </p>
      </div>
    </aside>
  );
}

export function SkillsChapter({ workspaceId }: { workspaceId: string }) {
  const skills = useSkills(workspaceId);
  if (skills.data === undefined && skills.error) {
    return (
      <div className="chapter-reading">
        <h1 className="page-title">Skills</h1>
        <RequestFailure
          error={skills.error}
          actions={<Button onClick={() => void skills.refetch()}>Try again</Button>}
        />
      </div>
    );
  }
  if (skills.data === undefined)
    return (
      <div className="chapter-reading">
        <h1 className="page-title">Skills</h1>
        <LoadingState stage="Loading what your targets ask for" />
      </div>
    );
  return <SkillsContent data={skills.data} workspaceId={workspaceId} />;
}

export function SkillsContent({ data, workspaceId }: { data: SkillsOut; workspaceId: string }) {
  const [chosen, setChosen] = useState<string | null>(null);
  const [selectedRow, setSelectedRow] = useState<string | null>(null);
  useEffect(() => {
    if (selectedRow !== null) document.getElementById(`skill-row-${selectedRow}`)?.focus();
  }, [selectedRow]);
  const target = data.targets.find((item) => item.target_key === chosen) ?? data.targets[0];
  const question =
    data.questions.prompts.find((prompt) => data.questions.initial.includes(prompt.prompt_id)) ??
    data.questions.prompts[0];
  const setQuestions = useSetSkillQuestions(workspaceId);
  const questions = (
    <section className="grid gap-12" aria-labelledby="skills-questions">
      <h2 id="skills-questions" className="section-title">
        {data.questions.state === "asking" ? "Your next answer" : "Your questions"}
      </h2>
      {data.questions.state === "stopped" ? (
        <p>Questions paused. Your answers are kept.</p>
      ) : data.questions.state === "enough" ? (
        <>
          <p>You have answered enough for now. Anything still unknown stays unresolved.</p>
          {question !== undefined && (
            <details className="place-more">
              <summary>Answer another question</summary>
              <div className="pt-12">
                <QuestionCard
                  key={question.prompt_id}
                  prompt={question}
                  data={data}
                  workspaceId={workspaceId}
                />
              </div>
            </details>
          )}
        </>
      ) : data.questions.state === "asking" && question !== undefined ? (
        <QuestionCard
          key={question.prompt_id}
          prompt={question}
          data={data}
          workspaceId={workspaceId}
        />
      ) : (
        <p className="small">
          Careerwright has no more questions it can use right now. Anything still unknown stays
          unresolved.
        </p>
      )}
      {(data.questions.state === "asking" || data.questions.state === "stopped") && (
        <div>
          <Button
            variant="secondary"
            onClick={() =>
              setQuestions.mutate({
                expected_version: data.questions.evidence_version,
                stopped: data.questions.state !== "stopped",
              })
            }
            disabledReason={setQuestions.isPending ? "Saving…" : undefined}
          >
            {data.questions.state === "stopped" ? "Resume questions" : "Pause questions"}
          </Button>
        </div>
      )}
      {setQuestions.error !== null && <RequestFailure error={setQuestions.error} />}
    </section>
  );

  return (
    <div className="chapter-layout">
      <div className="chapter-reading">
        <header className="chapter-heading">
          <h1 className="page-title">Skills</h1>
          <p>What your evidence tells us, and what you still need to show.</p>
        </header>
        {target === undefined ? (
          <div className="card grid gap-12">
            <p>Choose a target in You to see what it asks for.</p>
            <div>
              <Link className="btn btn-primary" href={chapterHref(workspaceId, "you")}>
                Choose a target
              </Link>
            </div>
          </div>
        ) : (
          <>
            {data.targets.length > 1 && (
              <fieldset className="flex flex-wrap gap-8">
                <legend className="sr-only">Choose a target</legend>
                {data.targets.map((item) => (
                  <Button
                    key={item.target_key}
                    variant="choice"
                    aria-pressed={target.target_key === item.target_key}
                    onClick={() => setChosen(item.target_key)}
                  >
                    {item.target_title}
                  </Button>
                ))}
              </fieldset>
            )}
            <TargetView
              target={target}
              data={data}
              workspaceId={workspaceId}
              selectedRow={selectedRow}
              nextQuestion={data.questions.state === "asking" ? questions : null}
            />
            {data.questions.state !== "asking" && questions}
            <UsualSkills data={data} workspaceId={workspaceId} />
          </>
        )}
        <details className="place-more">
          <summary>About these records</summary>
          <p className="small muted">
            Careerwright's course and skill records are dated {date(data.pack.dated)}. Draft records
            are labelled.
          </p>
        </details>
      </div>
      {target && (
        <SkillsLandscape target={target} selectedRow={selectedRow} onInspect={setSelectedRow} />
      )}
    </div>
  );
}
