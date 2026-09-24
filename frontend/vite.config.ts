import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api to the FastAPI backend so the SPA and API share an
// origin during development (no CORS friction). In production the SPA is served
// statically and talks to the API via VITE_API_BASE_URL.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY ?? "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
