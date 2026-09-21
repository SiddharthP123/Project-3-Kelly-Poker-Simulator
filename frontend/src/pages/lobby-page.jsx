import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { AppHeader } from '@/components/layout/app-header'
import { SessionSetupForm } from '@/components/session/session-setup-form'
import { AnimatedText } from '@/components/ui/animated-shiny-text'
import { BorderBeam, EDUCATION_BORDER_BEAM_PROPS } from '@/components/ui/border-beam'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useGameSession } from '@/hooks/use-game-session'
import { formatCurrency } from '@/lib/format'

const READY_UP_GRADIENT = 'linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.16), rgba(255,255,255,0.03))'

const LobbyPage = () => {
    const navigate = useNavigate()
    const { createSession, getSession, getStoredSessionId, setStoredSessionId } = useGameSession()

    const [activeSession, setActiveSession] = useState(null)
    const [isCheckingForActiveSession, setIsCheckingForActiveSession] = useState(true)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [errorMessage, setErrorMessage] = useState('')

    useEffect(() => {
        const checkForActiveSession = async () => {
            const storedSessionId = getStoredSessionId()
            if (!storedSessionId) {
                setIsCheckingForActiveSession(false)
                return
            }

            try {
                const session = await getSession(storedSessionId)
                if (session.status === 'active') {
                    setActiveSession(session)
                } else {
                    setStoredSessionId(null)
                }
            } catch {
                setStoredSessionId(null)
            } finally {
                setIsCheckingForActiveSession(false)
            }
        }

        checkForActiveSession()
    }, [getSession, getStoredSessionId, setStoredSessionId])

    const handleCreateSession = async (formValues) => {
        setErrorMessage('')
        setIsSubmitting(true)

        try {
            const session = await createSession(formValues)
            navigate(`/sessions/${session.id}/play`)
        } catch (error) {
            setErrorMessage(error.detail || 'Could not start a session')
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <div className="relative flex min-h-svh flex-col overflow-hidden">
            <AppHeader />
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <AnimatedText
                    text="READY UP"
                    gradientColors={READY_UP_GRADIENT}
                    gradientAnimationDuration={2.5}
                    textClassName="font-black tracking-wide text-[14vw] sm:text-[14vw] md:text-[14vw] lg:text-[14vw] xl:text-[14vw] leading-none whitespace-nowrap"
                />
            </div>
            <main className="relative z-10 mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-6 p-4">
                {!isCheckingForActiveSession && activeSession && (
                    <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS}>
                        <Card className="border-border bg-transparent ring-0">
                            <CardHeader>
                                <CardTitle>Resume Your Session:</CardTitle>
                                <CardDescription>
                                    {activeSession.num_opponents} Opponent
                                    {activeSession.num_opponents > 1 ? 's' : ''} &mdash;{' '}
                                    {formatCurrency(activeSession.current_bankroll)} Bankroll.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="flex flex-col gap-2">
                                <Button onClick={() => navigate(`/sessions/${activeSession.id}/play`)}>
                                    Keep Playing
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={() => navigate(`/sessions/${activeSession.id}/dashboard`)}
                                >
                                    View Dashboard
                                </Button>
                            </CardContent>
                        </Card>
                    </BorderBeam>
                )}

                {!isCheckingForActiveSession && (
                    <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS}>
                        <Card className="border-border bg-transparent ring-0">
                            <CardHeader>
                                <CardTitle>
                                    {activeSession ? 'Start Your New Session:' : 'Start Your Session:'}
                                </CardTitle>
                                <CardDescription>Choose your opponent and stakes.</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <SessionSetupForm
                                    onSubmit={handleCreateSession}
                                    isSubmitting={isSubmitting}
                                    errorMessage={errorMessage}
                                />
                            </CardContent>
                        </Card>
                    </BorderBeam>
                )}
            </main>
        </div>
    )
}

export { LobbyPage }
