import { useCallback, useEffect, useState } from 'react'

import { ActionControls } from '@/components/poker/action-controls'
import { HandResultBanner } from '@/components/poker/hand-result-banner'
import { HoleCards } from '@/components/poker/hole-cards'
import { KellyStakePanel } from '@/components/poker/kelly-stake-panel'
import { Button } from '@/components/ui/button'
import { apiRequest } from '@/lib/api-client'
import { formatCurrency } from '@/lib/format'

/**
 * The deal/act state machine for one session. Driven by GET .../hands/pending
 * on mount so a page refresh mid-decision recovers correctly instead of
 * silently losing the in-progress hand.
 */
const PokerTable = ({ sessionId, session, onSessionUpdate }) => {
    const [pendingHand, setPendingHand] = useState(null)
    const [resolvedHand, setResolvedHand] = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [errorMessage, setErrorMessage] = useState('')

    const loadPendingHand = useCallback(async () => {
        try {
            const hand = await apiRequest(`/game/sessions/${sessionId}/hands/pending`)
            setPendingHand(hand)
            setResolvedHand(null)
        } catch (error) {
            if (error.status !== 404) {
                setErrorMessage(error.detail || 'Could not load the current hand')
            }
            setPendingHand(null)
        } finally {
            setIsLoading(false)
        }
    }, [sessionId])

    useEffect(() => {
        loadPendingHand()
    }, [loadPendingHand])

    const handleDeal = async () => {
        setErrorMessage('')
        setIsSubmitting(true)

        try {
            const hand = await apiRequest(`/game/sessions/${sessionId}/hands/deal`, {
                method: 'POST',
                body: {},
            })
            setPendingHand(hand)
            setResolvedHand(null)
        } catch (error) {
            setErrorMessage(error.detail || 'Could not deal a hand')
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleAct = async (action, raiseAmount) => {
        setErrorMessage('')
        setIsSubmitting(true)

        try {
            const body = { action }
            if (action === 'raise') {
                body.raise_amount = raiseAmount
            }

            const hand = await apiRequest(`/game/sessions/${sessionId}/hands/${pendingHand.id}/act`, {
                method: 'POST',
                body,
            })
            setResolvedHand(hand)
            setPendingHand(null)
            await onSessionUpdate()
        } catch (error) {
            setErrorMessage(error.detail || 'Could not resolve the hand')
        } finally {
            setIsSubmitting(false)
        }
    }

    if (isLoading) {
        return <p className="text-center text-muted-foreground">Loading...</p>
    }

    return (
        <div className="mx-auto flex w-full max-w-md flex-col gap-6">
            <div className="text-center">
                <p className="text-sm text-muted-foreground">Bankroll</p>
                <p className="text-2xl font-semibold">{formatCurrency(session.current_bankroll)}</p>
            </div>

            {errorMessage && <p className="text-center text-sm text-destructive">{errorMessage}</p>}

            {resolvedHand && <HandResultBanner hand={resolvedHand} onDealNext={handleDeal} />}

            {!resolvedHand && !pendingHand && (
                <div className="flex justify-center">
                    <Button onClick={handleDeal} disabled={isSubmitting}>
                        Deal hand
                    </Button>
                </div>
            )}

            {!resolvedHand && pendingHand && (
                <div className="flex flex-col gap-6">
                    <HoleCards cardsString={pendingHand.hero_hole_cards} label="Your hand" />
                    <KellyStakePanel
                        equity={pendingHand.equity_at_decision}
                        kellyRecommendedStake={pendingHand.kelly_recommended_stake}
                        potSize={pendingHand.pot_size}
                        betToCall={pendingHand.bet_to_call}
                        bankroll={session.current_bankroll}
                    />
                    <ActionControls
                        betToCall={pendingHand.bet_to_call}
                        bankroll={session.current_bankroll}
                        suggestedRaiseAmount={pendingHand.kelly_recommended_stake}
                        onAct={handleAct}
                        isSubmitting={isSubmitting}
                    />
                </div>
            )}
        </div>
    )
}

export { PokerTable }
