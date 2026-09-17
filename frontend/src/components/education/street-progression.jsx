import { PlayingCard } from '@/components/poker/playing-card'

// One fixed worked example, told across all 4 streets -- hero's hole
// cards never change, the board only ever grows, matching how a real hand
// actually plays out (nothing is ever un-dealt).
const HERO_CARDS = ['Ah', 'Kd']
const BOARD_CARDS = ['Jh', '8c', '2d', '5s', '9h']

const STREETS = [
    {
        name: 'Preflop:',
        boardCount: 0,
        description: 'Hole cards are dealt. The first betting round.',
    },
    {
        name: 'Flop:',
        boardCount: 3,
        description: 'The first 3 community cards are revealed at once.',
    },
    { name: 'Turn:', boardCount: 4, description: 'A 4th community card is revealed.' },
    { name: 'River', boardCount: 5, description: 'The 5th and final community card is revealed.' },
]

/**
 * Undealt-card placeholder, matching the dashed-outline pattern used for
 * the live table's own empty board/hero slots (poker-table.jsx) -- same
 * fixed h-14 w-10 footprint as PlayingCard's own `sm` size, so a row of
 * mixed dealt/undealt cards lines up.
 */
const UndealtSlot = () => (
    <div className="h-14 w-10 rounded-lg border border-dashed border-muted-foreground/40" />
)

/**
 * A single worked hand shown across all 4 streets -- hero's 2 hole cards
 * stay fixed while the board builds up 0 -> 3 -> 4 -> 5 cards, so a
 * first-time reader can see exactly what "more of the board" means street
 * by street, not just read about it.
 *
 * Each row highlights (white glow, same style as hand-rankings.jsx) only
 * the card(s) that street actually deals -- hero's 2 hole cards on
 * Preflop, the 3 flop cards on Flop, just the 4th card on Turn, just the
 * 5th on River -- rather than every card dealt so far, so the glow always
 * points at what's new about that specific row.
 */
const StreetProgression = () => (
    <div className="flex flex-col gap-3">
        {STREETS.map((street) => {
            // The flop deals 3 cards at once (new cards start at index 0);
            // the turn and river each deal exactly 1 new card (the last
            // index that street's boardCount reaches).
            const newBoardStart = street.boardCount === 3 ? 0 : street.boardCount - 1

            return (
                <div
                    key={street.name}
                    className="flex flex-col gap-3 rounded-lg border border-border p-3 sm:flex-row sm:items-center sm:gap-6"
                >
                    <div className="sm:w-44 sm:shrink-0">
                        <p className="font-semibold">{street.name}</p>
                        <p className="text-sm text-muted-foreground">{street.description}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-4">
                        <div className="flex items-center gap-1.5">
                            <span className="mr-1 text-xs text-muted-foreground">Your hand</span>
                            {HERO_CARDS.map((card, index) => (
                                <PlayingCard key={index} card={card} size="sm" highlighted={street.boardCount === 0} />
                            ))}
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="mr-1 text-xs text-muted-foreground">Board</span>
                            {BOARD_CARDS.map((card, index) =>
                                index < street.boardCount ? (
                                    <PlayingCard
                                        key={index}
                                        card={card}
                                        size="sm"
                                        highlighted={index >= newBoardStart}
                                    />
                                ) : (
                                    <UndealtSlot key={index} />
                                ),
                            )}
                        </div>
                    </div>
                </div>
            )
        })}
    </div>
)

export { StreetProgression }
