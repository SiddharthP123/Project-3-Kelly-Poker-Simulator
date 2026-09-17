import { motion } from 'framer-motion'
import { useCallback, useEffect, useState } from 'react'

import { BankrollGrowthChart } from '@/components/dashboard/bankroll-growth-chart'
import { PlayStyleRadarChart } from '@/components/dashboard/play-style-radar-chart'
import { StatRadialGauge } from '@/components/dashboard/stat-radial-gauge'
import { StatTile } from '@/components/dashboard/stat-tile'
import { WinRateSummary } from '@/components/dashboard/win-rate-summary'
import { AppHeader } from '@/components/layout/app-header'
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
            setErrorMessage(error.detail || 'Could not load your stats')
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

    return (
        <div className="flex min-h-svh flex-col">
            <AppHeader />
            <main className="mx-auto flex w-full max-w-2xl flex-col gap-8 p-4">
                <h1 className="text-xl font-semibold">Your stats</h1>

                {stats.total_sessions === 0 ? (
                    <p className="text-center text-muted-foreground">
                        No sessions played yet -- start one from the lobby to see your stats here.
                    </p>
                ) : (
                    <motion.div
                        className="flex flex-col gap-8"
                        variants={containerVariants}
                        initial="hidden"
                        animate="visible"
                    >
                        <motion.div variants={itemVariants} className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                            <StatTile
                                label="Sessions played"
                                numericValue={stats.total_sessions}
                                formatValue={(n) => `${Math.round(n)}`}
                                tooltip={STAT_DESCRIPTIONS['Sessions played']}
                            />
                            <StatTile
                                label="Sessions won"
                                numericValue={stats.sessions_won}
                                formatValue={(n) => `${Math.round(n)}`}
                                tooltip={STAT_DESCRIPTIONS['Sessions won']}
                            />
                            <StatTile
                                label="Hands played"
                                numericValue={stats.total_hands}
                                formatValue={(n) => `${Math.round(n)}`}
                                tooltip={STAT_DESCRIPTIONS['Hands played']}
                            />
                            <StatTile
                                label="Hands won"
                                numericValue={stats.hands_won}
                                formatValue={(n) => `${Math.round(n)}`}
                                tooltip={STAT_DESCRIPTIONS['Hands won']}
                            />
                            <StatTile
                                label="All-time winnings"
                                numericValue={stats.cumulative_bankroll_change}
                                formatValue={(n) => `${n >= 0 ? '+' : ''}${formatCurrency(n)}`}
                                variant={
                                    stats.cumulative_bankroll_change > 0
                                        ? 'good'
                                        : stats.cumulative_bankroll_change < 0
                                          ? 'critical'
                                          : 'neutral'
                                }
                                tooltip={STAT_DESCRIPTIONS['All-time winnings']}
                            />
                            <StatTile
                                label="Biggest win"
                                value={stats.biggest_win != null ? formatCurrency(stats.biggest_win) : '—'}
                                variant={stats.biggest_win != null ? 'good' : 'neutral'}
                                tooltip={STAT_DESCRIPTIONS['Biggest win']}
                            />
                            <StatTile
                                label="Biggest loss"
                                value={stats.biggest_loss != null ? formatCurrency(stats.biggest_loss) : '—'}
                                variant={stats.biggest_loss != null ? 'critical' : 'neutral'}
                                tooltip={STAT_DESCRIPTIONS['Biggest loss']}
                            />
                        </motion.div>

                        <motion.section variants={itemVariants} className="flex flex-col gap-3">
                            <h2 className="text-lg font-semibold">Win rate</h2>
                            <WinRateSummary winRate={winRate} />
                        </motion.section>

                        <motion.section variants={itemVariants} className="flex flex-col gap-4">
                            <h2 className="text-lg font-semibold">Play style</h2>
                            <p className="text-sm text-muted-foreground">
                                Green means the stat sits in a generally healthy range; red flags something worth
                                a closer look -- neither is a hard rule, just a signal.
                            </p>
                            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                                <StatRadialGauge
                                    label="VPIP"
                                    value={stats.vpip_rate}
                                    statKey="vpip"
                                    tooltip={STAT_DESCRIPTIONS.VPIP}
                                />
                                <StatRadialGauge
                                    label="PFR"
                                    value={stats.pfr_rate}
                                    statKey="pfr"
                                    tooltip={STAT_DESCRIPTIONS.PFR}
                                />
                                <StatRadialGauge
                                    label="3-bet"
                                    value={stats.three_bet_rate}
                                    statKey="threeBet"
                                    tooltip={STAT_DESCRIPTIONS['3-bet']}
                                />
                                <StatRadialGauge
                                    label="ATS"
                                    value={stats.ats_rate}
                                    statKey="ats"
                                    tooltip={STAT_DESCRIPTIONS.ATS}
                                />
                                <StatRadialGauge
                                    label="WTSD"
                                    value={stats.wtsd_rate}
                                    statKey="wtsd"
                                    tooltip={STAT_DESCRIPTIONS.WTSD}
                                />
                                <StatRadialGauge
                                    label="W$SD"
                                    value={stats.won_at_showdown_rate}
                                    statKey="wonAtShowdown"
                                    tooltip={STAT_DESCRIPTIONS['W$SD']}
                                />
                                <StatRadialGauge
                                    label="WWSF"
                                    value={stats.won_when_saw_flop_rate}
                                    statKey="wonWhenSawFlop"
                                    tooltip={STAT_DESCRIPTIONS.WWSF}
                                />
                                <StatTile
                                    label="Aggression factor"
                                    value={stats.aggression_factor != null ? stats.aggression_factor.toFixed(2) : '—'}
                                    tooltip={STAT_DESCRIPTIONS['Aggression factor']}
                                />
                            </div>
                            <PlayStyleRadarChart stats={stats} />
                        </motion.section>

                        <motion.section variants={itemVariants} className="flex flex-col gap-3">
                            <h2 className="text-lg font-semibold">Fold / aggression frequency by street</h2>
                            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                                {['preflop', 'flop', 'turn', 'river'].map((street) => (
                                    <div key={street} className="flex flex-col gap-1 rounded-lg border p-3 text-sm">
                                        <p className="font-medium capitalize">{street}</p>
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
                                ))}
                            </div>
                        </motion.section>

                        <motion.section variants={itemVariants} className="flex flex-col gap-3">
                            <h2 className="text-lg font-semibold">Bankroll over time</h2>
                            <p className="text-sm text-muted-foreground">
                                Every session, chronologically -- a jump back down is a new session starting at its
                                own bankroll, not a loss.
                            </p>
                            <BankrollGrowthChart series={computeBankrollSeries(stats.bankroll_history)} />
                        </motion.section>
                    </motion.div>
                )}
            </main>
        </div>
    )
}

export { StatsPage }
