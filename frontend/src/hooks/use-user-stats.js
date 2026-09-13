import { useCallback } from 'react'

import { apiRequest } from '@/lib/api-client'

const useUserStats = () => {
    const getMyStats = useCallback(() => apiRequest('/users/me/stats'), [])

    return { getMyStats }
}

export { useUserStats }
