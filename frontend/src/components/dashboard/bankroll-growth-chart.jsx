import { Line, LineChart, ReferenceArea, ReferenceLine, XAxis, YAxis } from 'recharts'

import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { formatCurrency } from '@/lib/format'
import { CLASSIFICATION_COLORS } from '@/lib/stat-classifier'

// Trend over time -> a single consistent line (never diverging red/green
// by magnitude -- color must follow the entity, not re-encode the value).
// The signed delta from session start is judged in a separate stat tile,
// not smeared across the line itself.
//
// Deliberately NOT using the theme's --chart-1 token here: this preset's
// chart palette is a grayscale ramp (chart-1 is a very light, low-contrast
// gray meant for multi-series charts), which washes out almost invisibly
// as a single highlighted line. An explicit, visible blue is used instead.
const chartConfig = {
    bankroll: {
        label: 'Bankroll',
        theme: {
            light: '#2a78d6',
            dark: '#3987e5',
        },
    },
}

// startingBankroll is optional -- the per-session dashboard (Part 10)
// passes it for a single dashed reference line, but an account-wide
// series (Part 13 Phase 4, spanning every session) has no single
// "starting" value to mark (each session resets to its own), so that
// chart just omits the prop rather than picking one session's value
// arbitrarily.
//
// `shaded` is a separate opt-in (Stats page only, Dashboard's per-session
// chart is unchanged) that tints the chart green above and red below the
// series' own first point -- there's still no single account-wide
// "starting bankroll" to anchor to, so the first recorded point is used
// as the reference the same way kelly-criterion-page.jsx's growth diagram
// anchors its own green/red split to growth=0.
const BankrollGrowthChart = ({ series, startingBankroll, shaded = false }) => {
    if (series.length === 0) {
        return <p className="text-sm text-muted-foreground">No bankroll history yet.</p>
    }

    const baseline = series[0].bankroll
    const bankrollValues = series.map((point) => point.bankroll)
    const maxBankroll = Math.max(...bankrollValues, baseline)
    const minBankroll = Math.min(...bankrollValues, baseline)

    return (
        <ChartContainer config={chartConfig} className="h-64 w-full">
            <LineChart data={series}>
                <XAxis dataKey="index" tickLine={false} axisLine={false} />
                <YAxis
                    tickLine={false}
                    axisLine={false}
                    width={80}
                    tickFormatter={(value) => formatCurrency(value)}
                />
                {shaded && (
                    <>
                        <ReferenceArea y1={baseline} y2={maxBankroll} fill={CLASSIFICATION_COLORS.good} fillOpacity={0.08} />
                        <ReferenceArea y1={minBankroll} y2={baseline} fill={CLASSIFICATION_COLORS.critical} fillOpacity={0.08} />
                        <ReferenceLine y={baseline} stroke="var(--muted-foreground)" strokeDasharray="4 4" />
                    </>
                )}
                {startingBankroll != null && (
                    <ReferenceLine y={startingBankroll} stroke="var(--muted-foreground)" strokeDasharray="4 4" />
                )}
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line type="monotone" dataKey="bankroll" stroke="var(--color-bankroll)" strokeWidth={2} dot={false} />
            </LineChart>
        </ChartContainer>
    )
}

export { BankrollGrowthChart }
