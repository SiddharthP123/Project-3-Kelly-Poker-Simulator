import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { formatCurrency } from '@/lib/format'

const ActionControls = ({ betToCall, bankroll, suggestedRaiseAmount, onAct, isSubmitting }) => {
    // The Kelly-recommended stake can be at or below betToCall (that's
    // exactly the "call, don't raise" zone) -- pre-filling the raise
    // input with an amount that's guaranteed to fail validation would be
    // a confusing default, so the suggestion is floored at the minimum
    // valid raise instead.
    const [raiseAmount, setRaiseAmount] = useState(() =>
        String(Math.max(Math.round(suggestedRaiseAmount), betToCall + 1)),
    )
    const [validationError, setValidationError] = useState('')

    const handleRaise = () => {
        const amount = Number(raiseAmount)

        if (!amount || amount <= betToCall) {
            setValidationError(`Raise must be more than ${formatCurrency(betToCall)}`)
            return
        }
        if (amount > bankroll) {
            setValidationError('Raise cannot exceed your bankroll')
            return
        }

        setValidationError('')
        onAct('raise', amount)
    }

    return (
        <div className="flex flex-col gap-3">
            <div className="flex gap-2">
                <Button variant="destructive" disabled={isSubmitting} onClick={() => onAct('fold')}>
                    Fold
                </Button>
                <Button variant="secondary" disabled={isSubmitting} onClick={() => onAct('call')}>
                    Call {formatCurrency(betToCall)}
                </Button>
            </div>
            <div className="flex items-end gap-2">
                <div className="flex flex-1 flex-col gap-2">
                    <Label htmlFor="raise-amount">Raise to</Label>
                    <Input
                        id="raise-amount"
                        type="number"
                        min={betToCall + 1}
                        max={bankroll}
                        value={raiseAmount}
                        onChange={(event) => setRaiseAmount(event.target.value)}
                    />
                </div>
                <Button disabled={isSubmitting} onClick={handleRaise}>
                    Raise
                </Button>
            </div>
            {validationError && <p className="text-sm text-destructive">{validationError}</p>}
        </div>
    )
}

export { ActionControls }
