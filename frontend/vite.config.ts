import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend port - must match start.py BACKEND_PORT
const BACKEND_PORT = process.env.VITE_BACKEND_PORT || '8003'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Listen on all interfaces (fixes IPv6 issues)
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${BACKEND_PORT}`,
        changeOrigin: true,
      },
    },
  },
})
