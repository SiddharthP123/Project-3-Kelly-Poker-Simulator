import { PlayingCard } from '@/components/poker/playing-card'
import { BorderBeam } from '@/components/ui/border-beam'

/**
 * The 10 standard Texas Hold'em hand categories, worst to best, each with
 * one concrete 5-card example, illustrated via the existing PlayingCard
 * (static, theme-independent, see its own docstring), not AnimatedCard's
 * deal/flip machinery, which this static reference chart doesn't need.
 *
 * `highlight`: indices (into `cards`) of the cards that actually make the
 * category -- e.g. only the two 8s for "Pair", not the 3 unrelated
 * kickers. Categories where the whole 5-card hand matters (straight,
 * flush, full house, straight flush, royal flush) highlight all 5.
 */
const HAND_RANKINGS = [
    {
        name: 'High Card:',
        cards: ['2h', '5c', '9d', 'Jc', 'Ah'],
        highlight: [4],
        description: 'No pair or better, so the highest single card plays.',
    },
    {
        name: 'Pair:',
        cards: ['8h', '8s', '2d', '5c', 'Kc'],
        highlight: [0, 1],
        description: 'Two cards of the same rank.',
    },
    {
        name: 'Two Pair:',
        cards: ['Jh', 'Js', '4d', '4c', '9s'],
        highlight: [0, 1, 2, 3],
        description: 'Two separate pairs.',
    },
    {
        name: 'Three of a Kind',
        cards: ['6h', '6d', '6s', '9c', 'Kd'],
        highlight: [0, 1, 2],
        description: 'Three cards of the same rank.',
    },
    {
        name: 'Straight:',
        cards: ['5h', '6d', '7s', '8c', '9h'],
        highlight: [0, 1, 2, 3, 4],
        description: 'Five cards in consecutive rank order, mixed suits.',
    },
    {
        name: 'Flush:',
        cards: ['2h', '6h', '9h', 'Jh', 'Kh'],
        highlight: [0, 1, 2, 3, 4],
        description: 'Five cards of the same suit, any rank order.',
    },
    {
        name: 'Full House:',
        cards: ['Th', 'Td', 'Ts', '4c', '4h'],
        highlight: [0, 1, 2, 3, 4],
        description: 'Three of a kind plus a pair.',
    },
    {
        name: 'Four of a Kind',
        cards: ['9h', '9d', '9s', '9c', '2d'],
        highlight: [0, 1, 2, 3],
        description: 'Four cards of the same rank.',
    },
    {
        name: 'Straight Flush:',
        cards: ['5s', '6s', '7s', '8s', '9s'],
        highlight: [0, 1, 2, 3, 4],
        description: 'Five consecutive cards, all the same suit.',
    },
    {
        name: 'Royal Flush',
        cards: ['Th', 'Jh', 'Qh', 'Kh', 'Ah'],
        highlight: [0, 1, 2, 3, 4],
        description: 'The best possible straight flush -- Ten through Ace, one suit.',
    },
]

const HandRankings = () => (
    <div className="flex flex-col gap-3">
        {HAND_RANKINGS.map((hand, index) => (
            <BorderBeam key={hand.name} size="md" colorVariant="colorful" theme="dark">
                <div className="flex flex-col gap-2 rounded-lg border border-border p-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
                    <div>
                        <p className="font-semibold">
                            <span className="mr-2 tabular-nums text-muted-foreground">
                                {HAND_RANKINGS.length - index}.
                            </span>
                            <span>{hand.name}</span>
                        </p>
                        <p className="text-sm text-muted-foreground">{hand.description}</p>
                    </div>
                    <div className="flex gap-1">
                        {hand.cards.map((card, cardIndex) => (
                            <PlayingCard
                                key={cardIndex}
                                card={card}
                                size="sm"
                                highlighted={hand.highlight.includes(cardIndex)}
                            />
                        ))}
                    </div>
                </div>
            </BorderBeam>
        ))}
    </div>
)

export { HandRankings }
