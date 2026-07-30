import { useCallback } from 'react'

import { apiRequest } from '@/lib/api-client'

// There's no "list my sessions" backend endpoint (Part 8/9 never needed
// one) -- resuming a session is done client-side by remembering the last
// created session's id and checking whether it's still active. Limited to
// the same browser, but avoids expanding backend scope just for this.
const CURRENT_SESSION_STORAGE_KEY = 'kelly_poker_current_session_id'

const getStoredSessionId = () => {
    const value = localStorage.getItem(CURRENT_SESSION_STORAGE_KEY)
    return value ? Number(value) : null
}

const setStoredSessionId = (sessionId) => {
    if (sessionId) {
        localStorage.setItem(CURRENT_SESSION_STORAGE_KEY, String(sessionId))
    } else {
        localStorage.removeItem(CURRENT_SESSION_STORAGE_KEY)
    }
}

const useGameSession = () => {
    const createSession = useCallback(async ({ botPersona, startingBankroll, kellyMultiplier }) => {
        const session = await apiRequest('/game/sessions', {
            method: 'POST',
            body: {
                bot_persona: botPersona,
                starting_bankroll: startingBankroll || null,
                kelly_multiplier: kellyMultiplier || null,
            },
        })
        setStoredSessionId(session.id)
        return session
    }, [])

    const getSession = useCallback((sessionId) => apiRequest(`/game/sessions/${sessionId}`), [])

    const endSession = useCallback(async (sessionId) => {
        const session = await apiRequest(`/game/sessions/${sessionId}/end`, { method: 'POST' })
        setStoredSessionId(null)
        return session
    }, [])

    return { createSession, getSession, endSession, getStoredSessionId, setStoredSessionId }
}

export { useGameSession }
