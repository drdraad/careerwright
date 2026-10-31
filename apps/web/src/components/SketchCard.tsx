"use client";
// The early requirement sketch (spec section 3, STATE-05): what each target usually asks for,
// from ESCO, and the steps still unresolved. Always labelled an early sketch, never a checked
// or best route; it names no provider, price or date. An ambiguous title is resolved only by
// the person's choice, never guessed.
import type { ProfileOut, TargetSketchOut } from "@/generated/api";
import { useChooseTarget, useSketch } from "@/lib/queries";
import {
  PROFILE_FIELDS,
  RESEARCH_STATUS,
  RESOLUTION,
  SKETCH_LABEL,
  SKETCH_STEP,
  TARGET_COVERAGE,
} from "@/lib/vocabulary";
import { Button } from "./Button";
import { Glyph } from "./Glyph";
import { LoadingState } from "./LoadingState";
import { RequestFailure } from "./PageState";

const sentence = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

/** What a target matched to one ESCO occupation usually asks for, from ESCO: its first
 *  essential skills, how many more there are, and whether ESCO marks it regulated. */
export function TargetRequirements({ target }: { target: TargetSketchOut }) {
  if (target.resolution !== "esco") return null;
  return (
    <>
      <p className="small">What this work usually asks for, from ESCO:</p>
      <ul className="plain-list">
        {target.requirements.map((requirement) => (
          <li key={requirement}>{sentence(requirement)}</li>
        ))}
      </ul>
      {target.requirement_count !== null &&
        target.requirement_count > target.requirements.length && (
          <p className="small muted">
            And {target.requirement_count - target.requirements.length} more essential skills in
            ESCO.
          </p>
        )}
      {target.regulated && (
        <p className="small">
          ESCO marks this as a regulated profession in at least one European country. Whether
          England requires registration isn't checked yet.
        </p>
      )}
    </>
  );
}

/** How far Careerwright can cover a target, from its stored record, in one plain line. */
export function TargetCoverageLine({ target }: { target: TargetSketchOut }) {
  return <p className="small">{TARGET_COVERAGE[target.coverage](target.resolution === "esco")}</p>;
}

/** What the target's match and coverage mean for its requirements; none for a pack target
 *  ESCO doesn't name, which its coverage line already covers. */
function ResearchStatus({ target }: { target: TargetSketchOut }) {
  const status = RESEARCH_STATUS[target.resolution](target.coverage);
  return status === null ? null : <p className="small muted">{status}</p>;
}

export function SketchCard({ workspaceId, profile }: { workspaceId: string; profile: ProfileOut }) {
  const sketch = useSketch(workspaceId);
  const choose = useChooseTarget(workspaceId);
  if (sketch.data === undefined) {
    return sketch.error ? (
      <RequestFailure
        error={sketch.error}
        actions={
          <Button variant="secondary" onClick={() => void sketch.refetch()}>
            Try again
          </Button>
        }
      />
    ) : (
      <LoadingState stage="Loading the early sketch" lines={2} />
    );
  }
  const data = sketch.data;
  return (
    <section className="sketch" aria-labelledby="sketch-title">
      <h3 id="sketch-title" className="status" data-tone="unknown">
        <Glyph name="unknown" />
        <span>{SKETCH_LABEL}</span>
      </h3>
      {data.targets.length === 0 ? (
        <p className="small">
          A sketch needs a target role. Name one, or ask Careerwright for directions to explore.
        </p>
      ) : (
        data.targets.map((target) => (
          <div key={target.title} className="grid gap-8">
            <p className="small">
              <strong>{sentence(target.title)}</strong>: {RESOLUTION[target.resolution]}
            </p>
            <TargetCoverageLine target={target} />
            <TargetRequirements target={target} />
            {(target.resolution === "ambiguous" ||
              target.resolution === "not_found" ||
              target.resolution === "uk_title") &&
              (target.resolution === "ambiguous" ? target.occupations : target.close_matches)
                .length > 0 && (
                <div className="grid gap-4">
                  <p className="small">
                    {target.resolution === "ambiguous" ? "Which do you mean?" : "Closest in ESCO:"}
                  </p>
                  <div className="flex flex-wrap gap-8">
                    {(target.resolution === "ambiguous"
                      ? target.occupations
                      : target.close_matches
                    ).map((occupation) => (
                      <Button
                        key={occupation.concept_id}
                        variant="secondary"
                        onClick={() =>
                          choose.mutate({
                            expected_version: profile.version,
                            concept_id: occupation.concept_id,
                            replaces: target.title,
                          })
                        }
                      >
                        Use {sentence(occupation.title)}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            <ResearchStatus target={target} />
          </div>
        ))
      )}
      {data.steps.length > 0 && (
        <ol className="plain-list">
          {data.steps.map(({ step }) => (
            <li key={step}>
              {SKETCH_STEP[step].name}.{" "}
              <span className="muted">
                Not resolved yet. {SKETCH_STEP[step].detail(data.inputs)}
              </span>
            </li>
          ))}
        </ol>
      )}
      {data.not_asked.length > 0 && (
        <p className="small muted">
          Not asked yet, so the sketch can't use them:{" "}
          {data.not_asked.map((name) => PROFILE_FIELDS[name].label.toLowerCase()).join(", ")}.
        </p>
      )}
      {choose.error !== null && <RequestFailure error={choose.error} />}
    </section>
  );
}
