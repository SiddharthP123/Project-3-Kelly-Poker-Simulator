import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ProtectedRoute } from '@/components/layout/protected-route'
import { AuthProvider } from '@/context/auth-context'
import { setStoredToken } from '@/lib/api-client'

const jsonResponse = (body, { status = 200 } = {}) => ({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () => body,
})

const renderProtected = (initialEntry) =>
    render(
        <MemoryRouter initialEntries={[initialEntry]}>
            <AuthProvider>
                <Routes>
                    <Route path="/login" element={<div>Login page</div>} />
                    <Route element={<ProtectedRoute />}>
                        <Route path="/" element={<div>Secret content</div>} />
                    </Route>
                </Routes>
            </AuthProvider>
        </MemoryRouter>,
    )

describe('ProtectedRoute', () => {
    beforeEach(() => {
        localStorage.clear()
        global.fetch = vi.fn()
    })

    it('redirects to /login when there is no authenticated user', async () => {
        renderProtected('/')

        await waitFor(() => expect(screen.getByText('Login page')).toBeInTheDocument())
        expect(screen.queryByText('Secret content')).not.toBeInTheDocument()
    })

    it('renders the protected content once a user is loaded', async () => {
        setStoredToken('tok123')
        global.fetch.mockResolvedValue(jsonResponse({ id: 1, email: 'me@example.com' }))

        renderProtected('/')

        await waitFor(() => expect(screen.getByText('Secret content')).toBeInTheDocument())
    })
})
