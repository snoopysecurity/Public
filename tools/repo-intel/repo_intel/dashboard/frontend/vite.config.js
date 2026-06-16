import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],
  base: './', // Relative paths for portability
  build: {
    outDir: '../dist',
    emptyOutDir: true
  }
})
