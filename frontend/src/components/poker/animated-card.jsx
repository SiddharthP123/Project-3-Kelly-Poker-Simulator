import { AnimatePresence, motion } from 'framer-motion'

const SUIT_GLYPHS = { h: '♥', d: '♦', c: '♣', s: '♠' }
const RED_SUITS = new Set(['h', 'd'])

const SIZE_CLASSES = {
    sm: 'h-14 w-10 text-sm',
    md: 'h-20 w-14 text-lg',
    // Hero's own hand in the side panel (Part 14 Phase 1) -- bigger than
    // "md" (used for board/other-seat cards) so the panel actually fills
    // the width it's given instead of leaving visible empty space.
    lg: 'h-28 w-20 text-2xl',
    // Exactly 1.25x "lg" (h-28/w-20 -> h-[8.75rem]/w-[6.25rem]), for the
    // game page's own 1.25x scale-up of its whole board.
    xl: 'h-[8.75rem] w-[6.25rem] text-3xl',
}

/**
 * The animated counterpart to PlayingCard -- same rendering rules (always
 * a light face/dark back regardless of the app's own theme), but animates
 * every transition a real deal actually goes through instead of popping
 * cards in/out instantly:
 *
 * - "dealt" false -> true: a deal-in entrance (fade + slight rise), once,
 *   the moment a card first appears on the table -- whether it's shown
 *   face-down (an opponent's hidden hole cards) or already face-up (the
 *   board, which real dealers place face-up directly, never face-down
 *   then flipped).
 * - "card" null -> a real value while already dealt: a 3D flip, not an
 *   instant swap -- this is specifically the showdown-reveal moment
 *   (an opponent's hole cards going from hidden to shown).
 *
 * dealt/card are intentionally two separate props (not one nullable
 * "card" prop) because "not dealt yet" and "dealt face-down" are
 * genuinely different states that need different treatment -- a
 * not-yet-dealt slot renders nothing at all, while a dealt-face-down slot
 * renders a card back and is what flips when revealed.
 */
const AnimatedCard = ({ dealt, card = null, size = 'md', dealDelay = 0 }) => {
    const sizeClass = SIZE_CLASSES[size] || SIZE_CLASSES.md

    return (
        <AnimatePresence>
            {dealt && (
                <motion.div
                    className={`relative ${sizeClass}`}
                    style={{ perspective: 600 }}
                    initial={{ opacity: 0, y: -14, scale: 0.85 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.85 }}
                    transition={{ duration: 0.25, delay: dealDelay }}
                >
                    <motion.div
                        className="absolute inset-0"
                        style={{ transformStyle: 'preserve-3d' }}
                        animate={{ rotateY: card ? 180 : 0 }}
                        transition={{ duration: 0.4, delay: card ? dealDelay : 0 }}
                    >
                        <div
                            className="absolute inset-0 flex items-center justify-center rounded-lg border border-white/20 bg-gradient-to-br from-zinc-700 to-zinc-900 shadow-sm"
                            style={{ backfaceVisibility: 'hidden' }}
                        >
                            <span className="text-white/30">◆</span>
                        </div>
                        {card && (
                            <div
                                className={`absolute inset-0 flex flex-col items-center justify-center rounded-lg border border-black/10 bg-white shadow-sm ${
                                    RED_SUITS.has(card.slice(-1)) ? 'text-red-600' : 'text-zinc-900'
                                }`}
                                style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
                            >
                                <span className="font-semibold leading-none">{card.slice(0, -1)}</span>
                                <span className="text-[1.4em] leading-none">{SUIT_GLYPHS[card.slice(-1)]}</span>
                            </div>
                        )}
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    )
}

export { AnimatedCard }
