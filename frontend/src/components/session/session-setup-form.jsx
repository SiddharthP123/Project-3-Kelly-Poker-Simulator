import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const PERSONAS = [
    { value: 'tight-aggressive', label: 'Tight-Aggressive' },
    { value: 'loose-passive', label: 'Loose-Passive' },
    { value: 'random', label: 'Random' },
    { value: 'kelly-optimal', label: 'Kelly-Optimal' },
]

const SessionSetupForm = ({ onSubmit, isSubmitting, errorMessage }) => {
    const [botPersona, setBotPersona] = useState('tight-aggressive')
    const [startingBankroll, setStartingBankroll] = useState('')
    const [kellyMultiplier, setKellyMultiplier] = useState('1')

    const handleSubmit = (event) => {
        event.preventDefault()
        onSubmit({
            botPersona,
            startingBankroll: startingBankroll ? Number(startingBankroll) : null,
            kellyMultiplier: kellyMultiplier ? Number(kellyMultiplier) : null,
        })
    }

    return (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
                <Label htmlFor="bot-persona">Opponent</Label>
                <Select value={botPersona} onValueChange={setBotPersona}>
                    <SelectTrigger id="bot-persona" className="w-full">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        {PERSONAS.map((persona) => (
                            <SelectItem key={persona.value} value={persona.value}>
                                {persona.label}
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
