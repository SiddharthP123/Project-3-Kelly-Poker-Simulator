import { describe, expect, it } from 'vitest'

import { computeWinRate } from '@/lib/compute-win-rate'

const hero = (overrides) => ({ seat_index: 0, is_hero: true, folded: false, ...overrides })
const opponent = (seatIndex = 1) => ({ seat_index: seatIndex, is_hero: false, folded: false })

describe('computeWinRate', () => {
    it('excludes pending (unresolved) hands', () => {
        const result = computeWinRate([{ street: 'preflop', winners: null, players: [hero(), opponent()] }])
        expect(result.total).toBe(0)
    })

    it('counts a fold correctly, even though hero is not among the winners', () => {
        const result = computeWinRate([
            { street: 'complete', winners: [1], players: [hero({ folded: true }), opponent()] },
        ])
        expect(result.fold).toEqual({ count: 1, pct: 1 })
        expect(result.loss.count).toBe(0)
    })

    it('distinguishes a showdown loss from a fold (hero not folded, not a winner)', () => {
        const result = computeWinRate([{ street: 'complete', winners: [1], players: [hero(), opponent()] }])
        expect(result.loss).toEqual({ count: 1, pct: 1 })
        expect(result.fold.count).toBe(0)
    })

    it('counts wins and splits', () => {
        const result = computeWinRate([
            { street: 'complete', winners: [0], players: [hero(), opponent()] },
            { street: 'complete', winners: [0, 1], players: [hero(), opponent()] },
        ])
        expect(result.win).toEqual({ count: 1, pct: 0.5 })
        expect(result.split).toEqual({ count: 1, pct: 0.5 })
    })

    it('a split pot with more than one opponent still counts as a split even with 3+ seats', () => {
        const result = computeWinRate([
            {
                street: 'complete',
                winners: [0, 2],
                players: [hero(), opponent(1), opponent(2), opponent(3)],
            },
        ])
        expect(result.split).toEqual({ count: 1, pct: 1 })
    })

    it('computes shares over a realistic mixed sample', () => {
        const hands = [
            { street: 'complete', winners: [1], players: [hero({ folded: true }), opponent()] },
            { street: 'complete', winners: [0], players: [hero(), opponent()] },
            { street: 'complete', winners: [1], players: [hero(), opponent()] },
            { street: 'complete', winners: [0, 1], players: [hero(), opponent()] },
        ]

        const result = computeWinRate(hands)

        expect(result.total).toBe(4)
        expect(result.fold.pct).toBeCloseTo(0.25)
        expect(result.win.pct).toBeCloseTo(0.25)
        expect(result.loss.pct).toBeCloseTo(0.25)
        expect(result.split.pct).toBeCloseTo(0.25)
    })
})
