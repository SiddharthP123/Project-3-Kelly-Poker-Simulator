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
 * (green) via strengthColor. Fills the full width of its container (an
 * `aspect-square` wrapper, not a fixed pixel size) so its left/right edges
 * line up with the surrounding page text instead of sitting narrower and
 * centered -- 13 equal columns/rows over a square box makes every cell
 * square too, without pinning any of them to a fixed size.
 */
const StartingHandMatrix = () => (
    <div className="aspect-square w-full">
        <div className="grid h-full w-full grid-cols-[repeat(13,minmax(0,1fr))] grid-rows-[repeat(13,minmax(0,1fr))] gap-0.5">
            {DISPLAY_RANKS.map((rowRank) =>
                DISPLAY_RANKS.map((colRank) => {
                    const label = cellFor(rowRank, colRank)
                    const score = STARTING_HAND_STRENGTH[label]
                    return (
                        <div
                            key={label}
                            title={label}
                            className="flex items-center justify-center rounded text-[0.55rem] font-semibold text-white sm:text-sm"
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
