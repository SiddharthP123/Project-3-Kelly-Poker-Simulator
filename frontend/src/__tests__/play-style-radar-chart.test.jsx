import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { buildPlayStyleData, PlayStyleRadarChart } from '@/components/dashboard/play-style-radar-chart'

describe('buildPlayStyleData', () => {
    it('scales vpip_rate/win_rate/fold_rate to 0-100 and caps aggression_factor at the display cap', () => {
        const data = buildPlayStyleData({ vpip_rate: 0.6, aggression_factor: 1.5, win_rate: 0.4, fold_rate: 0.2 })

        expect(data).toEqual([
            { axis: 'VPIP', value: 60 },
            { axis: 'Aggression', value: 50 }, // 1.5 / cap(3) * 100
            { axis: 'Win rate', value: 40 },
            { axis: 'Fold rate', value: 20 },
        ])
    })

    it('shows 0 for aggression when there is no call data yet (null, not 0 or infinity)', () => {
        const data = buildPlayStyleData({ vpip_rate: 0, aggression_factor: null, win_rate: 0, fold_rate: 0 })

        expect(data.find((point) => point.axis === 'Aggression').value).toBe(0)
    })

    it('clips an aggression_factor above the display cap to 100, not an out-of-range value', () => {
        const data = buildPlayStyleData({ vpip_rate: 0, aggression_factor: 10, win_rate: 0, fold_rate: 0 })

        expect(data.find((point) => point.axis === 'Aggression').value).toBe(100)
    })
})

describe('PlayStyleRadarChart', () => {
    it('shows a prompt instead of a chart when no hands have been played yet', () => {
        render(<PlayStyleRadarChart stats={{ total_hands: 0, vpip_rate: 0, aggression_factor: null, win_rate: 0, fold_rate: 0 }} />)

        expect(screen.getByText(/play a few hands to see your play style here/i)).toBeInTheDocument()
    })
})
