// vite.config.ts
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  const inDocker =
    env.VITE_IN_DOCKER === "1" || process.env.DOCKER_CONTAINER === "1" || false;

  const host = env.VITE_BIND_HOST || "0.0.0.0";
  const port = Number(env.VITE_PORT || 5173);

  // Targets can be overridden via env. Sensible defaults for each mode:
  const proxyUM =
    env.VITE_PROXY_UM ||
    (inDocker ? "http://user_management:8000" : "http://localhost:8000");
  const proxyNotif =
    env.VITE_PROXY_NOTIF ||
    (inDocker ? "http://notifications:8001" : "http://localhost:8001");
  const proxyAgg =
    env.VITE_PROXY_AGG ||
    (inDocker ? "http://aggregator:9000" : "http://localhost:9000");

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    server: {
      host,
      port,
      strictPort: true,
      // Set HMR overlay off if you prefer (uncomment):
      // hmr: { overlay: false },
      proxy: {
        "/api": {
          target: proxyUM,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api/, ""),
        },
        "/notif": {
          target: proxyNotif,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/notif/, ""),
        },
        "/agg": {
          target: proxyAgg,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/agg/, ""),
        },
      },
    },
  };
});
