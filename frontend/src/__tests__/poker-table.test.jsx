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

const session = { id: 1, current_bankroll: 1000, bot_persona: 'random', status: 'active' }

const dealtHand = {
    id: 42,
    hero_hole_cards: 'Ah,Ac',
    board_cards: null,
    opponent_hole_cards: null,
    pot_size: 100,
    bet_to_call: 100,
    hero_action: null,
    equity_at_decision: 0.85,
    kelly_recommended_stake: 400,
    winner: null,
    hero_bankroll_delta: null,
}

const resolvedHand = {
    ...dealtHand,
    board_cards: '2c,3d,4h,5s,6c',
    opponent_hole_cards: 'Kh,Kd',
    hero_action: 'call',
    winner: 'hero',
    hero_bankroll_delta: 100,
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

    it('shows hole cards and Kelly sizing after dealing', async () => {
        global.fetch
            .mockResolvedValueOnce(jsonResponse({ detail: 'not found' }, { status: 404 })) // initial pending check
            .mockResolvedValueOnce(jsonResponse(dealtHand)) // deal

        render(<PokerTable sessionId="1" session={session} onSessionUpdate={vi.fn()} />)

        await waitFor(() => screen.getByRole('button', { name: /deal hand/i }))
        await userEvent.click(screen.getByRole('button', { name: /deal hand/i }))

        await waitFor(() => expect(screen.getByText('Your hand')).toBeInTheDocument())
        expect(screen.getByText(/85\.0%/)).toBeInTheDocument() // equity
    })

    it('resolves the hand once an action is submitted and calls onSessionUpdate', async () => {
        const onSessionUpdate = vi.fn().mockResolvedValue(undefined)

        global.fetch
            .mockResolvedValueOnce(jsonResponse(dealtHand)) // initial pending check finds a dealt hand
            .mockResolvedValueOnce(jsonResponse(resolvedHand)) // act: call

        render(<PokerTable sessionId="1" session={session} onSessionUpdate={onSessionUpdate} />)

        await waitFor(() => expect(screen.getByText('Your hand')).toBeInTheDocument())
        await userEvent.click(screen.getByRole('button', { name: /call/i }))

        await waitFor(() => expect(screen.getByText('You won!')).toBeInTheDocument())
        expect(onSessionUpdate).toHaveBeenCalled()
    })
})
