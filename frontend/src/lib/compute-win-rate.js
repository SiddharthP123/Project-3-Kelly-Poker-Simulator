/**
 * Aggregates resolved hands into win/loss/split/fold counts and shares.
 *
 * Note: `winner === 'opponent'` covers two different situations -- hero
 * folded (hero_action === 'fold'), or hero called/raised and lost at
 * showdown -- so `hero_action` has to be checked first to tell them apart.
 * Pending (unresolved) hands are excluded entirely.
 *
 * @param {Array<{hero_action: string|null, winner: string|null}>} hands
 * @returns {{
 *   total: number,
 *   win: {count: number, pct: number},
 *   loss: {count: number, pct: number},
 *   split: {count: number, pct: number},
 *   fold: {count: number, pct: number},
 * }}
 */
const computeWinRate = (hands) => {
    const resolvedHands = hands.filter((hand) => hand.hero_action !== null)
    const total = resolvedHands.length

    const counts = { win: 0, loss: 0, split: 0, fold: 0 }

    for (const hand of resolvedHands) {
        if (hand.hero_action === 'fold') {
            counts.fold += 1
        } else if (hand.winner === 'hero') {
            counts.win += 1
        } else if (hand.winner === 'split') {
            counts.split += 1
        } else {
            counts.loss += 1
        }
    }

    const toShare = (count) => ({ count, pct: total > 0 ? count / total : 0 })

    return {
        total,
        win: toShare(counts.win),
        loss: toShare(counts.loss),
        split: toShare(counts.split),
        fold: toShare(counts.fold),
    }
}

export { computeWinRate }
