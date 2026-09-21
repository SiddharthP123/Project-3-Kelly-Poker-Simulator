import { motion } from 'framer-motion'

import { StatCard } from '@/components/dashboard/stat-card'
import { StatTile } from '@/components/dashboard/stat-tile'
import { formatPercent } from '@/lib/format'
import { STAT_DESCRIPTIONS } from '@/lib/stat-descriptions'

// hero-win/loss/split/fold are status-meaning outcomes (2 good/bad, 2
// neutral), not arbitrary categories -- see stat-tile.jsx's variant tokens.
const SEGMENTS = [
    { key: 'win', label: 'Win', barClass: 'bg-green-600' },
    { key: 'loss', label: 'Loss', barClass: 'bg-red-600' },
    { key: 'split', label: 'Split', barClass: 'bg-muted-foreground' },
    { key: 'fold', label: 'Fold', barClass: 'bg-amber-500' },
]

/**
 * `translucent`, when true, renders the four tiles as StatCard (the
 * profile/stats page's translucent BorderBeam look) instead of StatTile's
 * shared solid Card -- opt-in so Dashboard's own usage keeps its existing
 * look untouched. Both components share the same label/value/numericValue/
 * formatValue/variant/tooltip prop shape, so they're a drop-in swap.
 */
const WinRateSummary = ({ winRate, translucent = false }) => {
    const Tile = translucent ? StatCard : StatTile

    return (
        <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Tile
                    label="Win %:"
                    numericValue={winRate.win.pct}
                    formatValue={(n) => formatPercent(n)}
                    variant="good"
                    tooltip={STAT_DESCRIPTIONS['Win %:']}
                />
                <Tile
                    label="Loss %:"
                    numericValue={winRate.loss.pct}
                    formatValue={(n) => formatPercent(n)}
                    variant="critical"
                    tooltip={STAT_DESCRIPTIONS['Loss %:']}
                />
                <Tile
                    label="Split %:"
                    numericValue={winRate.split.pct}
                    formatValue={(n) => formatPercent(n)}
                    variant="neutral"
                    tooltip={STAT_DESCRIPTIONS['Split %:']}
                />
                <Tile
                    label="Fold %:"
                    numericValue={winRate.fold.pct}
                    formatValue={(n) => formatPercent(n)}
                    variant="warning"
                    tooltip={STAT_DESCRIPTIONS['Fold %:']}
                />
            </div>

            {winRate.total > 0 && (
                <div className="flex h-6 w-full overflow-hidden rounded-full">
                    {SEGMENTS.map(({ key, label, barClass }, index) => {
                        const pct = winRate[key].pct
                        if (pct === 0) {
                            return null
                        }

                        return (
                            <motion.div
                                key={key}
                                className={`flex items-center justify-center text-[10px] font-medium text-white ${barClass}`}
                                initial={{ width: 0 }}
                                animate={{ width: `${pct * 100}%` }}
                                transition={{ duration: 0.8, delay: 0.2 + index * 0.1, ease: 'easeOut' }}
                                title={`${label}: ${formatPercent(pct)}`}
                            >
                                {pct >= 0.08 && formatPercent(pct, 0)}
                            </motion.div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}

export { WinRateSummary }
