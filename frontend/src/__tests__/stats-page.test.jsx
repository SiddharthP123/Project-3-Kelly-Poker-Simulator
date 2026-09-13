import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/context/auth-context'
import { StatsPage } from '@/pages/stats-page'

const jsonResponse = (body, { status = 200 } = {}) => ({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () => body,
})

const renderStatsPage = () =>
    render(
        <MemoryRouter>
            <AuthProvider>
                <StatsPage />
            </AuthProvider>
        </MemoryRouter>,
    )

const emptyStats = {
    total_sessions: 0, total_hands: 0,
    win_count: 0, loss_count: 0, split_count: 0, fold_count: 0,
    win_rate: 0, loss_rate: 0, split_rate: 0, fold_rate: 0,
    cumulative_bankroll_change: 0, biggest_win: null, biggest_loss: null,
}

const realStats = {
    total_sessions: 2, total_hands: 5,
    win_count: 2, loss_count: 1, split_count: 1, fold_count: 1,
    win_rate: 0.4, loss_rate: 0.2, split_rate: 0.2, fold_rate: 0.2,
    cumulative_bankroll_change: 150.5, biggest_win: 200, biggest_loss: -75,
}

describe('StatsPage', () => {
    beforeEach(() => {
        localStorage.clear()
        global.fetch = vi.fn().mockResolvedValue(jsonResponse(null, { status: 401 })) // no token -> /auth/me skipped anyway
    })

    it('shows a message when no sessions have been played yet', async () => {
        global.fetch = vi.fn().mockResolvedValue(jsonResponse(emptyStats))

        renderStatsPage()

        await waitFor(() => expect(screen.getByText(/no sessions played yet/i)).toBeInTheDocument())
    })

    it('shows stat tiles and win rate once real stats load', async () => {
        global.fetch = vi.fn().mockResolvedValue(jsonResponse(realStats))

        renderStatsPage()

        await waitFor(() => expect(screen.getByText('Sessions played')).toBeInTheDocument())
        expect(screen.getByText('2')).toBeInTheDocument() // sessions played
        expect(screen.getByText('5')).toBeInTheDocument() // hands played
        expect(screen.getByText('+$150.50')).toBeInTheDocument()
        expect(screen.getByText('$200.00')).toBeInTheDocument() // biggest win
        expect(screen.getByText('-$75.00')).toBeInTheDocument() // biggest loss
    })

    it('shows an error message if the stats request fails', async () => {
        global.fetch = vi.fn().mockResolvedValue(jsonResponse({ detail: 'server exploded' }, { status: 500 }))

        renderStatsPage()

        await waitFor(() => expect(screen.getByText('server exploded')).toBeInTheDocument())
    })
})
