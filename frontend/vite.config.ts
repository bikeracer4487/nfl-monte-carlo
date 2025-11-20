import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  base: command === 'serve' ? '/' : './',
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/status': 'http://127.0.0.1:8000',
      '/standings': 'http://127.0.0.1:8000',
      '/schedule': 'http://127.0.0.1:8000',
      '/simulate': 'http://127.0.0.1:8000',
      '/override': 'http://127.0.0.1:8000',
    }
  }
}))
