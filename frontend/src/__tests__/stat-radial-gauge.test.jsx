import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { StatRadialGauge } from '@/components/dashboard/stat-radial-gauge'

describe('StatRadialGauge', () => {
    it('shows the percentage and label for a real value', () => {
        render(<StatRadialGauge label="VPIP" value={0.256} statKey="vpip" />)

        expect(screen.getByText('25.6%')).toBeInTheDocument()
        expect(screen.getByText('VPIP')).toBeInTheDocument()
    })

    it('shows a dash when there is no data yet', () => {
        render(<StatRadialGauge label="3-bet" value={null} statKey="threeBet" />)

        expect(screen.getByText('—')).toBeInTheDocument()
        expect(screen.getByText('3-bet')).toBeInTheDocument()
    })
})
