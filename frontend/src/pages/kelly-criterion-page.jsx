import { AppHeader } from '@/components/layout/app-header'
import { GlossaryEntry } from '@/components/education/glossary-entry'

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
const MAX_ABS_GROWTH = Math.max(...GROWTH_BY_FRACTION.map((row) => Math.abs(row.growth)))

const GrowthByFractionDiagram = () => (
    <div className="flex flex-col gap-2 rounded-lg border border-border p-4">
        <p className="text-sm font-medium">
            Expected bankroll growth per bet, betting a 60%-to-win / even-money edge repeatedly
        </p>
        <div className="flex flex-col gap-1.5">
            {GROWTH_BY_FRACTION.map((row) => (
                <div key={row.fraction} className="flex items-center gap-2 text-sm">
                    <span className={`w-12 shrink-0 tabular-nums ${row.isKellyOptimal ? 'font-bold' : ''}`}>
                        {Math.round(row.fraction * 100)}%
                    </span>
                    <div className="flex h-4 flex-1 items-center">
                        <div
                            className={`h-full rounded-sm ${row.growth >= 0 ? 'bg-green-600' : 'bg-red-600'}`}
                            style={{ width: `${(Math.abs(row.growth) / MAX_ABS_GROWTH) * 100}%` }}
                        />
                    </div>
                    {row.isKellyOptimal && (
                        <span className="shrink-0 text-xs font-medium text-green-700 dark:text-green-500">
                            Kelly-optimal
                        </span>
                    )}
                </div>
            ))}
        </div>
        <p className="text-xs text-muted-foreground">
            Growth rises smoothly up to the Kelly fraction (20% here), then falls -- and eventually
            turns negative -- the further past it you bet, even though the bet itself hasn't changed.
        </p>
    </div>
)

/**
 * A public, no-login-required page (Part 14 Phase 3) explaining the Kelly
 * Criterion this whole project is built around -- registered outside
 * ProtectedRoute in app.jsx, same as the "How to Play" tutorial (Phase
 * 2), whose glossary component this page reuses. Pure static content.
 */
const KellyCriterionPage = () => (
    <div className="dark flex min-h-svh flex-col bg-background text-foreground">
        <AppHeader />
        <main className="mx-auto flex w-full max-w-3xl flex-col gap-10 p-4 pb-16">
            <div className="flex flex-col gap-2 pt-4">
                <h1 className="text-3xl font-bold">The Kelly Criterion</h1>
                <p className="text-muted-foreground">
                    The formula this whole simulator is built around -- what fraction of your
                    bankroll to stake on a bet where you have a real, known edge.
                </p>
            </div>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">The formula</h2>
                <p className="rounded-lg bg-muted p-4 text-center text-lg font-mono">f* = (bp − q) / b</p>
                <ul className="flex flex-col gap-2 pl-5">
                    <li className="list-disc">
                        <strong>f*</strong> -- the fraction of your bankroll to stake.
                    </li>
                    <li className="list-disc">
                        <strong>p</strong> -- your probability of winning the bet.
                    </li>
                    <li className="list-disc">
                        <strong>q</strong> -- your probability of losing, i.e. <code>1 − p</code>.
                    </li>
                    <li className="list-disc">
                        <strong>b</strong> -- the net odds you're getting: how many units you win per
                        unit staked if you win (even money is <code>b = 1</code>).
                    </li>
                </ul>
                <p>
                    A positive f* means you have a real edge and Kelly tells you how much of your
                    bankroll to risk to grow it fastest over the long run. A zero or negative f*
                    means there's no edge here at all -- the correct stake is nothing.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Step by step: a classic example</h2>
                <p>Suppose you have a 60% chance of winning a bet at even money (win $1 for every $1 staked):</p>
                <ol className="flex flex-col gap-2 pl-5">
                    <li className="list-decimal">
                        <code>p = 0.6</code> (60% win probability), so <code>q = 1 − 0.6 = 0.4</code>.
                    </li>
                    <li className="list-decimal">
                        <code>b = 1</code> (even money -- you win 1 unit per unit staked).
                    </li>
                    <li className="list-decimal">
                        <code>f* = (1 × 0.6 − 0.4) / 1 = 0.2</code>
                    </li>
                </ol>
                <p>
                    Kelly says to stake <strong>20% of your bankroll</strong> on this bet -- not 60%
                    (your win probability) and not 100% (however confident you feel). Betting more
                    than 20% here doesn't just add risk for more reward -- past a certain point it
                    makes your long-run growth rate worse too, since your losses can no longer be
                    outrun by compounding wins fast enough. The diagram below shows exactly that,
                    computed from this same bet:
                </p>
                <GrowthByFractionDiagram />
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Step by step: from a poker pot to a stake</h2>
                <p>
                    At the poker table there's no bookmaker quoting odds -- but the pot itself
                    implies them. Calling a bet risks <code>bet_to_call</code> to potentially win
                    the whole pot, so for every 1 unit risked you stand to win{' '}
                    <code>pot_size / bet_to_call</code> units -- exactly Kelly's <code>b</code>.
                </p>
                <ol className="flex flex-col gap-2 pl-5">
                    <li className="list-decimal">You've calculated your equity (win probability) at 60% -- <code>p = 0.6</code>.</li>
                    <li className="list-decimal">The pot is $100 and it costs $50 to call, so <code>b = 100 / 50 = 2</code>.</li>
                    <li className="list-decimal"><code>f* = (2 × 0.6 − 0.4) / 2 = 0.8 / 2 = 0.4</code></li>
                </ol>
                <p>
                    Kelly recommends staking <strong>40% of your bankroll</strong> here -- exactly
                    what this simulator's Kelly-recommended stake panel shows you live, every time
                    you face a real decision.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Beyond poker</h2>
                <p>
                    Kelly wasn't invented for poker -- it was originally derived for gambling
                    problems in general, but the identical formula is used today to size positions
                    in an investment portfolio: if you believe you have an edge (an expected return
                    better than the market's) and can express the payoff structure of the trade in
                    terms of p/q/b, Kelly gives the allocation that maximizes long-run compound
                    growth. Ed Thorp -- a professional card counter turned quantitative hedge fund
                    manager -- used exactly this reasoning to go from blackjack tables to
                    institutional investing. Poker just gives a cleaner, self-contained environment
                    (known edge, known odds, discrete bets) to learn the formula in before applying
                    the same thinking anywhere else.
                </p>
            </section>

            <section className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">Glossary</h2>
                <dl className="flex flex-col gap-3">
                    <GlossaryEntry term="Edge">
                        Having a real advantage in a bet -- your true win probability is better than
                        what the odds being offered would require to break even.
                    </GlossaryEntry>
                    <GlossaryEntry term="Full Kelly">Staking exactly the raw Kelly fraction, f*, with no adjustment.</GlossaryEntry>
                    <GlossaryEntry term="Fractional Kelly (e.g. half Kelly)">
                        Staking a fraction of f* itself (e.g. half of it) -- gives up some long-run
                        growth in exchange for meaningfully lower variance and smaller drawdowns,
                        since growth near the Kelly peak is flat but variance keeps rising with bet
                        size. This simulator's Kelly multiplier setting controls exactly this.
                    </GlossaryEntry>
                    <GlossaryEntry term="Log-growth">
                        The right quantity to maximize when a bet repeats many times, since a
                        bankroll compounds multiplicatively -- not the same as maximizing plain
                        expected value, which would push you to bet everything every time.
                    </GlossaryEntry>
                    <GlossaryEntry term="Risk of ruin">
                        The probability of losing your entire bankroll. Betting beyond the Kelly
                        fraction increases this at the same time it lowers your long-run growth rate.
                    </GlossaryEntry>
                </dl>
            </section>
        </main>
    </div>
)

export { KellyCriterionPage }
