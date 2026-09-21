import { motion } from 'framer-motion'
import { InfoIcon } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

import { BankrollGrowthChart } from '@/components/dashboard/bankroll-growth-chart'
import { PlayStyleRadarChart } from '@/components/dashboard/play-style-radar-chart'
import { StatRadialGauge } from '@/components/dashboard/stat-radial-gauge'
import { StatTile } from '@/components/dashboard/stat-tile'
import { WinRateSummary } from '@/components/dashboard/win-rate-summary'
import { AppHeader } from '@/components/layout/app-header'
import { AnimatedNumber } from '@/components/ui/animated-number'
import { BorderBeam, EDUCATION_BORDER_BEAM_PROPS } from '@/components/ui/border-beam'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
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

// Matches stat-tile.jsx's own good/critical/neutral tokens -- kept local
// (not reused from StatTile) since the top summary cards need this page's
// translucent BorderBeam look, not StatTile's shared solid-card style
// (still used by the Play Style and Hand Results tiles further down).
const STAT_CARD_VARIANT_CLASSES = {
    good: 'text-green-600',
    critical: 'text-red-600',
    neutral: 'text-foreground',
}

/**
 * `subtext`, when passed, renders inline next to the value (not on its own
 * line) so a card that needs an extra detail -- e.g. All-Time Winnings'
 * percent-of-starting-bankroll -- stays the same height as a plain card.
 */
const StatCard = ({ label, value, numericValue, formatValue, variant = 'neutral', tooltip, subtext, className }) => (
    <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS} className={className}>
        <div className="flex flex-col items-center gap-1 rounded-lg border border-border bg-transparent p-4">
            <div className="flex items-center gap-1">
                <p className="text-sm text-muted-foreground">{label}</p>
                {tooltip && (
                    <Tooltip>
                        <TooltipTrigger
                            aria-label={`What is ${label}?`}
                            className="text-muted-foreground/60 hover:text-muted-foreground"
                        >
                            <InfoIcon className="size-3.5" />
                        </TooltipTrigger>
                        <TooltipContent>{tooltip}</TooltipContent>
                    </Tooltip>
                )}
            </div>
            <p className={`flex items-baseline gap-2 text-xl font-semibold tabular-nums ${STAT_CARD_VARIANT_CLASSES[variant]}`}>
                {numericValue != null && formatValue ? (
                    <AnimatedNumber value={numericValue} format={formatValue} />
                ) : (
                    value
                )}
                {subtext && <span className="text-xs font-normal text-muted-foreground">{subtext}</span>}
            </p>
        </div>
    </BorderBeam>
)

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
        stats.cumulative_bankroll_change > 0 ? 'good' : stats.cumulative_bankroll_change < 0 ? 'critical' : 'neutral'
    const allTimeWinningsPct =
        stats.cumulative_starting_bankroll > 0
            ? (stats.cumulative_bankroll_change / stats.cumulative_starting_bankroll) * 100
            : 0

    return (
        <div className="flex min-h-svh flex-col">
            <AppHeader />
            <main className="mx-auto flex w-full max-w-2xl flex-col gap-8 p-4">
                <h1 className="text-xl font-semibold">Basic Statistics:</h1>

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
                            <WinRateSummary winRate={winRate} />
                        </motion.section>

                        <motion.section variants={itemVariants} className="flex flex-col gap-4">
                            <h2 className="text-lg font-semibold">Play style</h2>
                            <p className="text-sm text-muted-foreground">
                                Green means the stat sits in a generally healthy range; red flags
                                something worth a closer look -- neither is a hard rule, just a
                                signal.
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
                                    tooltip={STAT_DESCRIPTIONS['3-Bet:']}
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
                                    value={
                                        stats.aggression_factor != null
                                            ? stats.aggression_factor.toFixed(2)
                                            : '—'
                                    }
                                    tooltip={STAT_DESCRIPTIONS['Aggression Factor:']}
                                />
                            </div>
                            <PlayStyleRadarChart stats={stats} />
                        </motion.section>

                        <motion.section variants={itemVariants} className="flex flex-col gap-3">
                            <h2 className="text-lg font-semibold">
                                Fold / aggression frequency by street
                            </h2>
                            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                                {['preflop', 'flop', 'turn', 'river'].map((street) => (
                                    <div
                                        key={street}
                                        className="flex flex-col gap-1 rounded-lg border p-3 text-sm"
                                    >
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
                                Every session, chronologically -- a jump back down is a new session
                                starting at its own bankroll, not a loss.
                            </p>
                            <BankrollGrowthChart
                                series={computeBankrollSeries(stats.bankroll_history)}
                            />
                        </motion.section>
                    </motion.div>
                )}
            </main>
        </div>
    )
}

export { StatsPage }
