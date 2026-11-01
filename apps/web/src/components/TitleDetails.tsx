"use client";
// The person's own details beside a title (Task 6d slice C; ADR 0015 decisions 3 and 4): a
// seniority and an industry beside their role or a target, each optional and never a default
// (not given is said, never filled in), and, beside the role, the skills ESCO lists for its
// kind of work, any of which they may mark "not part of my job": a display state, never
// evidence. Matching ignores all of it. Shown only for a title the person gave, so nothing here
// presumes a job (the product owner, 1 November 2026). Typed words go through the support
// screen, as What we know's do: the panel shows under the title's details, from the API, and is
// never stored.
import { useId, useRef, useState } from "react";
import type { SupportNoteOut, TitleDetailsOut, UsualSkillOut } from "@/generated/api";
import { ApiError } from "@/lib/api";
import { useOrigin, useSaveTitleDetails, useTitleDetails } from "@/lib/queries";
import { TITLE_DETAILS, TITLE_USE } from "@/lib/vocabulary";
import { Button } from "./Button";
import { RequestFailure } from "./PageState";
import { SupportNote } from "./SupportNote";

const sentence = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
const given = (text: string) => (text.trim() === "" ? null : text.trim());

type Save = (next: Pick<TitleDetailsOut, "seniority" | "industry" | "not_part_of_job">) => void;

/** One title's seniority and industry, said as given or not, and the form that changes them. */
function DetailsForm({
  details,
  saving,
  onSave,
}: {
  details: TitleDetailsOut;
  saving: boolean;
  onSave: Save;
}) {
  const [open, setOpen] = useState(false);
  const [seniority, setSeniority] = useState(details.seniority ?? "");
  const [industry, setIndustry] = useState(details.industry ?? "");
  const opener = useRef<HTMLButtonElement>(null);
  const formId = useId();
  const hasAny = details.seniority !== null || details.industry !== null;
  return (
    <div className="grid gap-8">
      <p className="small">{TITLE_DETAILS.given(details.seniority, details.industry)}</p>
      <div>
        <Button
          ref={opener}
          variant="quiet"
          aria-expanded={open}
          aria-controls={formId}
          onClick={() => {
            setSeniority(details.seniority ?? "");
            setIndustry(details.industry ?? "");
            setOpen((now) => !now);
          }}
        >
          {TITLE_DETAILS.open(details.title, hasAny)}
        </Button>
      </div>
      {open && (
        <form
          id={formId}
          className="grid gap-8"
          onSubmit={(event) => {
            event.preventDefault();
            onSave({
              seniority: given(seniority),
              industry: given(industry),
              not_part_of_job: details.not_part_of_job,
            });
          }}
        >
          <Field
            label={TITLE_DETAILS.seniority}
            hint={TITLE_DETAILS.seniorityHint}
            value={seniority}
            onChange={setSeniority}
          />
          <Field
            label={TITLE_DETAILS.industry}
            hint={TITLE_DETAILS.industryHint}
            value={industry}
            onChange={setIndustry}
          />
          <div className="flex flex-wrap items-center gap-8">
            <Button
              type="submit"
              variant="secondary"
              disabledReason={saving ? "Saving…" : undefined}
            >
              {TITLE_DETAILS.save}
            </Button>
            <Button
              variant="quiet"
              onClick={() => {
                setOpen(false);
                opener.current?.focus();
              }}
            >
              {TITLE_DETAILS.cancel}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}

function Field({
  label,
  hint,
  value,
  onChange,
}: {
  label: string;
  hint: string;
  value: string;
  onChange(next: string): void;
}) {
  const id = useId();
  return (
    <div className="grid gap-4">
      <label htmlFor={id} className="small muted">
        {label}
      </label>
      <input
        id={id}
        className="input"
        maxLength={120}
        autoComplete="off"
        value={value}
        aria-describedby={`${id}-hint`}
        onChange={(event) => onChange(event.target.value)}
      />
      <p id={`${id}-hint`} className="small muted">
        {hint}
      </p>
    </div>
  );
}

/** The skills ESCO lists for the role's kind of work, one step away, each with "Not part of my
 *  job" as a toggle. */
function ListedSkills({
  details,
  skills,
  saving,
  onSave,
}: {
  details: TitleDetailsOut;
  skills: UsualSkillOut[];
  saving: boolean;
  onSave: Save;
}) {
  if (skills.length === 0) return null;
  const marked = new Set(details.not_part_of_job);
  return (
    <details className="details">
      <summary>{TITLE_DETAILS.listed(skills.length)}</summary>
      <div className="grid gap-8 mt-8">
        <p className="small muted">{TITLE_DETAILS.listedIntro}</p>
        <ul className="plain-list grid gap-8">
          {skills.map((skill) => {
            const pressed = marked.has(skill.skill_id);
            return (
              <li key={skill.skill_id} className="grid gap-4">
                <div className="flex flex-wrap items-center gap-8">
                  <span>{sentence(skill.label)}</span>
                  <Button
                    variant="quiet"
                    aria-pressed={pressed}
                    disabledReason={saving ? "Saving…" : undefined}
                    onClick={() =>
                      onSave({
                        seniority: details.seniority,
                        industry: details.industry,
                        not_part_of_job: pressed
                          ? details.not_part_of_job.filter((id) => id !== skill.skill_id)
                          : [...details.not_part_of_job, skill.skill_id],
                      })
                    }
                  >
                    {TITLE_DETAILS.notPart}
                    <span className="sr-only">: {skill.label}</span>
                  </Button>
                </div>
                {pressed && <p className="small muted">{TITLE_DETAILS.notPartSaid}</p>}
              </li>
            );
          })}
        </ul>
      </div>
    </details>
  );
}

function OneTitle({ workspaceId, details }: { workspaceId: string; details: TitleDetailsOut }) {
  const save = useSaveTitleDetails(workspaceId);
  const isRole = details.title_use === "role";
  const origin = useOrigin(workspaceId, isRole);
  // The calm panel the last save brought, kept until dismissed or the next save.
  const [support, setSupport] = useState<SupportNoteOut | null>(null);
  const [saved, setSaved] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const onSave: Save = (next) => {
    setSaved(false);
    void save
      .mutateAsync({
        expected_version: details.version,
        title_use: details.title_use,
        title: details.title,
        ...next,
      })
      .then((stored) => {
        setSupport(stored.support_note ?? null);
        setSaved(true);
      })
      .catch((error: unknown) => setSupport(error instanceof ApiError ? error.supportNote : null));
  };
  const headingId = useId();
  return (
    <section className="grid gap-8" aria-labelledby={headingId}>
      <h4 id={headingId} className="small font-semibold" tabIndex={-1} ref={heading}>
        {TITLE_USE[details.title_use]}: {sentence(details.title)}
      </h4>
      <p role="status" className="sr-only">
        {saved ? TITLE_DETAILS.saved : ""}
      </p>
      <DetailsForm
        // A saved version starts the form again from what was saved.
        key={details.version}
        details={details}
        saving={save.isPending}
        onSave={onSave}
      />
      {support !== null && (
        <SupportNote
          note={support}
          onDismiss={() => {
            setSupport(null);
            heading.current?.focus(); // the button goes; focus is never lost
          }}
        />
      )}
      {isRole && (
        <ListedSkills
          details={details}
          skills={origin.data?.usual_skills ?? []}
          saving={save.isPending}
          onSave={onSave}
        />
      )}
      {save.error !== null && <RequestFailure error={save.error} />}
    </section>
  );
}

export function TitleDetails({ workspaceId }: { workspaceId: string }) {
  const titles = useTitleDetails(workspaceId);
  if (titles.data === undefined) {
    return titles.error ? <RequestFailure error={titles.error} /> : null;
  }
  // A person who gave no title meets nothing here: no empty panel, no job wording.
  if (titles.data.titles.length === 0) return null;
  return (
    <section className="known-group grid gap-12" aria-labelledby="title-details">
      <h3 id="title-details">{TITLE_DETAILS.heading}</h3>
      <p className="small muted">{TITLE_DETAILS.intro}</p>
      {titles.data.titles.map((details) => (
        <OneTitle
          key={`${details.title_use}:${details.title}`}
          workspaceId={workspaceId}
          details={details}
        />
      ))}
    </section>
  );
}
