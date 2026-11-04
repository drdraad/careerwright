import { type FormEvent, useId, useState } from "react";
import { Button } from "./Button";
import { FieldError } from "./fields";

export type AddedOption = {
  title: string;
  provider: string | null;
  kind: "learning" | "apprenticeship";
  text: string | null;
};

export function AddOptionForm({
  target,
  saving,
  onSave,
  onCancel,
}: {
  target: string;
  saving: boolean;
  onSave(value: AddedOption): Promise<string | null>;
  onCancel(): void;
}) {
  const id = useId();
  const [step, setStep] = useState<"title" | "provider" | "source">("title");
  const [title, setTitle] = useState("");
  const [provider, setProvider] = useState("");
  const [kind, setKind] = useState<AddedOption["kind"]>("learning");
  const [text, setText] = useState("");
  const [problem, setProblem] = useState<string | null>(null);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (saving) return;
    if (step === "title") {
      if (!title.trim()) {
        setProblem("Name the option first.");
        return;
      }
      setProblem(null);
      setStep("provider");
      return;
    }
    if (step === "provider") {
      setProblem(null);
      setStep("source");
      return;
    }
    void onSave({
      title: title.trim(),
      provider: provider.trim() || null,
      kind,
      text: text.trim() || null,
    });
  };
  return (
    <form className="grid gap-12" onSubmit={submit} noValidate>
      <h3 className="section-title">Add an option for {target}</h3>
      {step === "title" && (
        <>
          <label className="grid gap-4" htmlFor="own-title">
            <span className="small">What is it called?</span>
            <input
              id="own-title"
              className="input"
              maxLength={300}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </label>
          <label className="grid gap-4" htmlFor="own-kind">
            <span className="small">What kind of option?</span>
            <select
              id="own-kind"
              className="input"
              value={kind}
              onChange={(event) => setKind(event.target.value as AddedOption["kind"])}
            >
              <option value="learning">Course</option>
              <option value="apprenticeship">Apprenticeship</option>
            </select>
          </label>
        </>
      )}
      {step === "provider" && (
        <label className="grid gap-4" htmlFor="own-provider">
          <span className="small">Who offers it? Leave blank if you do not know yet.</span>
          <input
            id="own-provider"
            className="input"
            maxLength={300}
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
          />
        </label>
      )}
      {step === "source" && (
        <>
          <label className="grid gap-4" htmlFor="own-source">
            <span className="small">
              Paste the page text if you have it. You can leave this blank.
            </span>
            <textarea
              id="own-source"
              className="input"
              maxLength={50000}
              rows={5}
              value={text}
              onChange={(event) => setText(event.target.value)}
            />
          </label>
          <p className="small">
            Careerwright will mark this as your own option, not reviewed. Adding it does not
            establish which requirements it meets.
          </p>
        </>
      )}
      {problem && <FieldError id={`${id}-error`}>{problem}</FieldError>}
      <div className="flex flex-wrap gap-8">
        <Button type="submit" variant="primary" disabledReason={saving ? "Saving…" : undefined}>
          {step === "source" ? "Save this option" : "Next"}
        </Button>
        <Button
          type="button"
          onClick={
            step === "title" ? onCancel : () => setStep(step === "source" ? "provider" : "title")
          }
        >
          {step === "title" ? "Cancel" : "Back"}
        </Button>
      </div>
    </form>
  );
}
