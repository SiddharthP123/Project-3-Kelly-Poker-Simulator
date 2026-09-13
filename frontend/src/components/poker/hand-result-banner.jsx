import { Button } from '@/components/ui/button'
import { formatCurrency, formatPersonaLabel } from '@/lib/format'

/**
 * hand: a completed HandResponse (street === 'complete'). Winners are
 * seat indices, not a single fixed 'hero'/'opponent'/'split' label like
 * Parts 8-10 -- with 1-4 opponents there can be any number of winners
 * (a split pot, or a genuinely uncontested side pot won by a seat who
 * wasn't even eligible for the whole thing).
 */
const HandResultBanner = ({ hand, onDealNext }) => {
    const hero = hand.players.find((player) => player.is_hero)
    const heroWon = hand.winners.includes(hero.seat_index)
    const isSplit = hand.winners.length > 1
    const deltaColorClass = hero.net_result > 0 ? 'text-green-500' : hero.net_result < 0 ? 'text-red-500' : ''

    const winnerLabel = isSplit
        ? 'Split pot'
        : heroWon
          ? 'You won!'
          : `${formatPersonaLabel(hand.players.find((p) => p.seat_index === hand.winners[0])?.persona || 'Opponent')} won`

    const nonFoldedRevealed = hand.players.filter((player) => !player.is_hero && player.hole_cards)

    return (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-white/15 bg-black/60 p-4 text-white">
            <p className="text-lg font-semibold">{winnerLabel}</p>

            {nonFoldedRevealed.length === 0 && (
                <p className="text-sm text-white/60">
                    {hero.folded ? 'You folded before showdown.' : 'Everyone else folded before showdown.'}
                </p>
            )}

            <p className={`text-lg font-semibold tabular-nums ${deltaColorClass}`}>
                {hero.net_result > 0 ? '+' : ''}
                {formatCurrency(hero.net_result)}
            </p>

            <Button onClick={onDealNext}>Deal next hand</Button>
        </div>
    )
}

export { HandResultBanner }
