// Request policy for every page and API call the web server answers (Global Constraint 9).
//   - The Host header must be one of the configured loopback `host:port` values. A hostile
//     page that rebinds its own name to 127.0.0.1 therefore gets nothing from this origin.
//   - The Content-Security-Policy confines the page to this origin and the Auth emulator:
//     no script, font, image or connection may come from anywhere else, so the app cannot
//     make an external request even by accident (BND1-11 in the browser).

export function hostAllowed(host: string | null, allowed: readonly string[]): boolean {
  return host !== null && allowed.includes(host.trim().toLowerCase());
}

export function securityHeaders(
  authEmulatorOrigin: string,
  development: boolean,
): Record<string, string> {
  const script = development ? "'self' 'unsafe-inline' 'unsafe-eval'" : "'self' 'unsafe-inline'";
  const connect = development ? `'self' ${authEmulatorOrigin} ws:` : `'self' ${authEmulatorOrigin}`;
  return {
    "Content-Security-Policy": [
      "default-src 'self'",
      `script-src ${script}`,
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data:",
      "font-src 'self'",
      `connect-src ${connect}`,
      "frame-src 'none'",
      "frame-ancestors 'none'",
      "object-src 'none'",
      "base-uri 'none'",
      "form-action 'self'",
    ].join("; "),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "Cross-Origin-Opener-Policy": "same-origin",
  };
}
