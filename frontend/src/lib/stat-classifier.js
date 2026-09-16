/**
 * Turns a raw stat value into "is this favorable?" -- 'good' | 'critical'
 * | 'neutral' -- matching StatTile's own existing variant vocabulary
 * (frontend/src/components/dashboard/stat-tile.jsx), so a classified stat
 * can be colored with the exact same tokens a plain StatTile already
 * uses, no separate color system invented for charts specifically.
 *
 * Ranges below are standard, widely-cited poker HUD guidance (not derived
 * from this project's own bot personas) for a "generally healthy" range
 * -- outside it isn't necessarily wrong, just a signal worth noticing,
 * the same way a real HUD's stat coloring works. 'neutral' means "no
 * data yet" (a null value) or a stat this classifier doesn't cover.
 */
const STAT_RANGES = {
    vpip: [0.15, 0.35],
    pfr: [0.1, 0.25],
    aggressionFactor: [1.5, 4.0],
    threeBet: [0.04, 0.12],
    ats: [0.25, 0.5],
    wtsd: [0.2, 0.3],
    wonAtShowdown: [0.5, 1.0],
    wonWhenSawFlop: [0.45, 1.0],
}

/**
 * @param {keyof typeof STAT_RANGES} statKey
 * @param {number | null | undefined} value
 * @returns {'good' | 'critical' | 'neutral'}
 */
const classifyStat = (statKey, value) => {
    if (value == null) {
        return 'neutral'
    }

    const range = STAT_RANGES[statKey]
    if (!range) {
        return 'neutral'
    }

    const [min, max] = range
    return value >= min && value <= max ? 'good' : 'critical'
}

// Matches StatTile's own good/critical/neutral text colors (Tailwind's
// green-600/red-600), as real color VALUES rather than class names --
// chart fills (SVG) need an actual color, not a Tailwind utility class.
// 'neutral' uses the app's own --muted-foreground token so it still
// tracks the light/dark theme, the same pattern BankrollGrowthChart
// already uses for its own non-classified stroke color.
const CLASSIFICATION_COLORS = {
    good: '#16a34a',
    critical: '#dc2626',
    neutral: 'var(--muted-foreground)',
}

export { classifyStat, CLASSIFICATION_COLORS, STAT_RANGES }
