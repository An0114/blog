import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 开发代理：API 与上传静态文件转发到本地 FastAPI（后端地址见 backend/.env）。
    // 容器化开发模式（docker-compose.dev.yml）通过 VITE_PROXY_TARGET 覆盖为 http://backend:8000；
    // 本地直接 npm run dev 时默认 127.0.0.1:8000，行为不变。
    proxy: {
      '/api': { target: process.env.VITE_PROXY_TARGET ?? 'http://127.0.0.1:8000', changeOrigin: true },
      '/uploads': { target: process.env.VITE_PROXY_TARGET ?? 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
