import { describe, expect, it } from 'vitest'

import { computeBankrollSeries } from '@/lib/compute-bankroll-series'

describe('computeBankrollSeries', () => {
    it('returns an empty array for no logs', () => {
        expect(computeBankrollSeries([])).toEqual([])
    })

    it('maps bankroll_after/logged_at to index/bankroll/loggedAt, preserving order', () => {
        const logs = [
            { bankroll_after: 1000, logged_at: '2026-01-01T00:00:00Z' },
            { bankroll_after: 900, logged_at: '2026-01-01T00:05:00Z' },
        ]

        expect(computeBankrollSeries(logs)).toEqual([
            { index: 0, bankroll: 1000, loggedAt: '2026-01-01T00:00:00Z' },
            { index: 1, bankroll: 900, loggedAt: '2026-01-01T00:05:00Z' },
        ])
    })
})
