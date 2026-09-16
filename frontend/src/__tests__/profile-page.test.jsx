import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/context/auth-context'
import { setStoredToken } from '@/lib/api-client'
import { ProfilePage } from '@/pages/profile-page'

const jsonResponse = (body, { status = 200 } = {}) => ({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () => body,
})

const baseUser = {
    id: 1, email: 'me@example.com', display_name: 'Sid', bio: 'Old bio', avatar_url: null,
    starting_bankroll: 1000, created_at: '2026-01-01T00:00:00Z',
}

const emptyStats = {
    total_sessions: 0, total_hands: 0,
    win_count: 0, loss_count: 0, split_count: 0, fold_count: 0,
    win_rate: 0, loss_rate: 0, split_rate: 0, fold_rate: 0,
    cumulative_bankroll_change: 0, biggest_win: null, biggest_loss: null,
    vpip_rate: 0, aggression_factor: null,
    pfr_rate: 0, three_bet_rate: null, ats_rate: null,
    wtsd_rate: 0, won_at_showdown_rate: null, won_when_saw_flop_rate: null,
    fold_frequency_by_street: { preflop: null, flop: null, turn: null, river: null },
    aggression_frequency_by_street: { preflop: null, flop: null, turn: null, river: null },
    hands_won: 0, sessions_won: 0,
    bankroll_history: [],
}

const renderProfilePage = () =>
    render(
        <MemoryRouter>
            <AuthProvider>
                <ProfilePage />
            </AuthProvider>
        </MemoryRouter>,
    )

describe('ProfilePage', () => {
    beforeEach(() => {
        localStorage.clear()
        setStoredToken('tok123')
    })

    it('loads the current user into the form and shows the stats snapshot', async () => {
        global.fetch = vi.fn((url) => {
            if (url.endsWith('/auth/me')) {
                return Promise.resolve(jsonResponse(baseUser))
            }
            if (url.endsWith('/users/me/stats')) {
                return Promise.resolve(
                    jsonResponse({ ...emptyStats, total_sessions: 3, total_hands: 10, cumulative_bankroll_change: 25 }),
                )
            }
            return Promise.resolve(jsonResponse({}, { status: 404 }))
        })

        renderProfilePage()

        await waitFor(() => expect(screen.getByDisplayValue('Sid')).toBeInTheDocument())
        expect(screen.getByDisplayValue('Old bio')).toBeInTheDocument()
        await waitFor(() => expect(screen.getByText('Sessions played')).toBeInTheDocument())
        expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('saves the profile, shows a confirmation, and refreshes the header display name', async () => {
        global.fetch = vi.fn((url, options = {}) => {
            if (url.endsWith('/auth/me') && options.method === 'PATCH') {
                return Promise.resolve(jsonResponse({ ...baseUser, display_name: 'New Name' }))
            }
            if (url.endsWith('/auth/me')) {
                return Promise.resolve(jsonResponse(baseUser))
            }
            if (url.endsWith('/users/me/stats')) {
                return Promise.resolve(jsonResponse(emptyStats))
            }
            return Promise.resolve(jsonResponse({}, { status: 404 }))
        })

        renderProfilePage()

        await waitFor(() => expect(screen.getByDisplayValue('Sid')).toBeInTheDocument())

        const nameInput = screen.getByLabelText(/display name/i)
        await userEvent.clear(nameInput)
        await userEvent.type(nameInput, 'New Name')
        await userEvent.click(screen.getByRole('button', { name: /save profile/i }))

        await waitFor(() => expect(screen.getByText(/profile saved/i)).toBeInTheDocument())

        const patchCall = global.fetch.mock.calls.find(([, init]) => init?.method === 'PATCH')
        expect(JSON.parse(patchCall[1].body)).toEqual({
            display_name: 'New Name', bio: 'Old bio', avatar_url: '',
        })
    })

    it('shows an initials fallback when there is no avatar URL', async () => {
        global.fetch = vi.fn((url) => {
            if (url.endsWith('/auth/me')) {
                return Promise.resolve(jsonResponse(baseUser))
            }
            if (url.endsWith('/users/me/stats')) {
                return Promise.resolve(jsonResponse(emptyStats))
            }
            return Promise.resolve(jsonResponse({}, { status: 404 }))
        })

        renderProfilePage()

        await waitFor(() => expect(screen.getByText('SI')).toBeInTheDocument())
    })

    it('shows an error message if saving fails', async () => {
        global.fetch = vi.fn((url, options = {}) => {
            if (url.endsWith('/auth/me') && options.method === 'PATCH') {
                return Promise.resolve(jsonResponse({ detail: 'bio: String should have at most 500 characters' }, { status: 422 }))
            }
            if (url.endsWith('/auth/me')) {
                return Promise.resolve(jsonResponse(baseUser))
            }
            if (url.endsWith('/users/me/stats')) {
                return Promise.resolve(jsonResponse(emptyStats))
            }
            return Promise.resolve(jsonResponse({}, { status: 404 }))
        })

        renderProfilePage()

        await waitFor(() => expect(screen.getByDisplayValue('Sid')).toBeInTheDocument())
        await userEvent.click(screen.getByRole('button', { name: /save profile/i }))

        await waitFor(() => expect(screen.getByText(/at most 500 characters/i)).toBeInTheDocument())
    })
})
