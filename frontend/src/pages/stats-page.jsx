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
                    <>
                        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                            <StatTile label="Sessions played" value={stats.total_sessions} />
                            <StatTile label="Sessions won" value={stats.sessions_won} />
                            <StatTile label="Hands played" value={stats.total_hands} />
                            <StatTile label="Hands won" value={stats.hands_won} />
                            <StatTile
                                label="All-time winnings"
                                value={`${stats.cumulative_bankroll_change >= 0 ? '+' : ''}${formatCurrency(
                                    stats.cumulative_bankroll_change,
                                )}`}
                                variant={
                                    stats.cumulative_bankroll_change > 0
                                        ? 'good'
                                        : stats.cumulative_bankroll_change < 0
                                          ? 'critical'
                                          : 'neutral'
                                }
                            />
                            <StatTile
                                label="Biggest win"
                                value={stats.biggest_win != null ? formatCurrency(stats.biggest_win) : '—'}
                                variant={stats.biggest_win != null ? 'good' : 'neutral'}
                            />
                            <StatTile
                                label="Biggest loss"
                                value={stats.biggest_loss != null ? formatCurrency(stats.biggest_loss) : '—'}
                                variant={stats.biggest_loss != null ? 'critical' : 'neutral'}
                            />
                        </div>

                        <section className="flex flex-col gap-3">
                            <h2 className="text-lg font-semibold">Win rate</h2>
                            <WinRateSummary winRate={winRate} />
                        </section>

                        <section className="flex flex-col gap-4">
                            <h2 className="text-lg font-semibold">Play style</h2>
                            <p className="text-sm text-muted-foreground">
                                Green means the stat sits in a generally healthy range; red flags something worth
                                a closer look -- neither is a hard rule, just a signal.
                            </p>
                            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                                <StatRadialGauge label="VPIP" value={stats.vpip_rate} statKey="vpip" />
                                <StatRadialGauge label="PFR" value={stats.pfr_rate} statKey="pfr" />
                                <StatRadialGauge label="3-bet" value={stats.three_bet_rate} statKey="threeBet" />
                                <StatRadialGauge label="ATS" value={stats.ats_rate} statKey="ats" />
                                <StatRadialGauge label="WTSD" value={stats.wtsd_rate} statKey="wtsd" />
                                <StatRadialGauge
                                    label="W$SD"
                                    value={stats.won_at_showdown_rate}
                                    statKey="wonAtShowdown"
                                />
                                <StatRadialGauge
                                    label="WWSF"
                                    value={stats.won_when_saw_flop_rate}
                                    statKey="wonWhenSawFlop"
                                />
                                <StatTile
                                    label="Aggression factor"
                                    value={stats.aggression_factor != null ? stats.aggression_factor.toFixed(2) : '—'}
                                />
                            </div>
                            <PlayStyleRadarChart stats={stats} />
                        </section>

                        <section className="flex flex-col gap-3">
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
                        </section>

                        <section className="flex flex-col gap-3">
                            <h2 className="text-lg font-semibold">Bankroll over time</h2>
                            <p className="text-sm text-muted-foreground">
                                Every session, chronologically -- a jump back down is a new session starting at its
                                own bankroll, not a loss.
                            </p>
                            <BankrollGrowthChart series={computeBankrollSeries(stats.bankroll_history)} />
                        </section>
                    </>
                )}
            </main>
        </div>
    )
}

export { StatsPage }
