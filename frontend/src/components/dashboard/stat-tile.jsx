import { motion } from 'framer-motion'
import { InfoIcon } from 'lucide-react'

import { AnimatedNumber } from '@/components/ui/animated-number'
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
 *
 * `numericValue`/`formatValue`, when both passed, swap the static `value`
 * text for a count-up (AnimatedNumber) instead. This is opt-in rather
 * than automatic for every numeric `value` so existing callers -- and the
 * synchronous assertions in stat-tile.test.jsx -- keep seeing their final
 * value on the very first render instead of an animation frame's worth
 * of "0".
 */
const StatTile = ({ label, value, numericValue, formatValue, variant = 'neutral', tooltip }) => (
    <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: 1.03, y: -3 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
    >
        <Card className="transition-shadow hover:shadow-lg hover:shadow-black/20">
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
                <p className={`text-xl font-semibold tabular-nums ${VARIANT_CLASSES[variant]}`}>
                    {numericValue != null && formatValue ? (
                        <AnimatedNumber value={numericValue} format={formatValue} />
                    ) : (
                        value
                    )}
                </p>
            </CardContent>
        </Card>
    </motion.div>
)

export { StatTile }
