import { StatTile } from '@/components/dashboard/stat-tile'
import { formatPercent } from '@/lib/format'

// hero-win/loss/split/fold are status-meaning outcomes (2 good/bad, 2
// neutral), not arbitrary categories -- see stat-tile.jsx's variant tokens.
const SEGMENTS = [
    { key: 'win', label: 'Win', barClass: 'bg-green-600' },
    { key: 'loss', label: 'Loss', barClass: 'bg-red-600' },
    { key: 'split', label: 'Split', barClass: 'bg-muted-foreground' },
    { key: 'fold', label: 'Fold', barClass: 'bg-amber-500' },
]

const WinRateSummary = ({ winRate }) => (
    <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile label="Win %" value={formatPercent(winRate.win.pct)} variant="good" />
            <StatTile label="Loss %" value={formatPercent(winRate.loss.pct)} variant="critical" />
            <StatTile label="Split %" value={formatPercent(winRate.split.pct)} variant="neutral" />
            <StatTile label="Fold %" value={formatPercent(winRate.fold.pct)} variant="warning" />
        </div>

        {winRate.total > 0 && (
            <div className="flex h-6 w-full overflow-hidden rounded-full">
                {SEGMENTS.map(({ key, label, barClass }) => {
                    const pct = winRate[key].pct
                    if (pct === 0) {
                        return null
                    }

                    return (
                        <div
                            key={key}
                            className={`flex items-center justify-center text-[10px] font-medium text-white ${barClass}`}
                            style={{ width: `${pct * 100}%` }}
                            title={`${label}: ${formatPercent(pct)}`}
                        >
                            {pct >= 0.08 && formatPercent(pct, 0)}
                        </div>
                    )
                })}
            </div>
        )}
    </div>
)

export { WinRateSummary }
