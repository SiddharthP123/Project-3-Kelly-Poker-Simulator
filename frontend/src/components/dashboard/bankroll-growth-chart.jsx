import { Line, LineChart, ReferenceLine, XAxis, YAxis } from 'recharts'

import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { formatCurrency } from '@/lib/format'

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

const BankrollGrowthChart = ({ series, startingBankroll }) => {
    if (series.length === 0) {
        return <p className="text-sm text-muted-foreground">No bankroll history yet.</p>
    }

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
                <ReferenceLine y={startingBankroll} stroke="var(--muted-foreground)" strokeDasharray="4 4" />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line type="monotone" dataKey="bankroll" stroke="var(--color-bankroll)" strokeWidth={2} dot={false} />
            </LineChart>
        </ChartContainer>
    )
}

export { BankrollGrowthChart }
