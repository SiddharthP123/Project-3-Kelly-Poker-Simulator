import { motion } from 'framer-motion'
import { useCallback, useEffect, useState } from 'react'

import { BankrollGrowthChart } from '@/components/dashboard/bankroll-growth-chart'
import { HandHistoryTable } from '@/components/dashboard/hand-history-table'
import { StatCard } from '@/components/dashboard/stat-card'
import { WinRateSummary } from '@/components/dashboard/win-rate-summary'
import { BorderBeam, EDUCATION_BORDER_BEAM_PROPS } from '@/components/ui/border-beam'
import { useGameSession } from '@/hooks/use-game-session'
import { useHandHistory } from '@/hooks/use-hand-history'
import { computeBankrollSeries } from '@/lib/compute-bankroll-series'
import { computeWinRate } from '@/lib/compute-win-rate'
import { formatCurrency } from '@/lib/format'

// Mirrors the 21st.dev "Marketing Dashboard" bookmark's container/item
// pattern: sections fade + rise in one after another instead of all
// popping in at once, so the page reads as composed rather than dumped.
const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.12 } },
}
const itemVariants = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
}

/**
 * The actual dashboard content (stat tiles, bankroll chart, win rate,
 * hand history) with no page chrome of its own -- shared between the
 * standalone dashboard-page.jsx route and the in-game DashboardDrawer, so
 * both stay in sync with a single implementation instead of two copies
 * that can drift.
 */
const SessionDashboardPanel = ({ sessionId }) => {
    const { getSession } = useGameSession()
    const { getHandHistory, getBankrollHistory } = useHandHistory()

    const [session, setSession] = useState(null)
    const [hands, setHands] = useState([])
    const [bankrollLogs, setBankrollLogs] = useState([])
    const [errorMessage, setErrorMessage] = useState('')

    const loadDashboard = useCallback(async () => {
        try {
            const [sessionData, handsData, bankrollData] = await Promise.all([
                getSession(sessionId),
                getHandHistory(sessionId),
                getBankrollHistory(sessionId),
            ])
            setSession(sessionData)
            setHands(handsData)
            setBankrollLogs(bankrollData)
        } catch (error) {
            setErrorMessage(error.detail || 'Could not load the dashboard')
        }
    }, [getBankrollHistory, getHandHistory, getSession, sessionId])

    useEffect(() => {
        loadDashboard()
    }, [loadDashboard])

    if (errorMessage) {
        return <p className="p-4 text-center text-sm text-destructive">{errorMessage}</p>
    }

    if (!session) {
        return <p className="p-4 text-center text-muted-foreground">Loading...</p>
    }

    const winRate = computeWinRate(hands)
    const bankrollSeries = computeBankrollSeries(bankrollLogs)
    const bankrollDelta = session.current_bankroll - session.starting_bankroll

    return (
        <motion.div
            className="flex w-full flex-col gap-8"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
        >
            <motion.div variants={itemVariants} className="grid grid-cols-2 gap-3">
                <StatCard
                    label="Current Bankroll:"
                    numericValue={session.current_bankroll}
                    formatValue={formatCurrency}
                />
                <StatCard
                    label="Change From Start:"
                    numericValue={bankrollDelta}
                    formatValue={(n) => `${n >= 0 ? '+' : ''}${formatCurrency(n)}`}
                    variant={bankrollDelta > 0 ? 'good' : bankrollDelta < 0 ? 'critical' : 'neutral'}
                />
            </motion.div>

            <motion.section variants={itemVariants} className="flex flex-col gap-3">
                <h2 className="text-lg font-semibold">Bankroll Growth:</h2>
                <BorderBeam {...EDUCATION_BORDER_BEAM_PROPS}>
                    <div className="rounded-lg border border-border bg-transparent p-4">
                        <BankrollGrowthChart
                            series={bankrollSeries}
                            startingBankroll={session.starting_bankroll}
                            shaded
                        />
                    </div>
                </BorderBeam>
            </motion.section>

            <motion.section variants={itemVariants} className="flex flex-col gap-3">
                <h2 className="text-lg font-semibold">Win Rate:</h2>
                <WinRateSummary winRate={winRate} translucent />
            </motion.section>

            <motion.section variants={itemVariants} className="flex flex-col gap-3">
                <h2 className="text-lg font-semibold">Hand History:</h2>
                <HandHistoryTable hands={hands} />
            </motion.section>
        </motion.div>
    )
}

export { SessionDashboardPanel }
