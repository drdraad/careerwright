"use client";
// Sign-in with the Auth emulator's seeded local identities (runbook "Addresses"). These are
// test accounts on this machine, not real accounts; passwords are documented test values.
import { useRouter } from "next/navigation";
import { useEffect, useId, useState } from "react";
import { type SignInProblem, useAuth } from "@/lib/auth";
import { Alert } from "./Alert";
import { Button } from "./Button";
import { Glyph } from "./Glyph";

const IDENTITIES = [
  { handle: "ada", name: "Ada Demo", note: "invited; owns the P01 fixture workspace" },
  { handle: "ben", name: "Ben Demo", note: "invited; no workspace yet" },
  { handle: "uninvited", name: "Uninvited Demo", note: "can sign in, then is refused" },
] as const;

const PROBLEM: Record<SignInProblem, string> = {
  wrong_credentials: "That email and password don't match a local identity.",
  unreachable: "The sign-in service isn't reachable. Is Careerwright running (make demo)?",
  too_many_attempts: "Too many attempts. Wait a moment, then try again.",
  failed: "Sign-in didn't work. Try again.",
};

export function SignInForm({ next }: { next: string }) {
  const auth = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [problem, setProblem] = useState<SignInProblem | null>(null);
  const [busy, setBusy] = useState(false);
  const id = useId();

  useEffect(() => {
    if (auth.state.status === "signed_in") router.replace(next);
  }, [auth.state.status, next, router]);

  const submit = async () => {
    setBusy(true);
    setProblem(await auth.signIn(email.trim(), password));
    setBusy(false);
  };

  return (
    <>
      <div className="flex items-center gap-12">
        <Glyph name="mark" className="h-[32px] w-[32px]" />
        <h1 className="page-title">Sign in to Careerwright</h1>
      </div>
      <p className="small muted">
        Local sign-in through the Firebase Auth emulator on this computer. Being signed in is not
        enough on its own: Careerwright also checks that the account is invited.
      </p>
      <section className="grid gap-8" aria-labelledby={`${id}-identities`}>
        <h2 id={`${id}-identities`} className="section-title">
          Seeded local identities
        </h2>
        <ul className="grid gap-8">
          {IDENTITIES.map((identity) => (
            <li key={identity.handle}>
              <button
                type="button"
                className="btn btn-secondary w-full flex-wrap justify-start whitespace-normal py-8 text-left"
                onClick={() => {
                  setEmail(`${identity.handle}@careerwright.test`);
                  setPassword(`careerwright-demo-${identity.handle}`);
                  setProblem(null);
                }}
              >
                Use {identity.name}
                <span className="font-normal text-fg-muted">({identity.note})</span>
              </button>
            </li>
          ))}
        </ul>
      </section>
      <form
        className="grid gap-12"
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <div className="grid gap-4">
          <label htmlFor={`${id}-email`} className="field-label">
            Email
          </label>
          <input
            id={`${id}-email`}
            className="input"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <div className="grid gap-4">
          <label htmlFor={`${id}-password`} className="field-label">
            Password
          </label>
          <input
            id={`${id}-password`}
            className="input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        {problem !== null && <Alert tone="error" title={PROBLEM[problem]} />}
        <div>
          <Button
            type="submit"
            variant="primary"
            disabledReason={
              busy
                ? "Signing in…"
                : email === "" || password === ""
                  ? "Enter an email and password."
                  : undefined
            }
          >
            Sign in
          </Button>
        </div>
      </form>
    </>
  );
}
