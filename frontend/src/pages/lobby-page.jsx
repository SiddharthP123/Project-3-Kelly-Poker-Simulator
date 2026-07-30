import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { AppHeader } from '@/components/layout/app-header'
import { SessionSetupForm } from '@/components/session/session-setup-form'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useGameSession } from '@/hooks/use-game-session'
import { formatCurrency } from '@/lib/format'

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
        <div className="flex min-h-svh flex-col">
            <AppHeader />
            <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center gap-6 p-4">
                {!isCheckingForActiveSession && activeSession && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Resume your session</CardTitle>
                            <CardDescription>
                                Playing against {activeSession.bot_persona} &mdash;{' '}
                                {formatCurrency(activeSession.current_bankroll)} bankroll
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="flex flex-col gap-2">
                            <Button onClick={() => navigate(`/sessions/${activeSession.id}/play`)}>
                                Keep playing
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => navigate(`/sessions/${activeSession.id}/dashboard`)}
                            >
                                View dashboard
                            </Button>
                        </CardContent>
                    </Card>
                )}

                {!isCheckingForActiveSession && (
                    <Card>
                        <CardHeader>
                            <CardTitle>{activeSession ? 'Start a new session' : 'Start a session'}</CardTitle>
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
                )}
            </main>
        </div>
    )
}

export { LobbyPage }
