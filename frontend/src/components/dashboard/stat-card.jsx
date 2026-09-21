import { InfoIcon } from 'lucide-react'

import { AnimatedNumber } from '@/components/ui/animated-number'
import { BorderBeam, EDUCATION_BORDER_BEAM_PROPS } from '@/components/ui/border-beam'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

// Matches stat-tile.jsx's own good/critical/neutral tokens -- kept as a
// separate translucent BorderBeam look (not StatTile's shared solid-card
// style) for pages that use the profile page's Player Snapshot styling.
const STAT_CARD_VARIANT_CLASSES = {
    good: 'text-green-600',
    critical: 'text-red-600',
    warning: 'text-amber-600',
    neutral: 'text-foreground',
}

/**
 * Same prop shape as StatTile (label/value/numericValue/formatValue/
 * variant/tooltip), so the two are interchangeable at call sites, plus:
 * `subtext`, when passed, renders inline next to the value (not on its own
 * line) so a card that needs an extra detail stays the same height as a
 * plain card; `className` reaches the BorderBeam wrapper for grid-span/
 * width overrides.
 */
const StatCard = ({ label, value, numericValue, formatValue, variant = 'neutral', tooltip, subtext, className }) => (
    <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS} className={className}>
        <div className="flex flex-col items-center gap-1 rounded-lg border border-border bg-transparent p-4">
            <div className="flex items-center gap-1">
                <p className="text-sm text-muted-foreground">{label}</p>
                {tooltip && (
                    <Tooltip>
                        <TooltipTrigger
                            aria-label={`What is ${label}?`}
                            className="text-muted-foreground/60 hover:text-muted-foreground"
                        >
                            <InfoIcon className="size-3.5" />
                        </TooltipTrigger>
                        <TooltipContent>{tooltip}</TooltipContent>
                    </Tooltip>
                )}
            </div>
            <p className={`flex items-baseline gap-2 text-xl font-semibold tabular-nums ${STAT_CARD_VARIANT_CLASSES[variant]}`}>
                {numericValue != null && formatValue ? (
                    <AnimatedNumber value={numericValue} format={formatValue} />
                ) : (
                    value
                )}
                {subtext && <span className="text-xs font-normal text-muted-foreground">{subtext}</span>}
            </p>
        </div>
    </BorderBeam>
)

export { StatCard }
