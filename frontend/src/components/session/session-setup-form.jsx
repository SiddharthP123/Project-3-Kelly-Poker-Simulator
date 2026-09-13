import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

// 1-4 opponents, matching the backend's supported range -- personas are
// randomly assigned per seat server-side (poker.bots.assign_opponent_personas),
// not chosen here.
const OPPONENT_COUNTS = [1, 2, 3, 4]

const SessionSetupForm = ({ onSubmit, isSubmitting, errorMessage }) => {
    const [numOpponents, setNumOpponents] = useState('1')
    const [startingBankroll, setStartingBankroll] = useState('')
    const [kellyMultiplier, setKellyMultiplier] = useState('1')

    const handleSubmit = (event) => {
        event.preventDefault()
        onSubmit({
            numOpponents: Number(numOpponents),
            startingBankroll: startingBankroll ? Number(startingBankroll) : null,
            kellyMultiplier: kellyMultiplier ? Number(kellyMultiplier) : null,
        })
    }

    return (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
                <Label htmlFor="num-opponents">Opponents</Label>
                <Select value={numOpponents} onValueChange={setNumOpponents}>
                    <SelectTrigger id="num-opponents" className="w-full">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        {OPPONENT_COUNTS.map((count) => (
                            <SelectItem key={count} value={String(count)}>
                                {count} opponent{count > 1 ? 's' : ''}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>
            <div className="flex flex-col gap-2">
                <Label htmlFor="starting-bankroll">Starting bankroll (optional)</Label>
                <Input
                    id="starting-bankroll"
                    type="number"
                    min="1"
                    placeholder="Defaults to your account default"
                    value={startingBankroll}
                    onChange={(event) => setStartingBankroll(event.target.value)}
                />
            </div>
            <div className="flex flex-col gap-2">
                <Label htmlFor="kelly-multiplier">Kelly multiplier</Label>
                <Input
                    id="kelly-multiplier"
                    type="number"
                    min="0"
                    step="0.1"
                    value={kellyMultiplier}
                    onChange={(event) => setKellyMultiplier(event.target.value)}
                />
            </div>
            {errorMessage && <p className="text-sm text-destructive">{errorMessage}</p>}
            <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Starting...' : 'Start session'}
            </Button>
        </form>
    )
}

export { SessionSetupForm }
