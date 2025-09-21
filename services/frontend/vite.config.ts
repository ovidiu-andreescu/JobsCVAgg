import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

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
    proxy: {
      // Inside Docker these point to service names; locally they'll proxy from the browser to your host.
      "/api": {
        target: "http://user_management:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
      "/notif": {
        target: "http://notifications:8001",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/notif/, ""),
      },
      "/agg": {
        target: "http://aggregator:9000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/agg/, ""),
      },
    },
  },
});
