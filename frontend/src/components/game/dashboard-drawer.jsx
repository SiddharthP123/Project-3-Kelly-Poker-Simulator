import { motion } from 'framer-motion'
import { useState } from 'react'

import { SessionDashboardPanel } from '@/components/game/session-dashboard-panel'
import { BorderBeam, EDUCATION_BORDER_BEAM_PROPS } from '@/components/ui/border-beam'

/**
 * A dashboard you pull out of the right edge of the screen mid-game,
 * rather than navigating to a separate page -- a fixed panel that slides
 * in from off-screen, with a vertical-text tab attached to its left edge
 * (visible even when closed, like a folder tab peeking out of a drawer).
 *
 * The tab sits at `left: -2.5rem` relative to the panel, so it rides
 * along with the panel's own slide animation instead of needing separate
 * positioning logic for open vs. closed.
 *
 * `openCount` remounts SessionDashboardPanel on every open (fresh `key`),
 * so the numbers reflect whatever's happened in the game since it was
 * last pulled out, without polling while it's closed.
 */
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
        <motion.div
            className="fixed top-0 right-0 z-30 h-full w-[92vw] max-w-md"
            animate={{ x: isOpen ? 0 : '100%' }}
            initial={false}
            transition={{ type: 'spring', stiffness: 300, damping: 32 }}
        >
            <div className="absolute top-1/2 -left-10 -translate-y-1/2">
                <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS} size="sm">
                    <button
                        type="button"
                        onClick={toggleOpen}
                        aria-label={isOpen ? 'Close dashboard' : 'Open dashboard'}
                        aria-expanded={isOpen}
                        className="flex h-32 w-10 cursor-pointer items-center justify-center rounded-l-lg border border-r-0 border-white/15 bg-zinc-900 text-sm font-semibold tracking-wide text-foreground hover:bg-zinc-800"
                    >
                        <span className="[writing-mode:vertical-rl]">Dashboard</span>
                    </button>
                </BorderBeam>
            </div>

            <div className="h-full overflow-y-auto border-l border-white/15 bg-zinc-950/95 p-4 shadow-2xl backdrop-blur-md">
                {hasOpenedOnce && <SessionDashboardPanel key={openCount} sessionId={sessionId} />}
            </div>
        </motion.div>
    )
}

export { DashboardDrawer }
