import { defineConfig } from "vite";

// The spike serves itself on loopback only and inlines nothing: fonts and scripts are files on
// its own origin, so the request log shows every asset.
export default defineConfig({
  server: { host: "127.0.0.1", port: 53300, strictPort: true },
  preview: { host: "127.0.0.1", port: 53300, strictPort: true },
  build: {
    assetsInlineLimit: 0,
    // three.js's WebGLRenderer brings its built-in shader library (about 590 kB minified); the
    // size is recorded in the README's library comparison rather than warned about on every build.
    chunkSizeWarningLimit: 800,
    rolldownOptions: {
      input: { main: "index.html", bench: "bench/index.html" },
    },
  },
});
