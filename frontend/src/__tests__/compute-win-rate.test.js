import { describe, expect, it } from 'vitest'

import { computeWinRate } from '@/lib/compute-win-rate'

describe('computeWinRate', () => {
    it('excludes pending (unresolved) hands', () => {
        const result = computeWinRate([{ hero_action: null, winner: null }])
        expect(result.total).toBe(0)
    })

    it('counts a fold correctly, even though winner is "opponent"', () => {
        const result = computeWinRate([{ hero_action: 'fold', winner: 'opponent' }])
        expect(result.fold).toEqual({ count: 1, pct: 1 })
        expect(result.loss.count).toBe(0)
    })

    it('distinguishes a showdown loss from a fold (both have winner="opponent")', () => {
        const result = computeWinRate([{ hero_action: 'call', winner: 'opponent' }])
        expect(result.loss).toEqual({ count: 1, pct: 1 })
        expect(result.fold.count).toBe(0)
    })

    it('counts wins and splits', () => {
        const result = computeWinRate([
            { hero_action: 'call', winner: 'hero' },
            { hero_action: 'raise', winner: 'split' },
        ])
        expect(result.win).toEqual({ count: 1, pct: 0.5 })
        expect(result.split).toEqual({ count: 1, pct: 0.5 })
    })

    it('computes shares over a realistic mixed sample', () => {
        const hands = [
            { hero_action: 'fold', winner: 'opponent' },
            { hero_action: 'call', winner: 'hero' },
            { hero_action: 'call', winner: 'opponent' },
            { hero_action: 'raise', winner: 'split' },
        ]

        const result = computeWinRate(hands)

        expect(result.total).toBe(4)
        expect(result.fold.pct).toBeCloseTo(0.25)
        expect(result.win.pct).toBeCloseTo(0.25)
        expect(result.loss.pct).toBeCloseTo(0.25)
        expect(result.split.pct).toBeCloseTo(0.25)
    })
})
