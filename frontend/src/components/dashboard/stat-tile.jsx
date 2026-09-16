import { InfoIcon } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

// Status-meaning tokens, not the generic categorical ramp -- these
// colors mean "good/bad/neutral", so they must never share a chart with
// plain arbitrary category hues.
const VARIANT_CLASSES = {
    good: 'text-green-600',
    critical: 'text-red-600',
    warning: 'text-amber-600',
    neutral: 'text-foreground',
}

/**
 * `tooltip`, when passed, renders a small hover-info icon next to the
 * label explaining what the (often abbreviated) stat means -- optional
 * so plain tiles with a self-explanatory label don't need one.
 */
const StatTile = ({ label, value, variant = 'neutral', tooltip }) => (
    <Card>
        <CardContent className="flex flex-col items-center gap-1 py-4">
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
            <p className={`text-xl font-semibold ${VARIANT_CLASSES[variant]}`}>{value}</p>
        </CardContent>
    </Card>
)

export { StatTile }
