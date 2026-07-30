import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { AppHeader } from '@/components/layout/app-header'
import { PokerTable } from '@/components/poker/poker-table'
import { Button } from '@/components/ui/button'
import { useGameSession } from '@/hooks/use-game-session'

const GamePage = () => {
    const { sessionId } = useParams()
    const { getSession } = useGameSession()

    const [session, setSession] = useState(null)
    const [errorMessage, setErrorMessage] = useState('')

    const refreshSession = useCallback(async () => {
        try {
            const updated = await getSession(sessionId)
            setSession(updated)
        } catch (error) {
            setErrorMessage(error.detail || 'Could not load this session')
        }
    }, [getSession, sessionId])

    useEffect(() => {
        refreshSession()
    }, [refreshSession])

    return (
        <div className="flex min-h-svh flex-col">
            <AppHeader />
            <main className="flex-1 p-4">
                <div className="mx-auto mb-4 flex w-full max-w-md justify-end">
                    <Button variant="outline" size="sm" asChild>
                        <Link to={`/sessions/${sessionId}/dashboard`}>View dashboard</Link>
                    </Button>
                </div>
                {errorMessage && <p className="text-center text-sm text-destructive">{errorMessage}</p>}
                {session && (
                    <PokerTable sessionId={sessionId} session={session} onSessionUpdate={refreshSession} />
                )}
            </main>
        </div>
    )
}

export { GamePage }
