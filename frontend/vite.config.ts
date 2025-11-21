import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    // Ensure Vite uses a single React instance to avoid "Invalid hook call" errors
    dedupe: ['react', 'react-dom'],
  },
})
