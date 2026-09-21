import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatCurrency } from '@/lib/format'

/**
 * Derives a per-hand result label + badge variant from the new
 * players[]/winners[] shape (Part 12) -- there's no single fixed
 * hero_action/winner pair anymore, since a hand can have 1-4 opponents
 * and any number of winners (a split, or an uncontested side pot).
 */
const describeResult = (hand) => {
    const hero = hand.players.find((player) => player.is_hero)

    if (hero.folded) {
        return { label: 'folded', variant: 'outline' }
    }
    if (!hand.winners.includes(hero.seat_index)) {
        return { label: 'lost', variant: 'destructive' }
    }
    return hand.winners.length > 1 ? { label: 'split', variant: 'secondary' } : { label: 'won', variant: 'default' }
}

const HandHistoryTable = ({ hands }) => {
    const resolvedHands = hands.filter((hand) => hand.street === 'complete')

    if (resolvedHands.length === 0) {
        return <p className="text-sm text-muted-foreground">No hands played yet.</p>
    }

    return (
        <Table>
            <TableHeader>
                <TableRow>
                    <TableHead>#</TableHead>
                    <TableHead>Your Hand:</TableHead>
                    <TableHead>Opponent's Hand:</TableHead>
                    <TableHead className="text-center">Result:</TableHead>
                    <TableHead className="text-right">Delta:</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {resolvedHands.map((hand) => {
                    const hero = hand.players.find((player) => player.is_hero)
                    const result = describeResult(hand)
                    const opponentHoleCards =
                        hand.players
                            .filter((player) => !player.is_hero && player.hole_cards)
                            .map((player) => player.hole_cards)
                            .join(', ') || '—'

                    return (
                        <TableRow key={hand.id}>
                            <TableCell>{hand.hand_number}</TableCell>
                            <TableCell>{hero.hole_cards}</TableCell>
                            <TableCell>{opponentHoleCards}</TableCell>
                            <TableCell className="text-center">
                                <Badge variant={result.variant}>{result.label}</Badge>
                            </TableCell>
                            <TableCell
                                className={`text-right ${
                                    hero.net_result > 0
                                        ? 'text-green-600'
                                        : hero.net_result < 0
                                          ? 'text-red-600'
                                          : ''
                                }`}
                            >
                                {hero.net_result > 0 ? '+' : ''}
                                {formatCurrency(hero.net_result)}
                            </TableCell>
                        </TableRow>
                    )
                })}
            </TableBody>
        </Table>
    )
}

export { HandHistoryTable }
