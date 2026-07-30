/**
 * Fetch-based API client. No axios -- keeps dependencies minimal, and
 * fetch + async/await is all this project actually needs.
 *
 * Key insight: api-client never imports auth-context directly (that would
 * create a circular import, since auth-context imports this module to
 * make requests). Instead, AuthProvider registers a callback via
 * registerUnauthorizedHandler at app startup, and this module calls it
 * whenever a 401 comes back -- a one-way dependency instead of a cycle.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const TOKEN_STORAGE_KEY = 'kelly_poker_token'

let onUnauthorized = () => {}

const registerUnauthorizedHandler = (handler) => {
    onUnauthorized = handler
}

const getStoredToken = () => localStorage.getItem(TOKEN_STORAGE_KEY)

const setStoredToken = (token) => {
    if (token) {
        localStorage.setItem(TOKEN_STORAGE_KEY, token)
    } else {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
    }
}

class ApiError extends Error {
    constructor(status, detail, retryAfter = null) {
        super(typeof detail === 'string' ? detail : 'Request failed')
        this.name = 'ApiError'
        this.status = status
        this.detail = detail
        this.retryAfter = retryAfter
    }
}

// FastAPI's default 422 body shape: {"detail": [{"loc", "msg", "type"}, ...]}
const parseValidationDetail = (body) => {
    if (!Array.isArray(body?.detail)) {
        return body?.detail || 'Invalid request'
    }

    return body.detail
        .map((issue) => {
            const field = issue.loc?.[issue.loc.length - 1]
            return field ? `${field}: ${issue.msg}` : issue.msg
        })
        .join('; ')
}

const apiRequest = async (path, { method = 'GET', body, requiresAuth = true } = {}) => {
    const headers = { 'Content-Type': 'application/json' }

    if (requiresAuth) {
        const token = getStoredToken()
        if (token) {
            headers.Authorization = `Bearer ${token}`
        }
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
    })

    if (response.status === 204) {
        return null
    }

    const responseBody = await response.json().catch(() => null)

    if (response.ok) {
        return responseBody
    }

    if (response.status === 401) {
        setStoredToken(null)
        onUnauthorized()
        throw new ApiError(401, responseBody?.detail || 'Session expired -- please log in again')
    }

    if (response.status === 422) {
        throw new ApiError(422, parseValidationDetail(responseBody))
    }

    if (response.status === 429) {
        const retryAfter = Number(response.headers.get('Retry-After')) || null
        throw new ApiError(429, responseBody?.detail || 'Too many requests', retryAfter)
    }

    throw new ApiError(response.status, responseBody?.detail || 'Request failed')
}

export { apiRequest, ApiError, getStoredToken, setStoredToken, registerUnauthorizedHandler }
