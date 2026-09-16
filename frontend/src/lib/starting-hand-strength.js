// Ascending rank order -- index doubles as each rank's position for gap
// math below.
const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

const RANK_VALUE = {
    A: 10, K: 8, Q: 7, J: 6, T: 5,
    9: 4.5, 8: 4, 7: 3.5, 6: 3, 5: 2.5, 4: 2, 3: 1.5, 2: 1,
}

/**
 * The standard "Chen Formula" (Bill Chen) -- a well-known, widely-cited
 * deterministic scoring heuristic for a 2-card Hold'em starting hand, not
 * an invented ranking or a runtime equity simulation. Higher score =
 * stronger hand. Famously scores 7-2 offsuit among the very worst hands in
 * the whole 169-hand table, matching its own folklore reputation as *the*
 * canonical "worst hand in Hold'em."
 *
 * Steps: score the high card alone (pairs double it, floored at 5); add 2
 * for suited; subtract a gap penalty (the "distance" between the two
 * ranks); add back 1 for a 0/1-gap hand where both cards are below a
 * Queen (well-connected low/mid cards make straights more easily).
 */
const chenScore = (highRank, lowRank, suited) => {
    if (highRank === lowRank) {
        return Math.max(RANK_VALUE[highRank] * 2, 5)
    }

    const highIndex = RANKS.indexOf(highRank)
    const lowIndex = RANKS.indexOf(lowRank)
    const gap = highIndex - lowIndex - 1

    let score = RANK_VALUE[highRank]
    if (suited) {
        score += 2
    }
    if (gap === 1) score -= 1
    else if (gap === 2) score -= 2
    else if (gap === 3) score -= 4
    else if (gap >= 4) score -= 5

    if (gap <= 1 && highIndex < RANKS.indexOf('Q')) {
        score += 1
    }

    return Math.ceil(score)
}

/**
 * All 169 starting-hand classes, keyed the standard way ('AA', 'AKs',
 * 'AKo', ...) -- the higher rank always comes first in the key.
 */
const STARTING_HAND_STRENGTH = {}

RANKS.forEach((rank) => {
    STARTING_HAND_STRENGTH[`${rank}${rank}`] = chenScore(rank, rank, false)
})

for (let hi = 0; hi < RANKS.length; hi += 1) {
    for (let lo = 0; lo < hi; lo += 1) {
        const high = RANKS[hi]
        const low = RANKS[lo]
        STARTING_HAND_STRENGTH[`${high}${low}s`] = chenScore(high, low, true)
        STARTING_HAND_STRENGTH[`${high}${low}o`] = chenScore(high, low, false)
    }
}

const SCORES = Object.values(STARTING_HAND_STRENGTH)
const MIN_SCORE = Math.min(...SCORES)
const MAX_SCORE = Math.max(...SCORES)

const RED = [220, 38, 38] // matches stat-classifier.js's CLASSIFICATION_COLORS.critical
const AMBER = [245, 158, 11]
const GREEN = [22, 163, 74] // matches stat-classifier.js's CLASSIFICATION_COLORS.good

const lerpChannel = (start, end, t) => Math.round(start + (end - start) * t)

/**
 * Continuous red -> amber -> green scale across the full strength range --
 * unlike stat-classifier.js's threshold-based good/critical/neutral split,
 * this chart is inherently a full ranking (every hand has a relative
 * strength), so it gets its own interpolated scale rather than reusing
 * classifyStat's discrete buckets.
 */
const strengthColor = (score) => {
    const t = MAX_SCORE === MIN_SCORE ? 1 : (score - MIN_SCORE) / (MAX_SCORE - MIN_SCORE)
    const [start, end, localT] = t < 0.5 ? [RED, AMBER, t / 0.5] : [AMBER, GREEN, (t - 0.5) / 0.5]
    const [r, g, b] = [0, 1, 2].map((channel) => lerpChannel(start[channel], end[channel], localT))
    return `rgb(${r}, ${g}, ${b})`
}

export { RANKS, STARTING_HAND_STRENGTH, strengthColor }
