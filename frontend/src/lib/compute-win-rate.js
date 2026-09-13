/**
 * Aggregates resolved hands into win/loss/split/fold counts and shares.
 *
 * Part 12 replaced the old single hero_action/winner fields with a
 * per-seat players[] array and a winners[] list of seat indices (since
 * there can be 1-4 opponents, not just one) -- a hand only counts once
 * it's genuinely resolved (hand.street === 'complete'); anything still
 * in progress is excluded entirely, same as a pending hand always was.
 *
 * @param {Array<{street: string, winners: number[]|null, players: Array<{is_hero: boolean, folded: boolean, seat_index: number}>}>} hands
 * @returns {{
 *   total: number,
 *   win: {count: number, pct: number},
 *   loss: {count: number, pct: number},
 *   split: {count: number, pct: number},
 *   fold: {count: number, pct: number},
 * }}
 */
const computeWinRate = (hands) => {
    const resolvedHands = hands.filter((hand) => hand.street === 'complete')
    const total = resolvedHands.length

    const counts = { win: 0, loss: 0, split: 0, fold: 0 }

    for (const hand of resolvedHands) {
        const hero = hand.players.find((player) => player.is_hero)

        if (hero.folded) {
            counts.fold += 1
        } else if (hand.winners.includes(hero.seat_index)) {
            counts[hand.winners.length > 1 ? 'split' : 'win'] += 1
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
