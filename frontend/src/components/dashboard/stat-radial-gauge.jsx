import { InfoIcon } from 'lucide-react'
import { PolarAngleAxis, RadialBar, RadialBarChart } from 'recharts'

import { CLASSIFICATION_COLORS, classifyStat } from '@/lib/stat-classifier'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

/**
 * A single-stat circular gauge (VPIP/PFR/WTSD%-style) -- `value` is a
 * 0-1 fraction (or null for "no data yet"), rendered as a 0-100% arc and
 * colored green/red/neutral via classifyStat, the same performance-based
 * meaning as the extended PlayStyleRadarChart's dots. `statKey` is one of
 * stat-classifier.js's own STAT_RANGES keys. `tooltip`, when passed,
 * renders a small hover-info icon next to the label explaining the
 * (often abbreviated) stat.
 */
const StatRadialGauge = ({ label, value, statKey, tooltip }) => {
    const percent = value == null ? 0 : Math.round(value * 1000) / 10
    const color = CLASSIFICATION_COLORS[classifyStat(statKey, value)]
    const data = [{ value: percent, fill: color }]

    return (
        <div className="flex flex-col items-center gap-1">
            <div className="relative h-24 w-24">
                <RadialBarChart
                    width={96}
                    height={96}
                    data={data}
                    innerRadius="70%"
                    outerRadius="100%"
                    startAngle={90}
                    endAngle={-270}
                    barSize={10}
                >
                    {/* Fixes the arc's scale to a real 0-100% -- without an
                        explicit domain, a single-bar RadialBarChart
                        auto-scales to the data itself, which would always
                        render as a full circle regardless of the actual
                        percentage. */}
                    <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                    <RadialBar dataKey="value" cornerRadius={6} background />
                </RadialBarChart>
                <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold tabular-nums">
                    {value == null ? '—' : `${percent.toFixed(1)}%`}
                </div>
            </div>
            <div className="flex items-center gap-1">
                <p className="text-xs text-muted-foreground">{label}</p>
                {tooltip && (
                    <Tooltip>
                        <TooltipTrigger
                            aria-label={`What is ${label}?`}
                            className="text-muted-foreground/60 hover:text-muted-foreground"
                        >
                            <InfoIcon className="size-3" />
                        </TooltipTrigger>
                        <TooltipContent>{tooltip}</TooltipContent>
                    </Tooltip>
                )}
            </div>
        </div>
    )
}

export { StatRadialGauge }
