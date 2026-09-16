import { describe, expect, it } from 'vitest'

import { classifyStat } from '@/lib/stat-classifier'

describe('classifyStat', () => {
    it('returns neutral for a null value regardless of stat key', () => {
        expect(classifyStat('vpip', null)).toBe('neutral')
        expect(classifyStat('vpip', undefined)).toBe('neutral')
    })

    it('returns neutral for a stat key it has no range for', () => {
        expect(classifyStat('winRate', 0.9)).toBe('neutral')
    })

    it('returns good for a value inside the healthy range', () => {
        expect(classifyStat('vpip', 0.25)).toBe('good')
        expect(classifyStat('pfr', 0.15)).toBe('good')
        expect(classifyStat('aggressionFactor', 2.0)).toBe('good')
    })

    it('returns critical for a value outside the healthy range, on either side', () => {
        expect(classifyStat('vpip', 0.05)).toBe('critical') // too tight
        expect(classifyStat('vpip', 0.6)).toBe('critical') // too loose
        expect(classifyStat('aggressionFactor', 0.2)).toBe('critical') // too passive
    })

    it('treats the range boundaries themselves as good (inclusive)', () => {
        expect(classifyStat('vpip', 0.15)).toBe('good')
        expect(classifyStat('vpip', 0.35)).toBe('good')
    })
})
