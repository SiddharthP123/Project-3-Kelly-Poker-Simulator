import { PolarAngleAxis, PolarGrid, Radar, RadarChart } from 'recharts'

import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'

// aggression_factor is an unbounded raises-to-calls ratio -- capped here
// (chart display only, never the raw number shown elsewhere) so it sits
// on the same 0-100 scale as the other three axes. An AF of 3+ is
// already extremely aggressive in real poker terms, so the cap rarely
// actually clips a realistic value.
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
 * Four axes, all normalized to a shared 0-100 scale: VPIP and aggression
 * factor are Part 13 Phase 4's new play-style metrics (the same
 * tight/loose and passive/aggressive axes poker/bots.py's personas are
 * built from, computed empirically instead of a fixed threshold); win
 * rate and fold rate reuse fields Part 12 Phase 7 already computes, not
 * re-derived here.
 * @param {object} stats - a UserStatsResponse
 */
const buildPlayStyleData = (stats) => [
    { axis: 'VPIP', value: stats.vpip_rate * 100 },
    {
        axis: 'Aggression',
        value:
            stats.aggression_factor == null
                ? 0
                : (Math.min(stats.aggression_factor, AGGRESSION_FACTOR_DISPLAY_CAP) / AGGRESSION_FACTOR_DISPLAY_CAP) * 100,
    },
    { axis: 'Win rate', value: stats.win_rate * 100 },
    { axis: 'Fold rate', value: stats.fold_rate * 100 },
]

const PlayStyleRadarChart = ({ stats }) => {
    if (stats.total_hands === 0) {
        return <p className="text-sm text-muted-foreground">Play a few hands to see your play style here.</p>
    }

    return (
        <ChartContainer config={chartConfig} className="h-64 w-full">
            <RadarChart data={buildPlayStyleData(stats)}>
                <PolarGrid />
                <PolarAngleAxis dataKey="axis" />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Radar dataKey="value" stroke="var(--color-value)" fill="var(--color-value)" fillOpacity={0.35} />
            </RadarChart>
        </ChartContainer>
    )
}

export { buildPlayStyleData, PlayStyleRadarChart }
