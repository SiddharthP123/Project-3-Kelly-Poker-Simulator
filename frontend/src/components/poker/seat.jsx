import { AnimatePresence, motion } from 'framer-motion'

import { AnimatedCard } from '@/components/poker/animated-card'
import { formatCurrency, formatPersonaLabel } from '@/lib/format'

/**
 * One seat at the table -- hero or an opponent. Redaction is entirely the
 * backend's job (HandPlayerResponse.hole_cards is null unless this seat
 * has earned the right to be seen): this component never decides whether
 * to show a card, only how -- a null hole_cards renders as face-down
 * placeholders for a non-hero seat, and nothing at all once a seat has
 * folded (a folded hand isn't still sitting face-down on the table in
 * real poker, it's mucked -- gone).
 *
 * dealDelay staggers the deal-in animation across seats (seat_index order,
 * mirroring how a real dealer deals one card to each player in rotation
 * rather than dealing one player's whole hand at once) -- passed straight
 * through to AnimatedCard, which only actually plays it once per card,
 * the moment that card first appears.
 *
 * actionLabel is `{ id, text }` (or undefined) -- PokerTable derives it
 * from the hand's own `actions` log and clears it again after a couple
 * seconds, so this component just renders whatever it's handed. `id`
 * (not `text`) is the AnimatePresence key so two consecutive identical
 * actions (e.g. "Checks" twice) still replay the fade in/out.
 */
const Seat = ({ player, isButton, dealDelay = 0, actionLabel }) => {
    const label = player.is_hero ? 'You' : formatPersonaLabel(player.persona)
    const showCards = !player.folded
    const cards = player.hole_cards ? player.hole_cards.split(',') : [null, null]

    return (
        <div className="relative flex flex-col items-center gap-1.5">
            <AnimatePresence>
                {actionLabel && (
                    <motion.span
                        key={actionLabel.id}
                        className="absolute -top-6 z-10 rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap text-black shadow"
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        transition={{ duration: 0.2 }}
                    >
                        {actionLabel.text}
                    </motion.span>
                )}
            </AnimatePresence>

            <div className="flex items-center gap-1">
                {showCards && (
                    <div className="flex gap-1">
                        {cards.map((card, index) => (
                            // Keyed by slot position, not card value, so this
                            // is the SAME element across a reveal (card going
                            // from null to a real value) -- that's what lets
                            // AnimatedCard flip it in place instead of one
                            // element unmounting and a different one mounting.
                            <AnimatedCard
                                key={index}
                                dealt
                                card={card}
                                size="md"
                                dealDelay={dealDelay + index * 0.06}
                            />
                        ))}
                    </div>
                )}
            </div>

            <motion.div
                className={`flex flex-col items-center rounded-md border px-3 py-1.5 text-center ${
                    player.is_winner ? 'border-white bg-white text-black' : 'border-white/15 bg-black/40 text-white'
                }`}
                animate={
                    player.is_winner
                        ? { scale: [1, 1.08, 1], boxShadow: ['0 0 0px #fff0', '0 0 18px #fff9', '0 0 0px #fff0'] }
                        : { scale: 1 }
                }
                transition={player.is_winner ? { duration: 1.1, repeat: 2 } : { duration: 0.2 }}
            >
                <div className="flex items-center gap-1.5">
                    {isButton && (
                        <span
                            className="flex h-4 w-4 items-center justify-center rounded-full bg-white text-[10px] font-bold text-black"
                            title="Dealer button"
                        >
                            D
                        </span>
                    )}
                    <span className="text-xs font-medium">{label}</span>
                </div>
                <span className="text-sm font-semibold tabular-nums">{formatCurrency(player.stack)}</span>
                {player.folded && <span className="text-[10px] uppercase tracking-wide text-white/50">Folded</span>}
                {!player.folded && player.all_in && (
                    <span className="text-[10px] uppercase tracking-wide text-red-500">All-in</span>
                )}
            </motion.div>
        </div>
    )
}

export { Seat }
