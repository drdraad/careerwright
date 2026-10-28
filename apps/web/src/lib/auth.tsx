"use client";
// Sign-in through the Firebase Auth emulator (ADR 0001, ADR 0004 decision 4). The browser
// talks to the emulator on loopback only; no popup or redirect resolver is installed, so the
// SDK loads nothing from Google. Sign-in alone is not authorisation: the API checks the token
// and an active invitation on every request.
import { initializeApp } from "@firebase/app";
import {
  type Auth,
  browserLocalPersistence,
  connectAuthEmulator,
  signOut as endSession,
  initializeAuth,
  onIdTokenChanged,
  signInWithEmailAndPassword,
} from "@firebase/auth";
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export type AuthSettings = { emulatorUrl: string; projectId: string };

export type AuthState =
  | { status: "loading" }
  | { status: "signed_out" }
  | { status: "signed_in"; uid: string; email: string | null };

export type SignInProblem = "wrong_credentials" | "unreachable" | "too_many_attempts" | "failed";

type AuthContextValue = {
  state: AuthState;
  signIn(email: string, password: string): Promise<SignInProblem | null>;
  signOut(): Promise<void>;
  /** The current ID token (refreshed when `forceRefresh`), or null when signed out. */
  token(forceRefresh?: boolean): Promise<string | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

let instance: { key: string; auth: Auth } | undefined;

function emulatorAuth({ emulatorUrl, projectId }: AuthSettings): Auth {
  const key = `${projectId}@${emulatorUrl}`;
  if (instance?.key === key) return instance.auth;
  // The emulator accepts any API key; this value is not a credential.
  const app = initializeApp(
    { apiKey: "local-emulator", projectId, authDomain: new URL(emulatorUrl).host },
    `nessa-${key}`,
  );
  const auth = initializeAuth(app, { persistence: browserLocalPersistence });
  connectAuthEmulator(auth, emulatorUrl, { disableWarnings: true });
  instance = { key, auth };
  return auth;
}

function problemOf(error: unknown): SignInProblem {
  const code =
    typeof error === "object" && error !== null && "code" in error ? String(error.code) : "";
  if (
    [
      "auth/invalid-credential",
      "auth/wrong-password",
      "auth/user-not-found",
      "auth/invalid-email",
    ].includes(code)
  ) {
    return "wrong_credentials";
  }
  if (code === "auth/network-request-failed") return "unreachable";
  if (code === "auth/too-many-requests") return "too_many_attempts";
  return "failed";
}

export function AuthProvider({
  settings,
  children,
}: {
  settings: AuthSettings;
  children: ReactNode;
}) {
  const auth = useMemo(() => emulatorAuth(settings), [settings]);
  const [state, setState] = useState<AuthState>({ status: "loading" });

  useEffect(
    () =>
      onIdTokenChanged(auth, (user) =>
        setState(
          user === null
            ? { status: "signed_out" }
            : { status: "signed_in", uid: user.uid, email: user.email },
        ),
      ),
    [auth],
  );

  const signIn = useCallback(
    async (email: string, password: string) => {
      try {
        await signInWithEmailAndPassword(auth, email, password);
        return null;
      } catch (error) {
        return problemOf(error);
      }
    },
    [auth],
  );

  const signOut = useCallback(() => endSession(auth), [auth]);

  const token = useCallback(
    async (forceRefresh = false) => {
      await auth.authStateReady();
      const user = auth.currentUser;
      if (user === null) return null;
      try {
        return await user.getIdToken(forceRefresh);
      } catch (error) {
        // Sign-in unreachable for now: a transient failure the caller retries.
        if (problemOf(error) === "unreachable") throw error;
        // The session itself was refused (expired, disabled, or unknown to the emulator).
        await endSession(auth);
        return null;
      }
    },
    [auth],
  );

  const value = useMemo(() => ({ state, signIn, signOut, token }), [state, signIn, signOut, token]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (value === null) throw new Error("useAuth outside AuthProvider");
  return value;
}
