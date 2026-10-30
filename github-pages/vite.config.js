import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: '/SMART-ECO-BIN/',
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1600
  }
});
