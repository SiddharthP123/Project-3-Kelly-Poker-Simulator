import { PlayingCard } from '@/components/poker/playing-card'

/**
 * The 10 standard Texas Hold'em hand categories, worst to best, each with
 * one concrete 5-card example -- illustrated via the existing PlayingCard
 * (static, theme-independent -- see its own docstring), not AnimatedCard's
 * deal/flip machinery, which this static reference chart doesn't need.
 */
const HAND_RANKINGS = [
    {
        name: 'High Card',
        cards: ['2h', '5c', '9d', 'Jc', 'Ah'],
        description: 'No pair or better -- the highest single card plays.',
    },
    {
        name: 'Pair',
        cards: ['8h', '8s', '2d', '5c', 'Kc'],
        description: 'Two cards of the same rank.',
    },
    {
        name: 'Two Pair',
        cards: ['Jh', 'Js', '4d', '4c', '9s'],
        description: 'Two separate pairs.',
    },
    {
        name: 'Three of a Kind',
        cards: ['6h', '6d', '6s', '9c', 'Kd'],
        description: 'Three cards of the same rank.',
    },
    {
        name: 'Straight',
        cards: ['5h', '6d', '7s', '8c', '9h'],
        description: 'Five cards in consecutive rank order, mixed suits.',
    },
    {
        name: 'Flush',
        cards: ['2h', '6h', '9h', 'Jh', 'Kh'],
        description: 'Five cards of the same suit, any rank order.',
    },
    {
        name: 'Full House',
        cards: ['Th', 'Td', 'Ts', '4c', '4h'],
        description: 'Three of a kind plus a pair.',
    },
    {
        name: 'Four of a Kind',
        cards: ['9h', '9d', '9s', '9c', '2d'],
        description: 'Four cards of the same rank.',
    },
    {
        name: 'Straight Flush',
        cards: ['5s', '6s', '7s', '8s', '9s'],
        description: 'Five consecutive cards, all the same suit.',
    },
    {
        name: 'Royal Flush',
        cards: ['Th', 'Jh', 'Qh', 'Kh', 'Ah'],
        description: 'The best possible straight flush -- Ten through Ace, one suit.',
    },
]

const HandRankings = () => (
    <div className="flex flex-col gap-2">
        {HAND_RANKINGS.map((hand, index) => (
            <div
                key={hand.name}
                className="flex flex-col gap-2 rounded-lg border border-border p-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4"
            >
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
                        <PlayingCard key={cardIndex} card={card} size="sm" />
                    ))}
                </div>
            </div>
        ))}
    </div>
)

export { HandRankings }
