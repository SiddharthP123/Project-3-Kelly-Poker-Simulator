import { useCallback } from 'react'

import { apiRequest } from '@/lib/api-client'

const useHandHistory = () => {
    const getHandHistory = useCallback(
        (sessionId) => apiRequest(`/game/sessions/${sessionId}/hands?limit=200`),
        [],
    )

    const getBankrollHistory = useCallback(
        (sessionId) => apiRequest(`/game/sessions/${sessionId}/bankroll-history`),
        [],
    )

    return { getHandHistory, getBankrollHistory }
}

export { useHandHistory }
