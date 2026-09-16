import path from 'path'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(import.meta.dirname, './src'),
        },
    },
    test: {
        environment: 'jsdom',
        setupFiles: ['./src/__tests__/setup.js'],
        globals: true,
        // jsdom's own localStorage throws without a real origin, so the
        // "test" script backs it with Node's --localstorage-file flag --
        // but that backs a single real file shared by every worker THREAD
        // in the process, not a separate store per test file. Running
        // files in parallel therefore lets one file's localStorage.clear()
        // race another file's setStoredToken() and wipe its token before
        // that file's own render ever reads it (a real, observed flake in
        // profile-page.test.jsx/use-auth.test.jsx once enough auth-related
        // test files exist for the timing to collide). Serializing file
        // execution removes the race; the suite is small enough that the
        // wall-clock cost is negligible.
        fileParallelism: false,
    },
})
