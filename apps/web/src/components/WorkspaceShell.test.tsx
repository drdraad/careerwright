import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ChapterId } from "@/lib/chapters";
import { fakeApi, type Route } from "@/test/fakeApi";
import { p01Checkpoint, p01Profile, p01Skills } from "@/test/p01DesignData";
import { ChapterView } from "./ChapterView";
import { EvidenceProvider } from "./EvidenceDrawer";
import { WorkspaceShell } from "./WorkspaceShell";

const navigation = vi.hoisted(() => ({ chapter: "routes" as ChapterId, replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => `/w/workspace/${navigation.chapter}`,
  useSelectedLayoutSegment: () => navigation.chapter,
  useRouter: () => ({ replace: navigation.replace }),
  useSearchParams: () => new URLSearchParams(window.location.search),
}));
vi.mock("@/lib/auth", () => ({
  useAuth: () => ({
    state: { status: "signed_in", uid: "ada", email: "ada@example.test" },
    token: async () => "test-token",
    signOut: async () => {},
  }),
}));
vi.mock("@/lib/queries", async (original) => ({
  ...(await original<typeof import("@/lib/queries")>()),
  useWorkspaceEvents: () => ({ status: { state: "live" }, restart: () => {} }),
}));

beforeEach(() => {
  vi.stubGlobal("matchMedia", () => ({
    matches: true,
    addEventListener: () => {},
    removeEventListener: () => {},
  }));
});

describe("[STATE-07][UI-09] chapter prerequisites", () => {
  it.each(["routes", "plan"] as const)(
    "shows a recoverable failure when %s prerequisites cannot be loaded",
    async (chapter) => {
      navigation.chapter = chapter;
      const prerequisite: Route = {
        method: "GET",
        path: chapter === "routes" ? /\/planning\/checkpoint$/ : /\/planning\/plans\/current$/,
        status: 503,
        answer: {
          error: {
            code: "STORE_UNAVAILABLE",
            message: "",
            retryable: true,
            stage: "storage",
            correlation_id: "c1",
            details: {},
          },
        },
      };
      fakeApi([
        prerequisite,
        { method: "GET", path: /\/me$/, answer: { email: "ada@example.test" } },
        {
          method: "GET",
          path: /\/workspaces\/workspace$/,
          answer: { workspace_id: "workspace", data_mode: "demo", synthetic: true },
        },
        { method: "GET", path: /\/workspaces$/, answer: { items: [], next_cursor: null } },
        { method: "GET", path: /\/profile$/, answer: p01Profile },
        { method: "GET", path: /\/skills$/, answer: p01Skills },
        { method: "GET", path: /\/planning\/checkpoint$/, answer: p01Checkpoint },
        { method: "GET", path: /\/runs$/, answer: { items: [], next_cursor: null } },
      ]);
      render(
        <QueryClientProvider
          client={new QueryClient({ defaultOptions: { queries: { retryDelay: 0 } } })}
        >
          <EvidenceProvider>
            <WorkspaceShell workspaceId="workspace">
              <ChapterView chapter={chapter} />
            </WorkspaceShell>
          </EvidenceProvider>
        </QueryClientProvider>,
      );

      expect(await screen.findByText("Careerwright's database isn't reachable")).toBeVisible();
      expect(screen.queryByText(/needs an earlier step/)).toBeNull();
      prerequisite.status = 200;
      prerequisite.answer = chapter === "routes" ? p01Checkpoint : () => null;
      await userEvent.click(screen.getByRole("button", { name: "Try again" }));
      expect(
        await screen.findByRole("heading", {
          name: chapter === "routes" ? "Compare your routes" : "Plan needs an earlier step",
        }),
      ).toBeVisible();
    },
  );
});
