import type { Metadata, Viewport } from "next";
import { connection } from "next/server";
import type { ReactNode } from "react";
import { webConfig } from "@/lib/config";
import "@/design/tokens/tokens.css";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Careerwright",
  description: "Plan a career change you can see and afford. Local L0 build.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = { themeColor: "#03050B", colorScheme: "dark" };

export default async function RootLayout({ children }: { children: ReactNode }) {
  // Runtime configuration (one image, any local ports): read per request, never at build.
  await connection();
  const config = webConfig();
  return (
    <html lang="en-GB">
      <body>
        <Providers
          auth={{ emulatorUrl: config.authEmulatorUrl, projectId: config.firebaseProjectId }}
        >
          {children}
        </Providers>
      </body>
    </html>
  );
}
