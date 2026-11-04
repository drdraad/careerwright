import { afterEach, describe, expect, it, vi } from "vitest";
import { client } from "@/generated/api/client.gen";
import { configureApiClient } from "./api";
import { downloadPlanCalendar, downloadPlanJson } from "./planExport";

const originalCreate = URL.createObjectURL;
const originalRevoke = URL.revokeObjectURL;

afterEach(() => {
  URL.createObjectURL = originalCreate;
  URL.revokeObjectURL = originalRevoke;
  vi.restoreAllMocks();
});

describe("plan downloads use the signed-in API client", () => {
  it("sends omission choices with the JSON export and saves the returned data", async () => {
    configureApiClient(async () => "test-token");
    const requests: Request[] = [];
    client.setConfig({
      baseUrl: "http://localhost:3000/api",
      fetch: async (input: RequestInfo | URL) => {
        requests.push(input as Request);
        return new Response('{"version":1}', {
          headers: { "content-type": "application/json" },
        });
      },
    });
    URL.createObjectURL = vi.fn(() => "blob:plan");
    URL.revokeObjectURL = vi.fn();
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    await downloadPlanJson("workspace", 1, { financial: true, sensitive: true });

    expect(requests).toHaveLength(1);
    expect(requests[0]?.headers.get("Authorization")).toBe("Bearer test-token");
    expect(requests[0]?.url).toContain("omit_financial_detail=true");
    expect(requests[0]?.url).toContain("omit_sensitive_detail=true");
    expect((click.mock.instances[0] as HTMLAnchorElement | undefined)?.download).toBe(
      "careerwright-plan-v1.json",
    );
  });

  it("downloads exact calendar text through the authenticated endpoint", async () => {
    configureApiClient(async () => "test-token");
    const requests: Request[] = [];
    client.setConfig({
      baseUrl: "http://localhost:3000/api",
      fetch: async (input: RequestInfo | URL) => {
        requests.push(input as Request);
        return new Response("BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n", {
          headers: { "content-type": "text/calendar" },
        });
      },
    });
    const blobs: Blob[] = [];
    URL.createObjectURL = vi.fn((blob: Blob) => {
      blobs.push(blob);
      return "blob:calendar";
    });
    URL.revokeObjectURL = vi.fn();
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    await downloadPlanCalendar("workspace", 2);

    expect(requests[0]?.headers.get("Authorization")).toBe("Bearer test-token");
    expect((click.mock.instances[0] as HTMLAnchorElement | undefined)?.download).toBe(
      "careerwright-plan-v2.ics",
    );
    expect(blobs[0]?.type).toBe("text/calendar");
  });
});
