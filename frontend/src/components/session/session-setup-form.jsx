import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

// 1-4 opponents, matching the backend's supported range -- personas are
// randomly assigned per seat server-side (poker.bots.assign_opponent_personas),
// not chosen here.
const OPPONENT_COUNTS = [1, 2, 3, 4]

// The backend itself places no upper bound on either field (starting_bankroll
// is just `gt=0`, kelly_multiplier just `ge=0` -- see backend/schemas/game_session.py)
// -- these are purely a client-side sanity guard against fat-fingered input,
// not a cap on how big a bankroll can grow during play (a session's
// current_bankroll is free to compound past this once play starts).
const MAX_STARTING_BANKROLL = 1_000_000
// 3x the raw Kelly fraction is already deep into "growth rate falls as you
// bet past the Kelly-optimal point" territory (see the Kelly Criterion
// page's own growth diagram) -- past that, larger multipliers stop being a
// meaningful strategy choice and start being just a way to lose faster.
const MAX_KELLY_MULTIPLIER = 3

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
                <Label htmlFor="num-opponents">Opponents:</Label>
                <Select value={numOpponents} onValueChange={setNumOpponents}>
                    <SelectTrigger id="num-opponents" className="w-full">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        {OPPONENT_COUNTS.map((count) => (
                            <SelectItem key={count} value={String(count)}>
                                {count} Opponent{count > 1 ? 's' : ''}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>
            <div className="flex flex-col gap-2">
                <Label htmlFor="starting-bankroll">Starting Bankroll (Optional):</Label>
                <Input
                    id="starting-bankroll"
                    type="number"
                    min="1"
                    max={MAX_STARTING_BANKROLL}
                    placeholder="Set to your account default:"
                    value={startingBankroll}
                    onChange={(event) => setStartingBankroll(event.target.value)}
                />
            </div>
            <div className="flex flex-col gap-2">
                <Label htmlFor="kelly-multiplier">Kelly Multiplier:</Label>
                <Input
                    id="kelly-multiplier"
                    type="number"
                    min="0"
                    max={MAX_KELLY_MULTIPLIER}
                    step="0.1"
                    value={kellyMultiplier}
                    onChange={(event) => setKellyMultiplier(event.target.value)}
                />
            </div>
            {errorMessage && <p className="text-sm text-destructive">{errorMessage}</p>}
            <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Starting...' : 'Start Session'}
            </Button>
        </form>
    )
}

export { SessionSetupForm }
