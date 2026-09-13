import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PokerTable } from '@/components/poker/poker-table'

const jsonResponse = (body, { status = 200 } = {}) => ({
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () => body,
})

const session = { id: 1, current_bankroll: 1000, num_opponents: 1, status: 'active' }

const dealtHand = {
    id: 42,
    hand_number: 1,
    button_seat: 0,
    street: 'preflop',
    board_cards: null,
    pot_size: 3,
    players: [
        {
            seat_index: 0, is_hero: true, persona: null, stack: 998,
            hole_cards: 'Ah,Ac', folded: false, all_in: false, is_winner: false, net_result: null,
        },
        {
            seat_index: 1, is_hero: false, persona: 'tight-aggressive', stack: 999,
            hole_cards: null, folded: false, all_in: false, is_winner: false, net_result: null,
        },
    ],
    legal_action_bounds: {
        can_fold: true, can_check: false, can_call: true, call_amount: 1,
        can_raise: true, min_raise_to: 4, max_raise_to: 998,
    },
    actions: [],
    winners: null,
    played_at: '2026-08-01T00:00:00Z',
}

const resolvedHand = {
    ...dealtHand,
    street: 'complete',
    board_cards: '2c,3d,4h,5s,6c',
    legal_action_bounds: null,
    winners: [0],
    players: [
        {
            ...dealtHand.players[0], stack: 1099, is_winner: true, net_result: 100,
        },
        {
            ...dealtHand.players[1], hole_cards: 'Kh,Kd', stack: 899, is_winner: false, net_result: -100,
        },
    ],
}

describe('PokerTable', () => {
    beforeEach(() => {
        global.fetch = vi.fn()
    })

    it('shows a Deal Hand button when there is no pending hand (idle state)', async () => {
        global.fetch.mockResolvedValue(jsonResponse({ detail: 'not found' }, { status: 404 }))

        render(<PokerTable sessionId="1" session={session} onSessionUpdate={vi.fn()} />)

        await waitFor(() => expect(screen.getByRole('button', { name: /deal hand/i })).toBeInTheDocument())
    })

    it('shows hero cards and action controls after dealing', async () => {
        global.fetch
            .mockResolvedValueOnce(jsonResponse({ detail: 'not found' }, { status: 404 })) // initial pending check
            .mockResolvedValueOnce(jsonResponse(dealtHand)) // deal

        render(<PokerTable sessionId="1" session={session} onSessionUpdate={vi.fn()} />)

        await waitFor(() => screen.getByRole('button', { name: /deal hand/i }))
        await userEvent.click(screen.getByRole('button', { name: /deal hand/i }))

        await waitFor(() => expect(screen.getByText('You')).toBeInTheDocument())
        expect(screen.getByRole('button', { name: /call \$1/i })).toBeInTheDocument()
        // Opponent's cards are never sent by the API mid-hand -- rendered face-down.
        expect(screen.getByText('Tight-Aggressive')).toBeInTheDocument()
    })

    it('resolves the hand once an action is submitted and calls onSessionUpdate', async () => {
        const onSessionUpdate = vi.fn().mockResolvedValue(undefined)

        global.fetch
            .mockResolvedValueOnce(jsonResponse(dealtHand)) // initial pending check finds a dealt hand
            .mockResolvedValueOnce(jsonResponse(resolvedHand)) // act: call

        render(<PokerTable sessionId="1" session={session} onSessionUpdate={onSessionUpdate} />)

        await waitFor(() => screen.getByRole('button', { name: /call \$1/i }))
        await userEvent.click(screen.getByRole('button', { name: /call \$1/i }))

        await waitFor(() => expect(screen.getByText('You won!')).toBeInTheDocument())
        expect(onSessionUpdate).toHaveBeenCalled()
    })

    it('does not call onSessionUpdate when the street advances but the hand is still pending', async () => {
        const onSessionUpdate = vi.fn()
        const stillPendingAfterCall = { ...dealtHand, street: 'flop', board_cards: '2c,3d,4h' }

        global.fetch
            .mockResolvedValueOnce(jsonResponse(dealtHand))
            .mockResolvedValueOnce(jsonResponse(stillPendingAfterCall))

        render(<PokerTable sessionId="1" session={session} onSessionUpdate={onSessionUpdate} />)

        await waitFor(() => screen.getByRole('button', { name: /call \$1/i }))
        await userEvent.click(screen.getByRole('button', { name: /call \$1/i }))

        await waitFor(() => expect(screen.getByText(/pot: \$3/i)).toBeInTheDocument())
        expect(onSessionUpdate).not.toHaveBeenCalled()
    })
})
