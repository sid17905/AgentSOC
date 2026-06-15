import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const isDev = mode === "development";

  // Only used in local dev — in production the browser talks directly
  // to Railway via VITE_API_URL / VITE_WS_URL env vars.
  const backendTarget =
    env.VITE_BACKEND_TARGET ??
    process.env.VITE_BACKEND_TARGET ??
    "http://localhost:8000";
  const backendWsTarget = backendTarget.replace(/^http/, "ws");

  return {
    plugins: [react()],
    server: isDev
      ? {
          port: 5173,
          proxy: {
            "/api": {
              target: backendTarget,
              changeOrigin: true,
            },
            "/ws": {
              target: backendWsTarget,
              ws: true,
              changeOrigin: true,
            },
          },
        }
      : { port: 5173 },
  };
});