import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development the FastAPI backend runs on :8000.
// Vite proxies /api/* to it so the frontend can fetch without CORS noise.
// In production the static bundle is served by FastAPI directly (or any other
// static host), and /api/* is on the same origin — so the proxy only matters
// at dev time.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
