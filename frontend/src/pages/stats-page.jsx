import { useCallback, useEffect, useState } from 'react'

import { StatTile } from '@/components/dashboard/stat-tile'
import { WinRateSummary } from '@/components/dashboard/win-rate-summary'
import { AppHeader } from '@/components/layout/app-header'
import { useUserStats } from '@/hooks/use-user-stats'
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
                            <StatTile label="Hands played" value={stats.total_hands} />
                            <StatTile
                                label="Cumulative change"
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
                    </>
                )}
            </main>
        </div>
    )
}

export { StatsPage }
