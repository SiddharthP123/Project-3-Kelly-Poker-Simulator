import { PlayingCard } from '@/components/poker/playing-card'
import { Button } from '@/components/ui/button'
import { formatCurrency } from '@/lib/format'

const WINNER_LABEL = {
    hero: 'You won!',
    opponent: 'You lost',
    split: 'Split pot',
}

const HandResultBanner = ({ hand, onDealNext }) => {
    const isWin = hand.hero_bankroll_delta > 0
    const isLoss = hand.hero_bankroll_delta < 0
    const deltaColorClass = isWin ? 'text-green-600' : isLoss ? 'text-red-600' : ''

    return (
        <div className="flex flex-col items-center gap-4 rounded-lg border p-4">
            <p className="text-lg font-semibold">{WINNER_LABEL[hand.winner] || hand.winner}</p>

            {hand.board_cards ? (
                <div className="flex flex-col items-center gap-2">
                    <span className="text-sm text-muted-foreground">Board</span>
                    <div className="flex gap-2">
                        {hand.board_cards.split(',').map((card) => (
                            <PlayingCard key={card} card={card} />
                        ))}
                    </div>
                </div>
            ) : (
                <p className="text-sm text-muted-foreground">
                    {hand.hero_action === 'fold'
                        ? 'You folded before showdown.'
                        : 'Opponent folded before showdown.'}
                </p>
            )}

            {hand.opponent_hole_cards && (
                <div className="flex flex-col items-center gap-2">
                    <span className="text-sm text-muted-foreground">Opponent&apos;s hand</span>
                    <div className="flex gap-2">
                        {hand.opponent_hole_cards.split(',').map((card) => (
                            <PlayingCard key={card} card={card} />
                        ))}
                    </div>
                </div>
            )}

            <p className={`text-lg font-semibold ${deltaColorClass}`}>
                {isWin ? '+' : ''}
                {formatCurrency(hand.hero_bankroll_delta)}
            </p>

            <Button onClick={onDealNext}>Deal next hand</Button>
        </div>
    )
}

export { HandResultBanner }
