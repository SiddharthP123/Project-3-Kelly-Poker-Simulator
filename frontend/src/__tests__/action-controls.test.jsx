import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ActionControls } from '@/components/poker/action-controls'

const boundsFacingABet = {
    can_fold: true,
    can_check: false,
    can_call: true,
    call_amount: 100,
    can_raise: true,
    min_raise_to: 200,
    max_raise_to: 1000,
}

const boundsFreeToCheck = {
    can_fold: true,
    can_check: true,
    can_call: false,
    call_amount: 0,
    can_raise: true,
    min_raise_to: 4,
    max_raise_to: 1000,
}

describe('ActionControls', () => {
    it('calls onAct("fold") when Fold is clicked', async () => {
        const onAct = vi.fn()
        render(<ActionControls legalActionBounds={boundsFacingABet} onAct={onAct} isSubmitting={false} />)

        await userEvent.click(screen.getByRole('button', { name: /fold/i }))
        expect(onAct).toHaveBeenCalledWith('fold')
    })

    it('shows "Call $X" and calls onAct("call") when facing a real bet', async () => {
        const onAct = vi.fn()
        render(<ActionControls legalActionBounds={boundsFacingABet} onAct={onAct} isSubmitting={false} />)

        const callButton = screen.getByRole('button', { name: /call \$100/i })
        await userEvent.click(callButton)
        expect(onAct).toHaveBeenCalledWith('call')
    })

    it('shows "Check" instead of "Call" when nothing is owed, and still calls onAct("call")', async () => {
        const onAct = vi.fn()
        render(<ActionControls legalActionBounds={boundsFreeToCheck} onAct={onAct} isSubmitting={false} />)

        const checkButton = screen.getByRole('button', { name: /^check$/i })
        await userEvent.click(checkButton)
        expect(onAct).toHaveBeenCalledWith('call')
    })

    it('pre-fills the raise input with the minimum legal raise and submits it', async () => {
        const onAct = vi.fn()
        render(<ActionControls legalActionBounds={boundsFacingABet} onAct={onAct} isSubmitting={false} />)

        expect(screen.getByLabelText(/raise to/i)).toHaveValue(200)
        await userEvent.click(screen.getByRole('button', { name: /^raise$/i }))
        expect(onAct).toHaveBeenCalledWith('raise', 200)
    })

    it('the All-in button fills the raise input with max_raise_to', async () => {
        const onAct = vi.fn()
        render(<ActionControls legalActionBounds={boundsFacingABet} onAct={onAct} isSubmitting={false} />)

        await userEvent.click(screen.getByRole('button', { name: /all-in/i }))
        expect(screen.getByLabelText(/raise to/i)).toHaveValue(1000)
        await userEvent.click(screen.getByRole('button', { name: /^raise$/i }))
        expect(onAct).toHaveBeenCalledWith('raise', 1000)
    })

    it('rejects a raise amount below the minimum legal raise, client-side', async () => {
        const onAct = vi.fn()
        render(<ActionControls legalActionBounds={boundsFacingABet} onAct={onAct} isSubmitting={false} />)

        const raiseInput = screen.getByLabelText(/raise to/i)
        await userEvent.clear(raiseInput)
        await userEvent.type(raiseInput, '150')
        await userEvent.click(screen.getByRole('button', { name: /^raise$/i }))

        expect(onAct).not.toHaveBeenCalled()
        expect(screen.getByText(/must be at least/i)).toBeInTheDocument()
    })

    it('rejects a raise amount exceeding max_raise_to, client-side', async () => {
        const onAct = vi.fn()
        render(<ActionControls legalActionBounds={boundsFacingABet} onAct={onAct} isSubmitting={false} />)

        const raiseInput = screen.getByLabelText(/raise to/i)
        await userEvent.clear(raiseInput)
        await userEvent.type(raiseInput, '9000')
        await userEvent.click(screen.getByRole('button', { name: /^raise$/i }))

        expect(onAct).not.toHaveBeenCalled()
        expect(screen.getByText(/cannot exceed/i)).toBeInTheDocument()
    })

    it('does not render a raise section when can_raise is false', () => {
        render(
            <ActionControls
                legalActionBounds={{ ...boundsFacingABet, can_raise: false }}
                onAct={vi.fn()}
                isSubmitting={false}
            />,
        )

        expect(screen.queryByLabelText(/raise to/i)).not.toBeInTheDocument()
    })

    it('does not render a fold button when can_fold is false', () => {
        render(
            <ActionControls
                legalActionBounds={{ ...boundsFacingABet, can_fold: false }}
                onAct={vi.fn()}
                isSubmitting={false}
            />,
        )

        expect(screen.queryByRole('button', { name: /fold/i })).not.toBeInTheDocument()
    })
})
