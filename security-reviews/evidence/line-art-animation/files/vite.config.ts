import { defineConfig } from 'vite';
import { resolve } from 'node:path';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        index: resolve(import.meta.dirname, 'index.html'),
        walker: resolve(import.meta.dirname, 'examples/walker/index.html'),
        village: resolve(import.meta.dirname, 'examples/village/index.html'),
      },
    },
  },
});
