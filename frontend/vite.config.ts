import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, /api is proxied to FastAPI so no CORS setup is needed locally.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": { target: "http://localhost:8000", changeOrigin: true } },
  },
});
