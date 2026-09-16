import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { StatTile } from '@/components/dashboard/stat-tile'

describe('StatTile', () => {
    it('shows the label and value', () => {
        render(<StatTile label="Sessions played" value={5} />)

        expect(screen.getByText('Sessions played')).toBeInTheDocument()
        expect(screen.getByText('5')).toBeInTheDocument()
    })

    it('renders a tooltip trigger when a tooltip is provided', () => {
        render(<StatTile label="VPIP" value="25.6%" tooltip="Voluntarily Put money In Pot." />)

        expect(screen.getByLabelText('What is VPIP?')).toBeInTheDocument()
    })

    it('renders no tooltip trigger when none is provided', () => {
        render(<StatTile label="Sessions played" value={5} />)

        expect(screen.queryByLabelText('What is Sessions played?')).not.toBeInTheDocument()
    })
})
