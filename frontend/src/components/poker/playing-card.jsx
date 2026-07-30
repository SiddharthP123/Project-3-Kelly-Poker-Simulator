const SUIT_GLYPHS = { h: '♥', d: '♦', c: '♣', s: '♠' }
const RED_SUITS = new Set(['h', 'd'])

/**
 * Renders one card from standard 2-character notation (e.g. 'Ah', 'Tc'),
 * matching poker/cards.py's Card.from_str/str(card) format exactly.
 */
const PlayingCard = ({ card }) => {
    const rank = card.slice(0, -1)
    const suit = card.slice(-1)
    const isRed = RED_SUITS.has(suit)

    return (
        <div
            className={`flex h-20 w-14 flex-col items-center justify-center rounded-lg border bg-card shadow-sm ${
                isRed ? 'text-red-600' : 'text-foreground'
            }`}
        >
            <span className="text-lg font-semibold">{rank}</span>
            <span className="text-2xl leading-none">{SUIT_GLYPHS[suit]}</span>
        </div>
    )
}

export { PlayingCard }
