import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/context/auth-context'
import { useAuth } from '@/hooks/use-auth'
import { getStoredToken } from '@/lib/api-client'

const jsonResponse = (body, { status = 200 } = {}) => ({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () => body,
})

describe('useAuth', () => {
    beforeEach(() => {
        localStorage.clear()
        global.fetch = vi.fn()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    it('throws when used outside an AuthProvider', () => {
        expect(() => renderHook(() => useAuth())).toThrow(/AuthProvider/)
    })

    it('starts with no user and isLoading false when no token is stored', async () => {
        const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })

        await waitFor(() => expect(result.current.isLoading).toBe(false))
        expect(result.current.user).toBeNull()
    })

    it('login stores the token and loads the current user', async () => {
        global.fetch
            .mockResolvedValueOnce(jsonResponse({ access_token: 'tok123', token_type: 'bearer' }))
            .mockResolvedValueOnce(jsonResponse({ id: 1, email: 'me@example.com' }))

        const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
        await waitFor(() => expect(result.current.isLoading).toBe(false))

        await act(async () => {
            await result.current.login('me@example.com', 'password123')
        })

        expect(getStoredToken()).toBe('tok123')
        expect(result.current.user).toEqual({ id: 1, email: 'me@example.com' })
    })

    it('logout clears the token and the user', async () => {
        global.fetch
            .mockResolvedValueOnce(jsonResponse({ access_token: 'tok123', token_type: 'bearer' }))
            .mockResolvedValueOnce(jsonResponse({ id: 1, email: 'me@example.com' }))

        const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
        await waitFor(() => expect(result.current.isLoading).toBe(false))

        await act(async () => {
            await result.current.login('me@example.com', 'password123')
        })

        act(() => {
            result.current.logout()
        })

        expect(getStoredToken()).toBeNull()
        expect(result.current.user).toBeNull()
    })
})
