import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // All /api traffic is proxied to the Python server so the browser sees a
      // single origin. This is deliberate: server.py sets Access-Control-Allow-Origin
      // but implements no do_OPTIONS handler, so any request that triggers a CORS
      // preflight gets a 501 from BaseHTTPRequestHandler. Same-origin never preflights.
      '/api': {
        // 127.0.0.1, not localhost. server.py binds ('', 8000) which is IPv4-only,
        // while Node resolves "localhost" to ::1 first on Windows -> ECONNREFUSED.
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
    },
  },
})
