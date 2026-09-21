import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { DashboardDrawer } from '@/components/game/dashboard-drawer'
import { AppHeader } from '@/components/layout/app-header'
import { PokerTable } from '@/components/poker/poker-table'
import { AnimatedText } from '@/components/ui/animated-shiny-text'
import { useGameSession } from '@/hooks/use-game-session'

// Same treatment as lobby-page.jsx's "READY UP" watermark -- a subtle
// sweeping gradient rather than a flat fill, so the giant background text
// reads as texture rather than competing with the felt table on top of it.
const HOLD_EM_GRADIENT = 'linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.16), rgba(255,255,255,0.03))'

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
        <div className="relative flex min-h-svh flex-col overflow-hidden">
            <AppHeader />
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <AnimatedText
                    text="HOLD 'EM"
                    gradientColors={HOLD_EM_GRADIENT}
                    gradientAnimationDuration={2.5}
                    textClassName="font-black tracking-wide text-[14vw] sm:text-[14vw] md:text-[14vw] lg:text-[14vw] xl:text-[14vw] leading-none whitespace-nowrap"
                />
            </div>
            <main className="relative z-10 flex-1 p-4">
                {errorMessage && <p className="text-center text-sm text-destructive">{errorMessage}</p>}
                {session && (
                    <PokerTable sessionId={sessionId} session={session} onSessionUpdate={refreshSession} />
                )}
            </main>
            <DashboardDrawer sessionId={sessionId} />
        </div>
    )
}

export { GamePage }
