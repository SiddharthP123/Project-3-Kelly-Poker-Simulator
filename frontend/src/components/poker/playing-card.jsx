const SUIT_GLYPHS = { h: '♥', d: '♦', c: '♣', s: '♠' }
const RED_SUITS = new Set(['h', 'd'])

const SIZE_CLASSES = {
    sm: 'h-14 w-10 text-sm',
    md: 'h-20 w-14 text-lg',
}

/**
 * Renders one card from standard 2-character notation (e.g. 'Ah', 'Tc'),
 * matching poker/cards.py's Card.from_str/str(card) format exactly.
 *
 * Always rendered as a light card face against a dark background --
 * unlike the rest of the app, the poker table's look is deliberately
 * fixed (black felt, white/black cards, red suit glyphs), not tied to
 * the app's own light/dark theme toggle, since a felt table doesn't
 * "go light mode."
 *
 * faceDown: renders a card back instead of the real rank/suit -- used
 * for opponents' hidden hole cards, which the API never even sends the
 * real values for (this isn't policy-hiding a value the frontend already
 * has; the backend redacts at the response layer, so there's nothing to
 * hide here beyond just rendering a placeholder).
 *
 * `highlighted`: the education pages (hand-rankings.jsx, street-progression.jsx)
 * use this to pick out which specific cards make a hand -- e.g. only the
 * two 8s in a "Pair" example, not the 3 unrelated kickers. A gold/amber
 * ring rather than white -- white on a white card face has almost no
 * contrast, so it barely read as "highlighted" at all -- kept here rather
 * than duplicated per caller so both pages render the exact same style.
 */
const PlayingCard = ({ card, faceDown = false, size = 'md', highlighted = false }) => {
    const sizeClass = SIZE_CLASSES[size] || SIZE_CLASSES.md
    const highlightClass = highlighted
        ? 'ring-4 ring-amber-400 shadow-[0_0_22px_6px_rgba(251,191,36,0.9)]'
        : ''

    if (faceDown) {
        return (
            <div
                className={`flex ${sizeClass} items-center justify-center rounded-lg border border-white/20 bg-gradient-to-br from-zinc-700 to-zinc-900 shadow-sm ${highlightClass}`}
                aria-label="Face-down card"
            >
                <span className="text-white/30">◆</span>
            </div>
        )
    }

    const rank = card.slice(0, -1)
    const suit = card.slice(-1)
    const isRed = RED_SUITS.has(suit)

    return (
        <div
            className={`flex ${sizeClass} flex-col items-center justify-center rounded-lg border border-black/10 bg-white shadow-sm ${
                isRed ? 'text-red-600' : 'text-zinc-900'
            } ${highlightClass}`}
        >
            <span className="font-semibold leading-none">{rank}</span>
            <span className="text-[1.4em] leading-none">{SUIT_GLYPHS[suit]}</span>
        </div>
    )
}

export { PlayingCard }
