/**
 * One term in a glossary <dl> -- shared by the "How to Play" tutorial
 * (Part 14 Phase 2) and the Kelly Criterion education page (Phase 3) so
 * both pages' glossaries render identically rather than duplicating the
 * markup.
 */
const GlossaryEntry = ({ term, children }) => (
    <div className="flex flex-col gap-1 border-b border-border pb-3 last:border-0 last:pb-0">
        <dt className="font-semibold">{term}</dt>
        <dd className="text-sm text-muted-foreground">{children}</dd>
    </div>
)

export { GlossaryEntry }
