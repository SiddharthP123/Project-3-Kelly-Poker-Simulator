import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
    ApiError,
    apiRequest,
    getStoredToken,
    registerUnauthorizedHandler,
    setStoredToken,
} from '@/lib/api-client'

const jsonResponse = (body, { status = 200, headers = {} } = {}) => ({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (key) => headers[key] ?? null },
    json: async () => body,
})

describe('apiRequest', () => {
    beforeEach(() => {
        localStorage.clear()
        global.fetch = vi.fn()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    it('attaches the Authorization header when a token is stored', async () => {
        setStoredToken('abc123')
        global.fetch.mockResolvedValue(jsonResponse({ ok: true }))

        await apiRequest('/some-path')

        const [, options] = global.fetch.mock.calls[0]
        expect(options.headers.Authorization).toBe('Bearer abc123')
    })

    it('does not attach an Authorization header when requiresAuth is false', async () => {
        setStoredToken('abc123')
        global.fetch.mockResolvedValue(jsonResponse({ ok: true }))

        await apiRequest('/auth/login', { requiresAuth: false })

        const [, options] = global.fetch.mock.calls[0]
        expect(options.headers.Authorization).toBeUndefined()
    })

    it('clears the token and calls the unauthorized handler on 401', async () => {
        setStoredToken('abc123')
        const handler = vi.fn()
        registerUnauthorizedHandler(handler)
        global.fetch.mockResolvedValue(jsonResponse({ detail: 'nope' }, { status: 401 }))

        await expect(apiRequest('/protected')).rejects.toThrow(ApiError)

        expect(getStoredToken()).toBeNull()
        expect(handler).toHaveBeenCalled()
    })

    it('flattens FastAPI 422 validation errors into a readable message', async () => {
        global.fetch.mockResolvedValue(
            jsonResponse(
                { detail: [{ loc: ['body', 'password'], msg: 'too short', type: 'value_error' }] },
                { status: 422 },
            ),
        )

        const error = await apiRequest('/auth/signup', { requiresAuth: false }).catch((error) => error)

        expect(error).toBeInstanceOf(ApiError)
        expect(error.status).toBe(422)
        expect(error.detail).toBe('password: too short')
    })

    it('surfaces the Retry-After header on 429', async () => {
        global.fetch.mockResolvedValue(
            jsonResponse({ error: 'rate limited' }, { status: 429, headers: { 'Retry-After': '900' } }),
        )

        const error = await apiRequest('/auth/login', { requiresAuth: false }).catch((error) => error)

        expect(error.status).toBe(429)
        expect(error.retryAfter).toBe(900)
    })

    it('returns the parsed body on success', async () => {
        global.fetch.mockResolvedValue(jsonResponse({ id: 1, email: 'a@b.com' }))

        const result = await apiRequest('/auth/me')

        expect(result).toEqual({ id: 1, email: 'a@b.com' })
    })
})
