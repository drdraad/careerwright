import type { NextConfig } from "next";

const config: NextConfig = {
  // A self-contained server (`node server.js`) for the web container.
  output: "standalone",
  poweredByHeader: false,
  reactStrictMode: true,
  // Loopback only: compression buys nothing here and would buffer the proxied event stream.
  compress: false,
  images: { unoptimized: true },
  // `next dev` must not write agent instruction files into the repository.
  agentRules: false,
};

export default config;
