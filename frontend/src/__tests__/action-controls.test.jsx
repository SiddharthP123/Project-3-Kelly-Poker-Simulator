import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ActionControls } from '@/components/poker/action-controls'

describe('ActionControls', () => {
    it('calls onAct("fold") when Fold is clicked', async () => {
        const onAct = vi.fn()
        render(
            <ActionControls
                betToCall={100}
                bankroll={1000}
                suggestedRaiseAmount={200}
                onAct={onAct}
                isSubmitting={false}
            />,
        )

        await userEvent.click(screen.getByRole('button', { name: /fold/i }))
        expect(onAct).toHaveBeenCalledWith('fold')
    })

    it('calls onAct("call") when Call is clicked', async () => {
        const onAct = vi.fn()
        render(
            <ActionControls
                betToCall={100}
                bankroll={1000}
                suggestedRaiseAmount={200}
                onAct={onAct}
                isSubmitting={false}
            />,
        )

        await userEvent.click(screen.getByRole('button', { name: /call/i }))
        expect(onAct).toHaveBeenCalledWith('call')
    })

    it('pre-fills the raise input with the suggested amount and submits it', async () => {
        const onAct = vi.fn()
        render(
            <ActionControls
                betToCall={100}
                bankroll={1000}
                suggestedRaiseAmount={250}
                onAct={onAct}
                isSubmitting={false}
            />,
        )

        expect(screen.getByLabelText(/raise to/i)).toHaveValue(250)
        await userEvent.click(screen.getByRole('button', { name: /^raise$/i }))
        expect(onAct).toHaveBeenCalledWith('raise', 250)
    })

    it('floors the pre-filled raise suggestion at the minimum valid raise when Kelly recommends less than a call', () => {
        // A Kelly-recommended stake below betToCall means "call, don't
        // raise" -- pre-filling the raise field with that number would be
        // a suggestion guaranteed to fail validation.
        render(
            <ActionControls
                betToCall={100}
                bankroll={1000}
                suggestedRaiseAmount={13.5}
                onAct={vi.fn()}
                isSubmitting={false}
            />,
        )

        expect(screen.getByLabelText(/raise to/i)).toHaveValue(101)
    })

    it('rejects a raise amount at or below the bet to call, client-side', async () => {
        const onAct = vi.fn()
        render(
            <ActionControls
                betToCall={100}
                bankroll={1000}
                suggestedRaiseAmount={200}
                onAct={onAct}
                isSubmitting={false}
            />,
        )

        const raiseInput = screen.getByLabelText(/raise to/i)
        await userEvent.clear(raiseInput)
        await userEvent.type(raiseInput, '100')
        await userEvent.click(screen.getByRole('button', { name: /^raise$/i }))

        expect(onAct).not.toHaveBeenCalled()
        expect(screen.getByText(/must be more than/i)).toBeInTheDocument()
    })

    it('rejects a raise amount exceeding the bankroll, client-side', async () => {
        const onAct = vi.fn()
        render(
            <ActionControls
                betToCall={100}
                bankroll={500}
                suggestedRaiseAmount={200}
                onAct={onAct}
                isSubmitting={false}
            />,
        )

        const raiseInput = screen.getByLabelText(/raise to/i)
        await userEvent.clear(raiseInput)
        await userEvent.type(raiseInput, '9000')
        await userEvent.click(screen.getByRole('button', { name: /^raise$/i }))

        expect(onAct).not.toHaveBeenCalled()
        expect(screen.getByText(/cannot exceed your bankroll/i)).toBeInTheDocument()
    })
})
