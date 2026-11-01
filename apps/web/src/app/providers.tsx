"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useEffect, useState } from "react";
import { EvidenceProvider } from "@/components/EvidenceDrawer";
import { configureApiClient } from "@/lib/api";
import { AuthProvider, type AuthSettings, useAuth } from "@/lib/auth";

function ApiSession({ children }: { children: ReactNode }) {
  const { state, token } = useAuth();
  const [queries] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: true } },
      }),
  );
  configureApiClient(() => token(false));
  // Another identity must never see the previous one's cached data.
  const uid = state.status === "signed_in" ? state.uid : null;
  useEffect(() => {
    if (uid === null) queries.clear();
  }, [uid, queries]);
  return <QueryClientProvider client={queries}>{children}</QueryClientProvider>;
}

export function Providers({ auth, children }: { auth: AuthSettings; children: ReactNode }) {
  return (
    <AuthProvider settings={auth}>
      <ApiSession>
        <EvidenceProvider>{children}</EvidenceProvider>
      </ApiSession>
    </AuthProvider>
  );
}
