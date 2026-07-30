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

    return (
        <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

export { AuthContext, AuthProvider }
