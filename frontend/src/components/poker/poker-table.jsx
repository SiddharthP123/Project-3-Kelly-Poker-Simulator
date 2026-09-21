import { AnimatePresence, motion } from 'framer-motion'
import { useCallback, useEffect, useRef, useState } from 'react'

import { ActionControls } from '@/components/poker/action-controls'
import { AnimatedCard } from '@/components/poker/animated-card'
import { HandResultBanner } from '@/components/poker/hand-result-banner'
import { KellyStakePanel } from '@/components/poker/kelly-stake-panel'
import { Seat } from '@/components/poker/seat'
import { Button } from '@/components/ui/button'
import { BorderBeam, EDUCATION_BORDER_BEAM_PROPS } from '@/components/ui/border-beam'
import { apiRequest } from '@/lib/api-client'
import { formatCurrency, formatPersonaLabel } from '@/lib/format'
import { getSeatPosition } from '@/lib/seat-positions'

const BOARD_SLOTS = 5
const POT_POSITION = { top: '50%', left: '50%' }
const ACTION_LABEL_TTL_MS = 1500

/**
 * action.action is the engine's own low-level vocabulary
 * ('post_blind' | 'fold' | 'match' | 'raise_to', see poker/betting.py's
 * BettingAction), and action.amount is the incremental chips moved by
 * that one action -- not a "raise to" total, which the API never sends
 * for a seat other than hero's own current decision. "Raises +$X" is
 * therefore the accurate label, not "Raises to $X".
 */
const formatActionLabel = (action) => {
    switch (action.action) {
        case 'fold':
            return 'Folds'
        case 'match':
            return action.amount > 0 ? `Calls ${formatCurrency(action.amount)}` : 'Checks'
        case 'raise_to':
            return `Raises +${formatCurrency(action.amount)}`
        case 'post_blind':
            return `Posts ${formatCurrency(action.amount)}`
        default:
            return action.action
    }
}

/**
 * Idle-state stand-in for Seat -- used before a hand exists, when there's
 * no HandPlayerResponse yet to hand Seat, just session.opponents' own
 * seat_index/persona. Outlined/dashed throughout (matching the existing
 * undealt-board-slot pattern) so it reads as "waiting for a hand," not a
 * real dealt seat.
 */
const SeatPlaceholder = ({ label }) => (
    <div className="flex flex-col items-center gap-1.5">
        <div className="flex gap-1">
            <div className="h-28 w-20 rounded-lg border border-dashed border-white/15" />
            <div className="h-28 w-20 rounded-lg border border-dashed border-white/15" />
        </div>
        <div className="rounded-md border border-dashed border-white/15 px-3 py-1.5 text-center">
            <span className="text-xs font-medium text-white/40">{label}</span>
        </div>
    </div>
)

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
 *
 * The felt/seats/board subtree is keyed by hand.id so a genuinely NEW
 * hand remounts it -- that's what makes the deal-in animations replay
 * for the new hand while NOT replaying on every action within the same
 * hand (a street advancing, or an action resolving, only changes props
 * on the already-mounted seat/card elements, which AnimatedCard only
 * animates for the specific state transition it represents -- see its
 * own docstring). Before any hand exists, the felt still renders --
 * seats/board are outlined placeholders built from `session.opponents`,
 * so the table always looks like a real table waiting for a hand rather
 * than a blank area with just a button on it.
 */
const PokerTable = ({ sessionId, session, onSessionUpdate }) => {
    const [hand, setHand] = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [errorMessage, setErrorMessage] = useState('')
    const [actionLabels, setActionLabels] = useState({})
    const previousHandIdRef = useRef(null)

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

    // Shows each seat's just-resolved action as a transient label, driven
    // entirely off hand.actions (never re-derived or recomputed -- see
    // formatActionLabel). A brand-new hand.id (a fresh deal, or the very
    // first hand recovered on page load) is treated as a remount, not an
    // update -- its already-included setup actions (blinds) establish the
    // baseline silently instead of flashing a burst of toasts the instant
    // the table remounts. Only a later response for the SAME hand.id (an
    // `act` call resolving bot turns and/or hero's own action) toasts.
    useEffect(() => {
        if (!hand) {
            previousHandIdRef.current = null
            return undefined
        }

        const isNewHand = hand.id !== previousHandIdRef.current
        previousHandIdRef.current = hand.id
        if (isNewHand) {
            return undefined
        }

        const newActions = hand.actions || []
        if (newActions.length === 0) {
            return undefined
        }

        const entries = newActions.map((action) => [
            action.seat_index,
            { id: `${hand.id}-${action.seq}`, text: formatActionLabel(action) },
        ])

        setActionLabels((previous) => ({ ...previous, ...Object.fromEntries(entries) }))

        const timeoutId = setTimeout(() => {
            setActionLabels((previous) => {
                const next = { ...previous }
                entries.forEach(([seatIndex, entry]) => {
                    if (next[seatIndex]?.id === entry.id) {
                        delete next[seatIndex]
                    }
                })
                return next
            })
        }, ACTION_LABEL_TTL_MS)

        return () => clearTimeout(timeoutId)
    }, [hand])

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
    const hero = hand?.players.find((player) => player.is_hero)
    const heroCards = hero?.hole_cards ? hero.hole_cards.split(',') : []

    const idleSeats = [
        { seat_index: 0, label: 'You' },
        ...(session.opponents || []).map((opponent) => ({
            seat_index: opponent.seat_index,
            label: formatPersonaLabel(opponent.persona),
        })),
    ]

    return (
        <div className="mx-auto flex h-full min-h-0 w-[97%] max-w-[1600px] flex-col gap-6">
            <h1 className="text-center text-3xl font-bold text-white">
                Bankroll: <span className="text-white/50">{formatCurrency(session.current_bankroll)}</span>
            </h1>

            {errorMessage && <p className="text-center text-sm text-destructive">{errorMessage}</p>}

            {/* flex-1/min-h-0 so this row fills whatever height is left under
                the heading above -- the felt and the action card each derive
                their own size from that (definite) height rather than the
                felt's aspect-ratio pushing the page taller than the viewport
                and forcing a scrollbar. */}
            <div className="flex min-h-0 flex-1 flex-col gap-8 rounded-xl border-2 border-white/25 p-8 lg:flex-row lg:items-stretch">
                <div className="relative h-full flex-1">
                    <div
                        key={hand?.id ?? 'idle'}
                        className="relative h-full w-full rounded-3xl border border-white/10 bg-gradient-to-b from-emerald-800/55 to-emerald-950/55 shadow-[inset_0_2px_8px_rgba(0,0,0,0.4)]"
                    >
                        {/* Purely decorative -- a second, inset rounded border
                            echoing the felt's own outer edge, like the inlay
                            line on a real poker table. */}
                        <div className="pointer-events-none absolute inset-6 rounded-2xl border border-dotted border-white/30" />

                        {(hand ? hand.players : idleSeats).map((seatEntry) => (
                            <div
                                key={seatEntry.seat_index}
                                className="absolute -translate-x-1/2 -translate-y-1/2"
                                style={getSeatPosition(seatEntry.seat_index, session.num_opponents)}
                            >
                                {hand ? (
                                    <Seat
                                        player={seatEntry}
                                        isButton={seatEntry.seat_index === hand.button_seat}
                                        dealDelay={seatEntry.seat_index * 0.12}
                                        actionLabel={actionLabels[seatEntry.seat_index]}
                                    />
                                ) : (
                                    <SeatPlaceholder label={seatEntry.label} />
                                )}
                            </div>
                        ))}

                        <div className="absolute top-1/2 left-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-2">
                            {hand && (
                                <AnimatePresence mode="popLayout">
                                    <motion.p
                                        key={hand.pot_size}
                                        className="text-2xl font-bold text-white"
                                        initial={{ opacity: 0, scale: 0.8 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                    >
                                        Pot: {formatCurrency(hand.pot_size)}
                                    </motion.p>
                                </AnimatePresence>
                            )}
                            {/* Purely decorative -- a red ring around just the
                                board, offset from (not touching) the felt's
                                own outer/inset borders. */}
                            <div className="rounded-xl border-2 border-red-500/70 p-3">
                                <div className="flex gap-3">
                                    {Array.from({ length: BOARD_SLOTS }, (_, index) => index).map((index) =>
                                        boardCards[index] ? (
                                            <AnimatedCard
                                                key={index}
                                                dealt
                                                card={boardCards[index]}
                                                size="lg"
                                                dealDelay={index * 0.15}
                                            />
                                        ) : (
                                            <div
                                                key={index}
                                                className="h-28 w-20 rounded-lg border border-dashed border-white/15"
                                            />
                                        ),
                                    )}
                                </div>
                            </div>
                        </div>

                        {isComplete &&
                            hand.winners.map((winnerSeat) => (
                                <motion.div
                                    key={`${hand.id}-chip-${winnerSeat}`}
                                    className="pointer-events-none absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white shadow-[0_0_8px_2px_rgba(255,255,255,0.6)]"
                                    initial={{ ...POT_POSITION, opacity: 0 }}
                                    animate={{
                                        ...getSeatPosition(winnerSeat, session.num_opponents),
                                        opacity: [0, 1, 1, 0],
                                    }}
                                    transition={{ duration: 0.9, ease: 'easeInOut' }}
                                />
                            ))}
                    </div>

                    {!hand && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <Button onClick={handleDeal} disabled={isSubmitting}>
                                Deal hand
                            </Button>
                        </div>
                    )}
                </div>

                <div className="flex h-full w-full flex-col lg:w-[440px] lg:shrink-0">
                    <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS} className="h-full">
                        <div className="flex h-full w-full flex-col gap-4 overflow-y-auto rounded-lg border border-white/15 bg-black/30 p-6">
                            {/* flex-1 so this section absorbs whatever height the
                                rest of the card doesn't use, keeping the card's
                                own top AND bottom edges aligned with the felt
                                table beside it (see the row's items-stretch)
                                instead of leaving a gap below a shorter card. */}
                            <div className="flex flex-1 flex-col items-center justify-center gap-3">
                                {hand ? (
                                    <>
                                        <p className="text-3xl font-bold text-white">Your Hand:</p>
                                        <div className="flex gap-3">
                                            {heroCards.length > 0
                                                ? heroCards.map((card, index) => (
                                                      <AnimatedCard
                                                          key={index}
                                                          dealt
                                                          card={card}
                                                          size="xl"
                                                          dealDelay={index * 0.06}
                                                      />
                                                  ))
                                                : [0, 1].map((index) => (
                                                      <div
                                                          key={index}
                                                          className="h-[8.75rem] w-[6.25rem] rounded-lg border border-dashed border-white/15"
                                                      />
                                                  ))}
                                        </div>
                                        <p className="text-2xl font-semibold tabular-nums text-white">
                                            {formatCurrency(hero?.stack ?? 0)}
                                        </p>
                                    </>
                                ) : (
                                    <p className="text-center text-sm text-white/50">
                                        Deal a hand to see your cards, equity, and actions here.
                                    </p>
                                )}
                            </div>

                            {isComplete && (
                                <div className="border-t border-white/10 pt-4">
                                    <HandResultBanner hand={hand} onDealNext={handleDeal} />
                                </div>
                            )}
                            {hand && !isComplete && hand.legal_action_bounds && (
                                <>
                                    <div className="border-t border-white/10 pt-4">
                                        <KellyStakePanel
                                            equity={hand.equity_at_decision}
                                            kellyRecommendedStake={hand.kelly_recommended_stake}
                                            potSize={hand.pot_size}
                                            callAmount={hand.legal_action_bounds.call_amount}
                                            bankroll={session.current_bankroll}
                                        />
                                    </div>
                                    <div className="border-t border-white/10 pt-4">
                                        <ActionControls
                                            legalActionBounds={hand.legal_action_bounds}
                                            onAct={handleAct}
                                            isSubmitting={isSubmitting}
                                        />
                                    </div>
                                </>
                            )}
                        </div>
                    </BorderBeam>
                </div>
            </div>
        </div>
    )
}

export { PokerTable }
