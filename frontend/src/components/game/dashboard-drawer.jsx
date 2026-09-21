import { motion } from 'framer-motion'
import { useState } from 'react'

import { SessionDashboardPanel } from '@/components/game/session-dashboard-panel'

/**
 * A dashboard you pull out of the right edge of the screen mid-game,
 * rather than navigating to a separate page -- a fixed panel that slides
 * in from off-screen, with a vertical-text tab attached to its left edge
 * (visible even when closed, like a folder tab peeking out of a drawer).
 *
 * A thin permanent strip sits at the very right edge of the screen
 * (outside the sliding panel, so it stays put even when the panel is
 * fully closed) -- the tab reads as mounted onto that strip, like a
 * folder tab attached to the spine of the folder, rather than floating
 * alone in empty space.
 *
 * The tab sits at a negative `left` relative to the panel, so it rides
 * along with the panel's own slide animation instead of needing separate
 * positioning logic for open vs. closed. It's clipped into a trapezoid
 * (full height at the edge attached to the panel, narrower at the tip
 * sticking into the page) with each corner chamfered -- a lightweight
 * stand-in for a true rounded fillet, since clip-path's polygon() only
 * draws straight edges -- so the tab reads as a folder tab rather than a
 * sharp-cornered rectangle. The label text is rotated 180deg on top of
 * vertical-rl so it reads bottom-to-top (the "D" sits at the bottom).
 *
 * `openCount` remounts SessionDashboardPanel on every open (fresh `key`),
 * so the numbers reflect whatever's happened in the game since it was
 * last pulled out, without polling while it's closed.
 */
const TAB_CLIP_PATH =
    '[clip-path:polygon(85%_3.75%,100%_6.25%,100%_93.75%,85%_96.25%,15%_78.75%,0%_68.75%,0%_31.25%,15%_21.25%)]'

const DashboardDrawer = ({ sessionId }) => {
    const [isOpen, setIsOpen] = useState(false)
    const [hasOpenedOnce, setHasOpenedOnce] = useState(false)
    const [openCount, setOpenCount] = useState(0)

    const toggleOpen = () => {
        setIsOpen((wasOpen) => {
            const nextIsOpen = !wasOpen
            if (nextIsOpen) {
                setHasOpenedOnce(true)
                setOpenCount((count) => count + 1)
            }
            return nextIsOpen
        })
    }

    return (
        <>
            <div className="fixed top-0 right-0 z-20 h-full w-3 border-l border-white/10 bg-zinc-900" />

            <motion.div
                className="fixed top-0 right-0 z-30 h-full w-[92vw] max-w-xl"
                animate={{ x: isOpen ? 0 : '100%' }}
                initial={false}
                transition={{ type: 'spring', stiffness: 300, damping: 32 }}
            >
                <div className="absolute top-1/2 -left-16 -translate-y-1/2">
                    <button
                        type="button"
                        onClick={toggleOpen}
                        aria-label={isOpen ? 'Close dashboard' : 'Open dashboard'}
                        aria-expanded={isOpen}
                        className={`flex h-48 w-16 cursor-pointer items-center justify-center border border-white/15 bg-zinc-900 text-base font-semibold tracking-wide text-foreground hover:bg-zinc-800 ${TAB_CLIP_PATH}`}
                    >
                        <span className="rotate-180 [writing-mode:vertical-rl]">Dashboard:</span>
                    </button>
                </div>

                <div className="h-full overflow-y-auto border-l border-white/15 bg-zinc-950/95 p-4 shadow-2xl backdrop-blur-md">
                    {hasOpenedOnce && <SessionDashboardPanel key={openCount} sessionId={sessionId} />}
                </div>
            </motion.div>
        </>
    )
}

export { DashboardDrawer }
