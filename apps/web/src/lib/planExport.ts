import { exportPlanCalendar, exportPlanJson, exportWorkspace } from "@/generated/api";

function save(name: string, type: string, content: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export async function downloadPlanJson(
  workspaceId: string,
  version: number,
  omissions: { financial: boolean; sensitive: boolean },
) {
  const data = (
    await exportPlanJson({
      path: { workspace_id: workspaceId, version },
      query: {
        omit_financial_detail: omissions.financial,
        omit_sensitive_detail: omissions.sensitive,
      },
      throwOnError: true,
    })
  ).data;
  save(`careerwright-plan-v${version}.json`, "application/json", JSON.stringify(data, null, 2));
}

export async function downloadPlanCalendar(workspaceId: string, version: number) {
  const data = (
    await exportPlanCalendar({
      path: { workspace_id: workspaceId, version },
      parseAs: "text",
      throwOnError: true,
    })
  ).data;
  if (typeof data !== "string") throw new Error("The calendar response was not text");
  save(`careerwright-plan-v${version}.ics`, "text/calendar", data);
}

export async function downloadWorkspace(workspaceId: string) {
  const data = (await exportWorkspace({ path: { workspace_id: workspaceId }, throwOnError: true }))
    .data;
  save("careerwright-workspace.json", "application/json", JSON.stringify(data, null, 2));
}
