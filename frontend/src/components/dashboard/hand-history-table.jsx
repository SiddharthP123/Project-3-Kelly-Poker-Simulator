import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatCurrency, formatPercent } from '@/lib/format'

const WINNER_BADGE_VARIANT = {
    hero: 'default',
    opponent: 'destructive',
    split: 'secondary',
}

const HandHistoryTable = ({ hands }) => {
    const resolvedHands = hands.filter((hand) => hand.hero_action !== null)

    if (resolvedHands.length === 0) {
        return <p className="text-sm text-muted-foreground">No hands played yet.</p>
    }

    return (
        <Table>
            <TableHeader>
                <TableRow>
                    <TableHead>#</TableHead>
                    <TableHead>Your hand</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Equity</TableHead>
                    <TableHead>Result</TableHead>
                    <TableHead className="text-right">Delta</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {resolvedHands.map((hand) => (
                    <TableRow key={hand.id}>
                        <TableCell>{hand.hand_number}</TableCell>
                        <TableCell>{hand.hero_hole_cards}</TableCell>
                        <TableCell className="capitalize">{hand.hero_action}</TableCell>
                        <TableCell>
                            {hand.equity_at_decision != null ? formatPercent(hand.equity_at_decision) : '—'}
                        </TableCell>
                        <TableCell>
                            <Badge variant={WINNER_BADGE_VARIANT[hand.winner] || 'outline'}>
                                {hand.winner || 'folded'}
                            </Badge>
                        </TableCell>
                        <TableCell
                            className={`text-right ${
                                hand.hero_bankroll_delta > 0
                                    ? 'text-green-600'
                                    : hand.hero_bankroll_delta < 0
                                      ? 'text-red-600'
                                      : ''
                            }`}
                        >
                            {hand.hero_bankroll_delta > 0 ? '+' : ''}
                            {formatCurrency(hand.hero_bankroll_delta)}
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    )
}

export { HandHistoryTable }
