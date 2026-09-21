import { PolarAngleAxis, PolarGrid, Radar, RadarChart } from 'recharts'

import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { CLASSIFICATION_COLORS, classifyStat } from '@/lib/stat-classifier'

// aggression_factor is an unbounded raises-to-calls ratio -- capped here
// (chart display only, never the raw number shown elsewhere) so it sits
// on the same 0-100 scale as the other axes. An AF of 3+ is already
// extremely aggressive in real poker terms, so the cap rarely actually
// clips a realistic value.
const AGGRESSION_FACTOR_DISPLAY_CAP = 3

const chartConfig = {
    value: {
        label: 'Play style',
        theme: {
            light: '#2a78d6',
            dark: '#3987e5',
        },
    },
}

/**
 * Five axes, all normalized to a shared 0-100 scale: VPIP, PFR, and
 * aggression factor are play-style metrics (the same tight/loose and
 * passive/aggressive axes poker/bots.py's personas are built from,
 * computed empirically instead of a fixed threshold); win rate and fold
 * rate reuse fields Part 12 Phase 7 already computes, not re-derived
 * here. Each point also carries a `classification` ('good'/'critical'/
 * 'neutral', from stat-classifier.js) used to color that axis's dot --
 * win rate/fold rate aren't covered by the classifier (no fixed "good"
 * range makes sense without knowing num_opponents), so they render as
 * plain neutral dots rather than a fabricated judgment.
 * @param {object} stats - a UserStatsResponse
 */
const buildPlayStyleData = (stats) => [
    { axis: 'VPIP:', value: stats.vpip_rate * 100, classification: classifyStat('vpip', stats.vpip_rate) },
    { axis: 'PFR:', value: stats.pfr_rate * 100, classification: classifyStat('pfr', stats.pfr_rate) },
    {
        axis: 'Aggression:',
        value:
            stats.aggression_factor == null
                ? 0
                : (Math.min(stats.aggression_factor, AGGRESSION_FACTOR_DISPLAY_CAP) / AGGRESSION_FACTOR_DISPLAY_CAP) * 100,
        classification: classifyStat('aggressionFactor', stats.aggression_factor),
    },
    { axis: 'Win Rate:', value: stats.win_rate * 100, classification: 'neutral' },
    { axis: 'Fold Rate:', value: stats.fold_rate * 100, classification: 'neutral' },
]

const renderClassifiedDot = (props) => {
    const { cx, cy, payload } = props
    return (
        <circle
            key={payload.axis}
            cx={cx}
            cy={cy}
            r={5}
            fill={CLASSIFICATION_COLORS[payload.classification]}
            stroke="var(--background)"
            strokeWidth={1.5}
        />
    )
}

const PlayStyleRadarChart = ({ stats }) => {
    if (stats.total_hands === 0) {
        return <p className="text-sm text-muted-foreground">Play a few hands to see your play style here.</p>
    }

    return (
        <ChartContainer config={chartConfig} className="h-96 w-full">
            <RadarChart data={buildPlayStyleData(stats)}>
                {/* An explicit stroke (not recharts' own default "#ccc")
                    bypasses ChartContainer's CSS rule that dims "#ccc" grid
                    lines down to the barely-visible --border token -- the
                    grid is the chart's own axis structure, not incidental
                    chrome, so it should read clearly against the felt. */}
                <PolarGrid stroke="rgba(255,255,255,0.35)" />
                <PolarAngleAxis dataKey="axis" />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Radar
                    dataKey="value"
                    stroke="var(--color-value)"
                    fill="var(--color-value)"
                    fillOpacity={0.35}
                    dot={renderClassifiedDot}
                />
            </RadarChart>
        </ChartContainer>
    )
}

export { buildPlayStyleData, PlayStyleRadarChart }
