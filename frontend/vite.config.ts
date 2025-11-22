import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// @ts-ignore
import mkcert from 'vite-plugin-mkcert'

export default defineConfig({
  plugins: [react()],
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
})
