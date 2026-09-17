/**
 * One term in a glossary <dl> -- shared by the "How to Play" tutorial
 * (Part 14 Phase 2) and the Kelly Criterion education page (Phase 3) so
 * both pages' glossaries render identically rather than duplicating the
 * markup. The divider between entries matches how-to-play-page.jsx's own
 * outer border (border-2, white/25) rather than the theme's default
 * border token, so it reads as the same visual system, not two.
 */
const GlossaryEntry = ({ term, children }) => (
    <div className="flex flex-col gap-1 border-b-2 border-white/25 pb-3 last:border-0 last:pb-0">
        <dt className="font-semibold">{term}</dt>
        <dd className="text-sm text-muted-foreground">{children}</dd>
    </div>
)

export { GlossaryEntry }
