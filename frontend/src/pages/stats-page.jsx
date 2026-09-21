import { motion } from 'framer-motion'
import { useCallback, useEffect, useState } from 'react'

import { BankrollGrowthChart } from '@/components/dashboard/bankroll-growth-chart'
import { PlayStyleRadarChart } from '@/components/dashboard/play-style-radar-chart'
import { StatCard } from '@/components/dashboard/stat-card'
import { StatRadialGauge } from '@/components/dashboard/stat-radial-gauge'
import { WinRateSummary } from '@/components/dashboard/win-rate-summary'
import { AppHeader } from '@/components/layout/app-header'
import { BorderBeam, EDUCATION_BORDER_BEAM_PROPS } from '@/components/ui/border-beam'
import { useUserStats } from '@/hooks/use-user-stats'
import { computeBankrollSeries } from '@/lib/compute-bankroll-series'
import { formatCurrency } from '@/lib/format'
import { STAT_DESCRIPTIONS } from '@/lib/stat-descriptions'

// Mirrors dashboard-page.jsx's stagger pattern (itself adapted from the
// 21st.dev "Marketing Dashboard" bookmark) so both stat-heavy pages feel
// like the same system rather than two different animation styles.
const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.12 } },
}
const itemVariants = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
}

/**
 * Account-wide statistics, aggregated across every session the user has
 * ever played (Part 12 Phase 7) -- distinct from the existing per-session
 * dashboard (Part 10), which only ever looks at one session at a time.
 *
 * The backend already returns win/loss/split/fold as flat count/rate
 * pairs (win_count, win_rate, ...); WinRateSummary expects the nested
 * {count, pct} shape computeWinRate() produces for the per-session
 * dashboard -- reshaping it here is simpler than teaching a second shape
 * to a component that already does exactly what this page needs.
 */
const StatsPage = () => {
    const { getMyStats } = useUserStats()

    const [stats, setStats] = useState(null)
    const [errorMessage, setErrorMessage] = useState('')

    const loadStats = useCallback(async () => {
        try {
            const data = await getMyStats()
            setStats(data)
        } catch (error) {
            setErrorMessage(
                error.detail || 'Could not load your statistics. Please try again later.',
            )
        }
    }, [getMyStats])

    useEffect(() => {
        loadStats()
    }, [loadStats])

    if (errorMessage) {
        return (
            <div className="flex min-h-svh flex-col">
                <AppHeader />
                <p className="p-4 text-center text-sm text-destructive">{errorMessage}</p>
            </div>
        )
    }

    if (!stats) {
        return (
            <div className="flex min-h-svh flex-col">
                <AppHeader />
                <p className="p-4 text-center text-muted-foreground">Loading...</p>
            </div>
        )
    }

    const winRate = {
        total: stats.total_hands,
        win: { count: stats.win_count, pct: stats.win_rate },
        loss: { count: stats.loss_count, pct: stats.loss_rate },
        split: { count: stats.split_count, pct: stats.split_rate },
        fold: { count: stats.fold_count, pct: stats.fold_rate },
    }

    const allTimeWinningsVariant =
        stats.cumulative_bankroll_change > 0
            ? 'good'
            : stats.cumulative_bankroll_change < 0
              ? 'critical'
              : 'neutral'
    const allTimeWinningsPct =
        stats.cumulative_starting_bankroll > 0
            ? (stats.cumulative_bankroll_change / stats.cumulative_starting_bankroll) * 100
            : 0

    return (
        <div className="flex min-h-svh flex-col">
            <AppHeader />
            <main className="mx-auto mt-8 flex w-full max-w-2xl flex-col gap-8 rounded-xl border-2 border-white/25 p-6 pb-16 sm:mt-12 sm:p-10">
                <h1 className="text-3xl font-bold">Your Detailed Statistics:</h1>
                <h2 className="text-lg font-semibold">Basic Statistics:</h2>

                {stats.total_sessions === 0 ? (
                    <p className="text-center text-muted-foreground">
                        No sessions played yet. Start one from the lobby to see your updated stats
                        here!
                    </p>
                ) : (
                    <motion.div
                        className="flex flex-col gap-8"
                        variants={containerVariants}
                        initial="hidden"
                        animate="visible"
                    >
                        <motion.div variants={itemVariants} className="flex flex-col gap-3">
                            <StatCard
                                className="w-full"
                                label="All-Time Winnings:"
                                numericValue={stats.cumulative_bankroll_change}
                                formatValue={(n) => `${n >= 0 ? '+' : ''}${formatCurrency(n)}`}
                                variant={allTimeWinningsVariant}
                                tooltip={STAT_DESCRIPTIONS['All-Time Winnings:']}
                                subtext={`(${allTimeWinningsPct >= 0 ? '+' : ''}${allTimeWinningsPct.toFixed(1)}% vs. starting bankroll)`}
                            />
                            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                                <StatCard
                                    label="Sessions Played:"
                                    numericValue={stats.total_sessions}
                                    formatValue={(n) => `${Math.round(n)}`}
                                    tooltip={STAT_DESCRIPTIONS['Sessions Played:']}
                                />
                                <StatCard
                                    label="Sessions Won:"
                                    numericValue={stats.sessions_won}
                                    formatValue={(n) => `${Math.round(n)}`}
                                    tooltip={STAT_DESCRIPTIONS['Sessions Won:']}
                                />
                                <StatCard
                                    label="Hands Played:"
                                    numericValue={stats.total_hands}
                                    formatValue={(n) => `${Math.round(n)}`}
                                    tooltip={STAT_DESCRIPTIONS['Hands Played:']}
                                />
                                <StatCard
                                    label="Hands Won:"
                                    numericValue={stats.hands_won}
                                    formatValue={(n) => `${Math.round(n)}`}
                                    tooltip={STAT_DESCRIPTIONS['Hands Won:']}
                                />
                                <StatCard
                                    label="Biggest Win:"
                                    value={
                                        stats.biggest_win != null
                                            ? formatCurrency(stats.biggest_win)
                                            : '—'
                                    }
                                    variant={stats.biggest_win != null ? 'good' : 'neutral'}
                                    tooltip={STAT_DESCRIPTIONS['Biggest Win:']}
                                />
                                <StatCard
                                    label="Biggest Loss:"
                                    value={
                                        stats.biggest_loss != null
                                            ? formatCurrency(stats.biggest_loss)
                                            : '—'
                                    }
                                    variant={stats.biggest_loss != null ? 'critical' : 'neutral'}
                                    tooltip={STAT_DESCRIPTIONS['Biggest Loss:']}
                                />
                            </div>
                        </motion.div>

                        <motion.section variants={itemVariants} className="flex flex-col gap-3">
                            <h2 className="text-lg font-semibold">Hand Results:</h2>
                            <WinRateSummary winRate={winRate} translucent />
                        </motion.section>

                        <motion.section variants={itemVariants} className="flex flex-col gap-4">
                            <h2 className="text-lg font-semibold">Play Style:</h2>
                            <p className="text-sm text-muted-foreground">
                                Just to clarify, a green indicator means the stat sits in a
                                generally healthy range, whereas red indicators flag something worth
                                a closer look. Neither is a hard rule, just a signal.
                            </p>
                            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                                <StatRadialGauge
                                    label="VPIP:"
                                    value={stats.vpip_rate}
                                    statKey="vpip"
                                    tooltip={STAT_DESCRIPTIONS.VPIP}
                                />
                                <StatRadialGauge
                                    label="PFR:"
                                    value={stats.pfr_rate}
                                    statKey="pfr"
                                    tooltip={STAT_DESCRIPTIONS.PFR}
                                />
                                <StatRadialGauge
                                    label="3-Bet:"
                                    value={stats.three_bet_rate}
                                    statKey="threeBet"
                                    tooltip={STAT_DESCRIPTIONS['3-Bet:']}
                                />
                                <StatRadialGauge
                                    label="ATS:"
                                    value={stats.ats_rate}
                                    statKey="ats"
                                    tooltip={STAT_DESCRIPTIONS.ATS}
                                />
                            </div>
                            {/* Same 4-column tracks as the row above, so each gauge below
                                can center itself under the row above's column pairs: WTSD
                                spans cols 1-2 (under VPIP/PFR), WWSF spans cols 3-4 (under
                                3-Bet/ATS), and W$SD spans cols 2-3 to land exactly between
                                them. All three share row-start-1 because their column spans
                                deliberately overlap -- without it, grid auto-placement would
                                push the later items to their own row to avoid that overlap.
                                The overlap wrapper is pointer-events-none (with pointer-events-
                                auto restored on the actual gauge) so its mostly-empty 2-column
                                bounding box doesn't sit on top of, and swallow hover for, an
                                earlier sibling's info-icon tooltip trigger underneath it. */}
                            <div className="grid grid-cols-1 gap-2 sm:grid-cols-4">
                                <div className="flex justify-center sm:pointer-events-none sm:col-start-1 sm:row-start-1 sm:col-span-2">
                                    <div className="pointer-events-auto">
                                        <StatRadialGauge
                                            label="WTSD:"
                                            value={stats.wtsd_rate}
                                            statKey="wtsd"
                                            tooltip={STAT_DESCRIPTIONS.WTSD}
                                        />
                                    </div>
                                </div>
                                <div className="flex justify-center sm:pointer-events-none sm:col-start-2 sm:row-start-1 sm:col-span-2">
                                    <div className="pointer-events-auto">
                                        <StatRadialGauge
                                            label="W$SD:"
                                            value={stats.won_at_showdown_rate}
                                            statKey="wonAtShowdown"
                                            tooltip={STAT_DESCRIPTIONS['W$SD']}
                                        />
                                    </div>
                                </div>
                                <div className="flex justify-center sm:pointer-events-none sm:col-start-3 sm:row-start-1 sm:col-span-2">
                                    <div className="pointer-events-auto">
                                        <StatRadialGauge
                                            label="WWSF:"
                                            value={stats.won_when_saw_flop_rate}
                                            statKey="wonWhenSawFlop"
                                            tooltip={STAT_DESCRIPTIONS.WWSF}
                                        />
                                    </div>
                                </div>
                            </div>
                            <StatCard
                                className="w-full"
                                label="Aggression Factor:"
                                value={
                                    stats.aggression_factor != null
                                        ? stats.aggression_factor.toFixed(2)
                                        : '—'
                                }
                                tooltip={STAT_DESCRIPTIONS['Aggression Factor:']}
                            />
                            <PlayStyleRadarChart stats={stats} />
                        </motion.section>

                        <motion.section variants={itemVariants} className="flex flex-col gap-3">
                            <h2 className="text-lg font-semibold">
                                Fold / Aggression Frequency By Street:
                            </h2>
                            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                                {['preflop', 'flop', 'turn', 'river'].map((street) => (
                                    <BorderBeam key={street} {...EDUCATION_BORDER_BEAM_PROPS}>
                                        <div className="flex flex-col gap-1 rounded-lg border border-border bg-transparent p-3 text-sm">
                                            <p className="font-medium capitalize">{street}:</p>
                                            <p className="text-muted-foreground">
                                                Fold:{' '}
                                                {stats.fold_frequency_by_street[street] != null
                                                    ? `${(stats.fold_frequency_by_street[street] * 100).toFixed(0)}%`
                                                    : '—'}
                                            </p>
                                            <p className="text-muted-foreground">
                                                Raise:{' '}
                                                {stats.aggression_frequency_by_street[street] != null
                                                    ? `${(stats.aggression_frequency_by_street[street] * 100).toFixed(0)}%`
                                                    : '—'}
                                            </p>
                                        </div>
                                    </BorderBeam>
                                ))}
                            </div>
                        </motion.section>

                        <motion.section variants={itemVariants} className="flex flex-col gap-3">
                            <h2 className="text-lg font-semibold">Bankroll Over Time:</h2>
                            <p className="text-sm text-muted-foreground">
                                Every session, chronologically recorded. A jump back down is a new
                                session starting at its own bankroll, not a loss.
                            </p>
                            <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS}>
                                <div className="rounded-lg border border-border bg-transparent p-4">
                                    <BankrollGrowthChart
                                        series={computeBankrollSeries(stats.bankroll_history)}
                                        shaded
                                    />
                                </div>
                            </BorderBeam>
                        </motion.section>
                    </motion.div>
                )}
            </main>
        </div>
    )
}

export { StatsPage }
