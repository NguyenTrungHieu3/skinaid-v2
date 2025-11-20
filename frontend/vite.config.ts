import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// @ts-ignore
import mkcert from 'vite-plugin-mkcert'

export default defineConfig({
  plugins: [react(), mkcert()],
  server: {
    host: true,
    https: true  // Enable HTTPS
  }
})