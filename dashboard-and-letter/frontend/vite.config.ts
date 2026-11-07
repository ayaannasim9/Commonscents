import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Mock mode reads ../contract/fixtures, which sits outside the Vite root.
export default defineConfig({
  plugins: [react()],
  server: {
    fs: { allow: ['..'] },
    proxy: { '/api': { target: 'http://localhost:8000', rewrite: (p) => p.replace(/^\/api/, '') } },
  },
})
