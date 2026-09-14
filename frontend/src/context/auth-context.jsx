import { createContext, useCallback, useEffect, useState } from 'react'

import { apiRequest, getStoredToken, registerUnauthorizedHandler, setStoredToken } from '@/lib/api-client'

const AuthContext = createContext(null)

const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null)
    const [isLoading, setIsLoading] = useState(true)

    const loadCurrentUser = useCallback(async () => {
        if (!getStoredToken()) {
            setUser(null)
            setIsLoading(false)
            return
        }

        try {
            const currentUser = await apiRequest('/auth/me')
            setUser(currentUser)
        } catch {
            setUser(null)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        registerUnauthorizedHandler(() => setUser(null))
        loadCurrentUser()
    }, [loadCurrentUser])

    const login = useCallback(
        async (email, password) => {
            const { access_token: accessToken } = await apiRequest('/auth/login', {
                method: 'POST',
                body: { email, password },
                requiresAuth: false,
            })
            setStoredToken(accessToken)
            await loadCurrentUser()
        },
        [loadCurrentUser],
    )

    const signup = useCallback(
        async (email, password, displayName) => {
            const { access_token: accessToken } = await apiRequest('/auth/signup', {
                method: 'POST',
                body: { email, password, display_name: displayName || null },
                requiresAuth: false,
            })
            setStoredToken(accessToken)
            await loadCurrentUser()
        },
        [loadCurrentUser],
    )

    const logout = useCallback(() => {
        setStoredToken(null)
        setUser(null)
    }, [])

    // Returns the updated user (ProfilePage reads it straight from here for
    // its own "saved" state) while also refreshing the shared `user` so
    // AppHeader's display name updates immediately, without a second request.
    const updateProfile = useCallback(async (profile) => {
        const updated = await apiRequest('/auth/me', { method: 'PATCH', body: profile })
        setUser(updated)
        return updated
    }, [])

    return (
        <AuthContext.Provider value={{ user, isLoading, login, signup, logout, updateProfile }}>
            {children}
        </AuthContext.Provider>
    )
}

export { AuthContext, AuthProvider }
