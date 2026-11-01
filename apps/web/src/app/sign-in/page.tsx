import type { Metadata } from "next";
import { PageFrame } from "@/components/PageState";
import { SignInForm } from "@/components/SignInForm";
import { safeNext } from "@/lib/navigation";

export const metadata: Metadata = { title: "Sign in · Careerwright" };

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string | string[] }>;
}) {
  const { next } = await searchParams;
  return (
    <PageFrame>
      <SignInForm next={safeNext(typeof next === "string" ? next : undefined)} />
    </PageFrame>
  );
}
