// Runs before every route (Next.js "proxy", formerly middleware): refuses a foreign Host and
// sets the security headers. Configuration errors fail closed: no page is served.
import { type NextRequest, NextResponse } from "next/server";
import { webConfig } from "@/lib/config";
import { hostAllowed, securityHeaders } from "@/lib/requestPolicy";

export function proxy(request: NextRequest): NextResponse {
  let config: ReturnType<typeof webConfig>;
  try {
    config = webConfig();
  } catch (error) {
    console.error(
      `careerwright-web refuses to serve: ${error instanceof Error ? error.message : "invalid configuration"}`,
    );
    return new NextResponse("Careerwright's web server is not configured safely; see its log.", {
      status: 500,
    });
  }
  if (!hostAllowed(request.headers.get("host"), config.allowedHosts)) {
    return new NextResponse("This server answers only on its local address.", { status: 400 });
  }
  const response = NextResponse.next();
  const headers = securityHeaders(config.authEmulatorUrl, process.env.NODE_ENV === "development");
  for (const [name, value] of Object.entries(headers)) response.headers.set(name, value);
  return response;
}

export const config = {
  // Everything except the container's liveness probe, which reaches the server by its
  // in-container address and reveals nothing.
  matcher: ["/((?!healthz$).*)"],
};
