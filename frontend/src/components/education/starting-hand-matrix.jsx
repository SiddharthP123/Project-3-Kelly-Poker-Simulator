import { RANKS, STARTING_HAND_STRENGTH, strengthColor } from '@/lib/starting-hand-strength'

// Standard chart convention: strongest to weakest, top-left to
// bottom-right, so pairs land on the diagonal.
const DISPLAY_RANKS = [...RANKS].reverse()

/**
 * Resolves one grid cell's hand key/label -- pairs on the diagonal, suited
 * combos above it (row rank stronger than column rank), offsuit combos
 * below it (row rank weaker), matching the classic 13x13 starting-hand
 * chart layout and STARTING_HAND_STRENGTH's own 'AKs'/'AKo' key format.
 */
const cellFor = (rowRank, colRank) => {
    if (rowRank === colRank) {
        return `${rowRank}${rowRank}`
    }

    const rowIsStronger = DISPLAY_RANKS.indexOf(rowRank) < DISPLAY_RANKS.indexOf(colRank)
    const high = rowIsStronger ? rowRank : colRank
    const low = rowIsStronger ? colRank : rowRank
    const suffix = rowIsStronger ? 's' : 'o'
    return `${high}${low}${suffix}`
}

/**
 * The classic 13x13 starting-hand grid, color-coded worst (red) to best
 * (green) via strengthColor -- an `overflow-x-auto` wrapper since 13
 * columns of labeled cells don't fit a mobile-width viewport.
 */
const StartingHandMatrix = () => (
    <div className="overflow-x-auto">
        <div className="grid w-max grid-cols-[repeat(13,minmax(0,1fr))] gap-0.5">
            {DISPLAY_RANKS.map((rowRank) =>
                DISPLAY_RANKS.map((colRank) => {
                    const label = cellFor(rowRank, colRank)
                    const score = STARTING_HAND_STRENGTH[label]
                    return (
                        <div
                            key={label}
                            title={label}
                            className="flex h-9 w-9 items-center justify-center rounded text-[0.65rem] font-semibold text-white sm:h-10 sm:w-10 sm:text-xs"
                            style={{ backgroundColor: strengthColor(score) }}
                        >
                            {label}
                        </div>
                    )
                }),
            )}
        </div>
    </div>
)

export { StartingHandMatrix }
