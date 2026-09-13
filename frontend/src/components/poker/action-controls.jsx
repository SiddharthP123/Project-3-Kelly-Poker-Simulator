import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { formatCurrency } from '@/lib/format'

/**
 * legalActionBounds: the backend's own ActionBounds for hero's current
 * decision (can_fold, can_check, can_call, call_amount, can_raise,
 * min_raise_to, max_raise_to) -- every number here already reflects the
 * real engine state (current bet, hero's actual stack), so this
 * component only needs to render exactly what it's given, not
 * recompute any of it.
 */
const ActionControls = ({ legalActionBounds, onAct, isSubmitting }) => {
    const { can_fold, can_check, can_call, call_amount, can_raise, min_raise_to, max_raise_to } =
        legalActionBounds

    const [raiseTo, setRaiseTo] = useState(() => String(Math.ceil(min_raise_to)))
    const [validationError, setValidationError] = useState('')

    const handleCheckOrCall = () => onAct('call')

    const handleRaise = () => {
        const amount = Number(raiseTo)

        if (!amount || amount < min_raise_to) {
            setValidationError(`Raise must be at least ${formatCurrency(min_raise_to)}`)
            return
        }
        if (amount > max_raise_to) {
            setValidationError(`Raise cannot exceed ${formatCurrency(max_raise_to)} (your stack)`)
            return
        }

        setValidationError('')
        onAct('raise', amount)
    }

    return (
        <div className="flex w-full max-w-md flex-col gap-3 rounded-lg border border-white/15 bg-black/60 p-4">
            <div className="flex gap-2">
                {can_fold && (
                    <Button variant="destructive" disabled={isSubmitting} onClick={() => onAct('fold')}>
                        Fold
                    </Button>
                )}
                {(can_check || can_call) && (
                    <Button variant="secondary" disabled={isSubmitting} onClick={handleCheckOrCall}>
                        {can_check ? 'Check' : `Call ${formatCurrency(call_amount)}`}
                    </Button>
                )}
            </div>

            {can_raise && (
                <div className="flex items-end gap-2">
                    <div className="flex flex-1 flex-col gap-2">
                        <Label htmlFor="raise-amount" className="text-white/70">
                            Raise to
                        </Label>
                        <Input
                            id="raise-amount"
                            type="number"
                            min={min_raise_to}
                            max={max_raise_to}
                            value={raiseTo}
                            onChange={(event) => setRaiseTo(event.target.value)}
                            className="text-white placeholder:text-white/40"
                        />
                    </div>
                    <Button
                        variant="outline"
                        disabled={isSubmitting}
                        onClick={() => setRaiseTo(String(max_raise_to))}
                    >
                        All-in
                    </Button>
                    <Button disabled={isSubmitting} onClick={handleRaise}>
                        Raise
                    </Button>
                </div>
            )}

            {validationError && <p className="text-sm text-red-500">{validationError}</p>}
        </div>
    )
}

export { ActionControls }
