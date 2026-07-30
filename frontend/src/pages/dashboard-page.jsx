import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { BankrollGrowthChart } from '@/components/dashboard/bankroll-growth-chart'
import { HandHistoryTable } from '@/components/dashboard/hand-history-table'
import { StatTile } from '@/components/dashboard/stat-tile'
import { WinRateSummary } from '@/components/dashboard/win-rate-summary'
import { AppHeader } from '@/components/layout/app-header'
import { useGameSession } from '@/hooks/use-game-session'
import { useHandHistory } from '@/hooks/use-hand-history'
import { computeBankrollSeries } from '@/lib/compute-bankroll-series'
import { computeWinRate } from '@/lib/compute-win-rate'
import { formatCurrency } from '@/lib/format'

const DashboardPage = () => {
    const { sessionId } = useParams()
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
        return (
            <div className="flex min-h-svh flex-col">
                <AppHeader />
                <p className="p-4 text-center text-sm text-destructive">{errorMessage}</p>
            </div>
        )
    }

    if (!session) {
        return (
            <div className="flex min-h-svh flex-col">
                <AppHeader />
                <p className="p-4 text-center text-muted-foreground">Loading...</p>
            </div>
        )
    }

    const winRate = computeWinRate(hands)
    const bankrollSeries = computeBankrollSeries(bankrollLogs)
    const bankrollDelta = session.current_bankroll - session.starting_bankroll

    return (
        <div className="flex min-h-svh flex-col">
            <AppHeader />
            <main className="mx-auto flex w-full max-w-2xl flex-col gap-8 p-4">
                <div className="grid grid-cols-2 gap-3">
                    <StatTile label="Current bankroll" value={formatCurrency(session.current_bankroll)} />
                    <StatTile
                        label="Change from start"
                        value={`${bankrollDelta >= 0 ? '+' : ''}${formatCurrency(bankrollDelta)}`}
                        variant={bankrollDelta > 0 ? 'good' : bankrollDelta < 0 ? 'critical' : 'neutral'}
                    />
                </div>

                <section className="flex flex-col gap-3">
                    <h2 className="text-lg font-semibold">Bankroll growth</h2>
                    <BankrollGrowthChart series={bankrollSeries} startingBankroll={session.starting_bankroll} />
                </section>

                <section className="flex flex-col gap-3">
                    <h2 className="text-lg font-semibold">Win rate</h2>
                    <WinRateSummary winRate={winRate} />
                </section>

                <section className="flex flex-col gap-3">
                    <h2 className="text-lg font-semibold">Hand history</h2>
                    <HandHistoryTable hands={hands} />
                </section>
            </main>
        </div>
    )
}

export { DashboardPage }
