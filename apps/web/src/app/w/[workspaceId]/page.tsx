import { redirect } from "next/navigation";
import { chapterHref } from "@/lib/chapters";

export default async function WorkspaceIndex({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  redirect(chapterHref(workspaceId, "you"));
}
