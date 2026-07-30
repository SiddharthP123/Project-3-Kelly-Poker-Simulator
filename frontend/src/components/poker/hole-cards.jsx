import { PlayingCard } from '@/components/poker/playing-card'

/** cardsString: comma-joined card notation, e.g. 'Ah,Ac'. */
const HoleCards = ({ cardsString, label }) => {
    if (!cardsString) {
        return null
    }

    const cards = cardsString.split(',')

    return (
        <div className="flex flex-col items-center gap-2">
            {label && <span className="text-sm text-muted-foreground">{label}</span>}
            <div className="flex gap-2">
                {cards.map((card) => (
                    <PlayingCard key={card} card={card} />
                ))}
            </div>
        </div>
    )
}

export { HoleCards }
