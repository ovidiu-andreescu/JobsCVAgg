// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

/**
 * Modes:
 */
const useProxy = process.env.VITE_USE_PROXY === "1";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: process.env.VITE_BIND_HOST || "0.0.0.0",
    port: 5173,
    cors: true,
    proxy: useProxy
      ? {
          // User Management (auth, /me)
          "/api": {
            target: "http://user_management:8000",
            changeOrigin: true,
            rewrite: (p) => p.replace(/^\/api/, ""),
          },
          // Notifications service
          "/notif": {
            target: "http://notifications:8001",
            changeOrigin: true,
            rewrite: (p) => p.replace(/^\/notif/, ""),
          },
          // Job Aggregator (generic)
          "/agg": {
            target: "http://aggregator:9000",
            changeOrigin: true,
            rewrite: (p) => p.replace(/^\/agg/, ""),
          },
          // If your aggregator exposes /jobs/search directly
          "/jobs": {
            target: "http://aggregator:9000",
            changeOrigin: true,
          },
          "/cv": {
            target: "http://cv:8002",
            changeOrigin: true,
            rewrite: (p) => p.replace(/^\/cv/, ""),
          },
          "/match": {
            target: "http://matcher:8003",
            changeOrigin: true,
            rewrite: (p) => p.replace(/^\/match/, ""),
          },
        }
      : undefined,
  },
});
