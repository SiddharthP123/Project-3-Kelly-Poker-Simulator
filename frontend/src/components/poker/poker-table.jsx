import { useCallback, useEffect, useState } from 'react'

import { ActionControls } from '@/components/poker/action-controls'
import { HandResultBanner } from '@/components/poker/hand-result-banner'
import { PlayingCard } from '@/components/poker/playing-card'
import { Seat } from '@/components/poker/seat'
import { Button } from '@/components/ui/button'
import { apiRequest } from '@/lib/api-client'
import { formatCurrency } from '@/lib/format'
import { getSeatPosition } from '@/lib/seat-positions'

const BOARD_SLOTS = 5

/**
 * The deal/act state machine for one session, now driving a multi-seat,
 * multi-street hand instead of Parts 8-10's single fixed-pot decision.
 * Driven by GET .../hands/pending on mount so a page refresh mid-hand
 * recovers correctly instead of silently losing progress.
 *
 * A single `hand` (the backend's HandResponse) is now the only state
 * that matters -- unlike the old pendingHand/resolvedHand split, this
 * response's own `street` field ('preflop'..'river' or 'complete') is
 * what distinguishes "hero has a decision" from "hand is over," so there's
 * nothing else to track separately.
 */
const PokerTable = ({ sessionId, session, onSessionUpdate }) => {
    const [hand, setHand] = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [errorMessage, setErrorMessage] = useState('')

    const loadPendingHand = useCallback(async () => {
        try {
            const pending = await apiRequest(`/game/sessions/${sessionId}/hands/pending`)
            setHand(pending)
        } catch (error) {
            if (error.status !== 404) {
                setErrorMessage(error.detail || 'Could not load the current hand')
            }
            setHand(null)
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
            const dealt = await apiRequest(`/game/sessions/${sessionId}/hands/deal`, {
                method: 'POST',
                body: {},
            })
            setHand(dealt)
        } catch (error) {
            setErrorMessage(error.detail || 'Could not deal a hand')
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleAct = async (action, raiseTo) => {
        setErrorMessage('')
        setIsSubmitting(true)

        try {
            const body = { action }
            if (action === 'raise') {
                body.raise_to = raiseTo
            }

            const updated = await apiRequest(`/game/sessions/${sessionId}/hands/${hand.id}/act`, {
                method: 'POST',
                body,
            })
            setHand(updated)
            if (updated.street === 'complete') {
                await onSessionUpdate()
            }
        } catch (error) {
            setErrorMessage(error.detail || 'Could not resolve the hand')
        } finally {
            setIsSubmitting(false)
        }
    }

    if (isLoading) {
        return <p className="text-center text-white/60">Loading...</p>
    }

    const boardCards = hand?.board_cards ? hand.board_cards.split(',') : []
    const isComplete = hand?.street === 'complete'

    return (
        <div className="mx-auto flex w-full max-w-3xl flex-col items-center gap-6">
            <div className="text-center text-white">
                <p className="text-sm text-white/60">Bankroll</p>
                <p className="text-2xl font-semibold">{formatCurrency(session.current_bankroll)}</p>
            </div>

            {errorMessage && <p className="text-center text-sm text-destructive">{errorMessage}</p>}

            {!hand && (
                <div className="flex justify-center">
                    <Button onClick={handleDeal} disabled={isSubmitting}>
                        Deal hand
                    </Button>
                </div>
            )}

            {hand && (
                <>
                    <div className="relative aspect-[16/10] w-full rounded-[999px] border-4 border-white/10 bg-gradient-to-b from-zinc-800 to-black shadow-inner">
                        {hand.players.map((player) => (
                            <div
                                key={player.seat_index}
                                className="absolute -translate-x-1/2 -translate-y-1/2"
                                style={getSeatPosition(player.seat_index, session.num_opponents)}
                            >
                                <Seat player={player} isButton={player.seat_index === hand.button_seat} />
                            </div>
                        ))}

                        <div className="absolute top-1/2 left-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-2">
                            <p className="text-sm font-medium text-white/70">
                                Pot: {formatCurrency(hand.pot_size)}
                            </p>
                            <div className="flex gap-1.5">
                                {Array.from({ length: BOARD_SLOTS }, (_, index) => index).map((index) =>
                                    boardCards[index] ? (
                                        <PlayingCard key={boardCards[index]} card={boardCards[index]} size="sm" />
                                    ) : (
                                        <div
                                            key={index}
                                            className="h-14 w-10 rounded-lg border border-dashed border-white/15"
                                        />
                                    ),
                                )}
                            </div>
                        </div>
                    </div>

                    {isComplete && <HandResultBanner hand={hand} onDealNext={handleDeal} />}
                    {!isComplete && hand.legal_action_bounds && (
                        <ActionControls
                            legalActionBounds={hand.legal_action_bounds}
                            onAct={handleAct}
                            isSubmitting={isSubmitting}
                        />
                    )}
                </>
            )}
        </div>
    )
}

export { PokerTable }
