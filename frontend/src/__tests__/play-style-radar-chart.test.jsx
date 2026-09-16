import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { buildPlayStyleData, PlayStyleRadarChart } from '@/components/dashboard/play-style-radar-chart'

const baseStats = {
    vpip_rate: 0.6, pfr_rate: 0.2, aggression_factor: 1.5, win_rate: 0.4, fold_rate: 0.2,
}

describe('buildPlayStyleData', () => {
    it('scales vpip_rate/pfr_rate/win_rate/fold_rate to 0-100 and caps aggression_factor at the display cap', () => {
        const data = buildPlayStyleData(baseStats)

        expect(data).toEqual([
            { axis: 'VPIP', value: 60, classification: 'critical' }, // 0.6 is outside the healthy VPIP range
            { axis: 'PFR', value: 20, classification: 'good' }, // 0.2 is inside the healthy PFR range
            { axis: 'Aggression', value: 50, classification: 'good' }, // 1.5 / cap(3) * 100
            { axis: 'Win rate', value: 40, classification: 'neutral' },
            { axis: 'Fold rate', value: 20, classification: 'neutral' },
        ])
    })

    it('shows 0 for aggression when there is no call data yet (null, not 0 or infinity)', () => {
        const data = buildPlayStyleData({ ...baseStats, aggression_factor: null })

        const aggression = data.find((point) => point.axis === 'Aggression')
        expect(aggression.value).toBe(0)
        expect(aggression.classification).toBe('neutral')
    })

    it('clips an aggression_factor above the display cap to 100, not an out-of-range value', () => {
        const data = buildPlayStyleData({ ...baseStats, aggression_factor: 10 })

        expect(data.find((point) => point.axis === 'Aggression').value).toBe(100)
    })
})

describe('PlayStyleRadarChart', () => {
    it('shows a prompt instead of a chart when no hands have been played yet', () => {
        render(<PlayStyleRadarChart stats={{ total_hands: 0, ...baseStats }} />)

        expect(screen.getByText(/play a few hands to see your play style here/i)).toBeInTheDocument()
    })
})
