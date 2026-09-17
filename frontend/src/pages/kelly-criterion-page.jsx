import {
    Bar,
    CartesianGrid,
    Cell,
    ComposedChart,
    Line,
    ReferenceArea,
    ReferenceDot,
    ReferenceLine,
    XAxis,
    YAxis,
} from 'recharts'

import { GlossaryEntry } from '@/components/education/glossary-entry'
import { AppHeader } from '@/components/layout/app-header'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { BorderBeam, EDUCATION_BORDER_BEAM_PROPS } from '@/components/ui/border-beam'
import { CLASSIFICATION_COLORS } from '@/lib/stat-classifier'

/**
 * Expected per-bet log-growth rate at p=0.6, b=1 (even money) -- the same
 * classic textbook numbers as poker/kelly.py's own
 * test_kelly_fraction_matches_classic_example, computed directly from
 * poker.kelly.expected_log_growth(0.6, 1, fraction) rather than invented
 * for this page. Growth peaks at fraction=0.2 (the Kelly-optimal stake
 * for this bet) and turns negative well before fraction=1.0 -- betting
 * more than Kelly makes both risk of ruin AND long-run growth worse at
 * the same time, which is the whole point of the diagram below.
 */
const GROWTH_BY_FRACTION = [
    { fraction: 0.0, growth: 0.0 },
    { fraction: 0.1, growth: 0.015 },
    { fraction: 0.2, growth: 0.0201, isKellyOptimal: true },
    { fraction: 0.3, growth: 0.0148 },
    { fraction: 0.4, growth: -0.0025 },
    { fraction: 0.5, growth: -0.034 },
    { fraction: 0.6, growth: -0.0845 },
]

// Recharts wants plain percentage numbers (20, not 0.2) to format/plot
// cleanly -- derived here once rather than re-scaled inline at every
// axis/tooltip/cell callback.
const GROWTH_CHART_DATA = GROWTH_BY_FRACTION.map((row) => ({
    fractionPct: row.fraction * 100,
    growthPct: row.growth * 100,
}))
const MAX_GROWTH_PCT = Math.max(...GROWTH_CHART_DATA.map((row) => row.growthPct))
const MIN_GROWTH_PCT = Math.min(...GROWTH_CHART_DATA.map((row) => row.growthPct))
const KELLY_OPTIMAL_POINT =
    GROWTH_CHART_DATA[GROWTH_BY_FRACTION.findIndex((row) => row.isKellyOptimal)]

const growthChartConfig = {
    growthPct: { label: 'Expected Growth Per Bet:' },
}

/**
 * A real coordinate chart (recharts ComposedChart), not just proportional
 * bar widths -- a bold ReferenceLine at growth=0 is the chart's actual
 * origin, with a green-tinted region above it (bankroll still compounds)
 * and a red-tinted region below it (bankroll shrinks), each bar colored
 * to match. The amber Line traces the same values as the bar tops, so
 * the "rises then falls" shape Kelly's formula produces reads as one
 * continuous curve, not just a sequence of disconnected bars.
 */
const GrowthByFractionDiagram = () => (
    <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS}>
        <div className="flex flex-col gap-2 rounded-lg border border-border p-4">
            <p className="text-sm font-medium">
                Expected Bankroll Growth Per Bet, Betting a 60%-to-win / Even-Money Edge Repeatedly:
            </p>
            <ChartContainer config={growthChartConfig} className="h-64 w-full">
                <ComposedChart
                    data={GROWTH_CHART_DATA}
                    margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
                >
                    <CartesianGrid vertical={false} strokeDasharray="3 3" />
                    <ReferenceArea
                        y1={0}
                        y2={MAX_GROWTH_PCT}
                        fill={CLASSIFICATION_COLORS.good}
                        fillOpacity={0.08}
                    />
                    <ReferenceArea
                        y1={MIN_GROWTH_PCT}
                        y2={0}
                        fill={CLASSIFICATION_COLORS.critical}
                        fillOpacity={0.08}
                    />
                    <XAxis
                        dataKey="fractionPct"
                        tickFormatter={(value) => `${value}%`}
                        tickLine={false}
                        axisLine={{ stroke: 'var(--border)' }}
                    />
                    <YAxis
                        tickFormatter={(value) => `${value.toFixed(1)}%`}
                        tickLine={false}
                        axisLine={{ stroke: 'var(--border)' }}
                        width={56}
                    />
                    <ReferenceLine y={0} stroke="var(--foreground)" strokeWidth={2} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar dataKey="growthPct" radius={3} maxBarSize={36}>
                        {GROWTH_CHART_DATA.map((row) => (
                            <Cell
                                key={row.fractionPct}
                                fill={
                                    row.growthPct >= 0
                                        ? CLASSIFICATION_COLORS.good
                                        : CLASSIFICATION_COLORS.critical
                                }
                            />
                        ))}
                    </Bar>
                    <Line
                        type="monotone"
                        dataKey="growthPct"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        dot={{ r: 3, fill: '#f59e0b', strokeWidth: 0 }}
                        activeDot={{ r: 4 }}
                    />
                    <ReferenceDot
                        x={KELLY_OPTIMAL_POINT.fractionPct}
                        y={KELLY_OPTIMAL_POINT.growthPct}
                        r={5}
                        fill="#f59e0b"
                        stroke="var(--background)"
                        strokeWidth={2}
                        label={{
                            value: 'Kelly-Optimal:',
                            position: 'top',
                            fill: CLASSIFICATION_COLORS.good,
                            fontSize: 11,
                            fontWeight: 600,
                        }}
                    />
                </ComposedChart>
            </ChartContainer>
            <p className="text-xs text-muted-foreground">
                Expected Growth Per Bet: Growth rises smoothly up to the Kelly fraction (20% here),
                falls, then eventually turns negative. The further past it you bet, the more
                negative the growth becomes, even though the bet itself hasn't changed. The zero
                line is the break-even point: green bars above it still grow your bankroll, red bars
                below it shrink it.
            </p>
        </div>
    </BorderBeam>
)

/**
 * A public, no-login-required page (Part 14 Phase 3) explaining the Kelly
 * Criterion this whole project is built around -- registered outside
 * ProtectedRoute in app.jsx, same as the "How to Play" tutorial (Phase
 * 2), whose glossary component this page reuses. Pure static content.
 */
const KellyCriterionPage = () => (
    <div className="flex min-h-svh flex-col">
        <AppHeader />
        <main className="mx-auto mt-8 flex w-full max-w-3xl flex-col gap-10 rounded-xl border-2 border-white/25 p-6 pb-16 sm:mt-12 sm:p-10">
            <div className="flex flex-col gap-4 pt-4">
                <h1 className="text-3xl font-bold">The Kelly Criterion:</h1>
                <p className="text-muted-foreground">
                    The formula the entire simulator is built around. This page aims to give you a
                    beginner's understanding of the math behind this criterion. It can be simply
                    defined as a factor deciding what fraction of your bankroll to stake on a bet
                    where you have a real, known edge.
                </p>
            </div>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">The Formula:</h2>
                <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS}>
                    <p className="rounded-lg border border-border p-4 text-center text-lg font-mono">
                        f* = (bp − q) / b
                    </p>
                </BorderBeam>
                <ul className="flex flex-col gap-2 pl-5">
                    <li className="list-disc">
                        <strong>f*</strong> : the fraction of your bankroll to stake.
                    </li>
                    <li className="list-disc">
                        <strong>p</strong> : your probability of winning the bet.
                    </li>
                    <li className="list-disc">
                        <strong>q</strong> : your probability of losing, i.e. <code>1 − p</code>.
                    </li>
                    <li className="list-disc">
                        <strong>b</strong> : the net odds you're getting: how many units you win per
                        unit staked if you win (even money is <code>b = 1</code>).
                    </li>
                </ul>
                <p>
                    A positive f* means you have a real edge and the Kelly Criterion tells you how
                    much of your bankroll to risk to grow it fastest over the long run. A zero or
                    negative f* means there's no edge here at all, so the correct stake to risk is
                    nothing.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">A General Example:</h2>
                <p>
                    Suppose you have a 60% chance of winning a bet at even money (win $1 for every
                    $1 staked):
                </p>
                <ol className="flex flex-col gap-2 pl-5">
                    <li className="list-decimal">
                        <code>p = 0.6</code> (60% win probability), so{' '}
                        <code>q = 1 − 0.6 = 0.4</code>.
                    </li>
                    <li className="list-decimal">
                        <code>b = 1</code> (even money, you win 1 unit per unit staked).
                    </li>
                    <li className="list-decimal">
                        <code>f* = (1 × 0.6 − 0.4) / 1 = 0.2</code>
                    </li>
                </ol>
                <p>
                    Kelly says to stake <strong>20% of your bankroll</strong> on this bet, not 60%
                    (your win probability) and not 100% (however confident you feel). Betting more
                    than 20% here doesn't just add risk for more reward. Past a certain point, it
                    makes your long-run growth rate worse too, since your losses can no longer be
                    outrun by compounding wins fast enough. The diagram below shows exactly that,
                    computed from this same bet:
                </p>
                <GrowthByFractionDiagram />
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">At the Poker Table</h2>
                <p>
                    On the board, there's no bookmaker quoting odds, but the pot itself implies
                    them. Calling a bet risks <code>bet_to_call</code> to potentially win the whole
                    pot, so for every 1 unit risked you stand to win{' '}
                    <code>pot_size / bet_to_call</code> units, which is exactly Kelly's{' '}
                    <code>b</code>.
                </p>
                <ol className="flex flex-col gap-2 pl-5">
                    <li className="list-decimal">
                        You've calculated your equity (win probability) at 60% --{' '}
                        <code>p = 0.6</code>.
                    </li>
                    <li className="list-decimal">
                        The pot is $100 and it costs $50 to call, so <code>b = 100 / 50 = 2</code>.
                    </li>
                    <li className="list-decimal">
                        <code>f* = (2 × 0.6 − 0.4) / 2 = 0.8 / 2 = 0.4</code>
                    </li>
                </ol>
                <p>
                    Kelly recommends staking <strong>40% of your bankroll</strong> here. This is
                    exactly what this simulator's Kelly-recommended stake panel shows you live every
                    time you face a real decision.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Beyond Poker - Into Finance:</h2>
                <p>
                    Kelly wasn't invented for poker, but rather originally derived for gambling
                    problems in general, however the identical formula is used today to size
                    positions in an investment portfolio: if you believe you have an edge (an
                    expected return better than the market's) and can express the payoff structure
                    of the trade in terms of p/q/b, Kelly gives the allocation that maximizes
                    long-run compound growth. Ed Thorp, a professional card counter turned
                    quantitative hedge fund manager, used exactly this reasoning to go from
                    blackjack tables to institutional investing. Poker gives a cleaner,
                    self-contained environment (known edge, known odds, discrete bets) to learn the
                    formula in before applying the same thinking anywhere else, the aim of this
                    simulator. Being into both poker and finance myself, is what inspired me to
                    build the sim in the first place.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Glossary:</h2>
                <dl className="flex flex-col gap-3">
                    <GlossaryEntry term="Edge">
                        Having a real advantage in a bet. When your true win probability is better
                        than what the odds being offered would require to break even.
                    </GlossaryEntry>
                    <GlossaryEntry term="Full Kelly">
                        Staking exactly the raw Kelly fraction, f*, with no adjustment.
                    </GlossaryEntry>
                    <GlossaryEntry term="Fractional Kelly (e.g. half Kelly)">
                        Staking a fraction of f* itself (e.g. half of it), gives up some long-run
                        growth in exchange for meaningfully lower variance and smaller drawdowns,
                        since growth near the Kelly peak is flat but variance keeps rising with bet
                        size. This simulator's Kelly multiplier setting controls exactly this.
                    </GlossaryEntry>
                    <GlossaryEntry term="Log-growth">
                        The right quantity to maximize when a bet repeats many times, since a
                        bankroll compounds multiplicatively (not the same as maximizing plain
                        expected value, which would push you to bet everything every time).
                    </GlossaryEntry>
                    <GlossaryEntry term="Risk of ruin">
                        The probability of losing your entire bankroll. Betting beyond the Kelly
                        fraction increases this at the same time it lowers your long-run growth
                        rate.
                    </GlossaryEntry>
                </dl>
            </section>
        </main>
    </div>
)

export { KellyCriterionPage }
