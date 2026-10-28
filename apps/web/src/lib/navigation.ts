/** Only same-site paths: a sign-in link can never send someone to another site. */
export function safeNext(next: string | undefined): string {
  if (next === undefined || !next.startsWith("/")) return "/";
  // "//host" and "/\host" are protocol-relative to browsers; control characters are refused.
  if (next.startsWith("//") || next.startsWith("/\\")) return "/";
  for (const char of next) {
    if (char.charCodeAt(0) < 0x20) return "/";
  }
  return next;
}
