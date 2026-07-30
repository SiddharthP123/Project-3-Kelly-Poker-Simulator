import path from 'path'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Port matches the backend's already-configured CORS_ALLOWED_ORIGINS
// (backend/config.py) -- less disruptive to fix here than to change an
// already-documented backend default.
export default defineConfig({
    plugins: [react(), tailwindcss()],
    resolve: {
        alias: {
            '@': path.resolve(import.meta.dirname, './src'),
        },
    },
    server: {
        port: 3000,
    },
})
