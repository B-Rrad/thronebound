import { defineConfig } from "vite";

export default defineConfig({
  root: ".",
  build: {
    outDir: "dist-web",
    emptyOutDir: true,
    rollupOptions: {
      input: "web/index.html"
    }
  },
  server: {
    port: 5173
  }
});
