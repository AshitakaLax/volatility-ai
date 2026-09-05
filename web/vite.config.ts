import path from "node:path";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The dev server proxies /api and /ws to the Python server (Phase 2) so
// the browser only ever talks to one origin. Without this the app would
// need CORS in development and not in production, which is exactly the
// kind of difference that works locally and fails once deployed.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // shadcn/ui generates imports as "@/components/...", so the alias is
    // a prerequisite rather than a convenience.
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    // 127.0.0.1, not 0.0.0.0. This app renders account balances and
    // positions; binding it to every interface is a decision to make
    // deliberately, not a default to inherit.
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
    },
  },
});
