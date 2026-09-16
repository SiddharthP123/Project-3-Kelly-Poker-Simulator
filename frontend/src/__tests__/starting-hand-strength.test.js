import { describe, expect, it } from 'vitest'

import { STARTING_HAND_STRENGTH, strengthColor } from '@/lib/starting-hand-strength'

describe('starting-hand-strength', () => {
    it('covers all 169 starting-hand classes', () => {
        expect(Object.keys(STARTING_HAND_STRENGTH)).toHaveLength(169)
    })

    it('scores AA as the uniquely strongest hand', () => {
        const scores = Object.entries(STARTING_HAND_STRENGTH)
        const maxScore = Math.max(...scores.map(([, score]) => score))

        expect(STARTING_HAND_STRENGTH.AA).toBe(maxScore)
        expect(scores.filter(([, score]) => score === maxScore)).toEqual([['AA', maxScore]])
    })

    it('scores 7-2 offsuit at the table minimum -- the canonical worst hand', () => {
        const minScore = Math.min(...Object.values(STARTING_HAND_STRENGTH))

        expect(STARTING_HAND_STRENGTH['72o']).toBe(minScore)
    })

    it('ranks a suited hand above the same hand offsuit', () => {
        expect(STARTING_HAND_STRENGTH.AKs).toBeGreaterThan(STARTING_HAND_STRENGTH.AKo)
    })

    it('colors the strongest hand green-leaning and the weakest red-leaning', () => {
        expect(strengthColor(STARTING_HAND_STRENGTH.AA)).toBe('rgb(22, 163, 74)')
        expect(strengthColor(STARTING_HAND_STRENGTH['72o'])).toBe('rgb(220, 38, 38)')
    })
})
