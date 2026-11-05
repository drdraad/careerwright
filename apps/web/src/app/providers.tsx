"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { EvidenceProvider } from "@/components/EvidenceDrawer";
import { configureApiClient } from "@/lib/api";
import { AuthProvider, type AuthSettings, useAuth } from "@/lib/auth";

function AccountSession({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [queries] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: true } },
      }),
  );
  configureApiClient(() => token(false));
  return <QueryClientProvider client={queries}>{children}</QueryClientProvider>;
}

function ApiSession({ children }: { children: ReactNode }) {
  const { state } = useAuth();
  // Changing accounts discards cached records, unsaved drafts and open evidence together.
  const session = state.status === "signed_in" ? `user:${state.uid}` : state.status;
  return (
    <AccountSession key={session}>
      <EvidenceProvider>{children}</EvidenceProvider>
    </AccountSession>
  );
}

export function Providers({ auth, children }: { auth: AuthSettings; children: ReactNode }) {
  return (
    <AuthProvider settings={auth}>
      <ApiSession>{children}</ApiSession>
    </AuthProvider>
  );
}
