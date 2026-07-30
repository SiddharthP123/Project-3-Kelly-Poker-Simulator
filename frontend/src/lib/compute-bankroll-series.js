/**
 * Converts BankrollLog rows (already ordered by logged_at) into
 * chart-ready points. Kept as a separate pure function so the chart
 * component only ever receives data already shaped the way it needs it.
 *
 * @param {Array<{bankroll_after: number, logged_at: string}>} bankrollLogs
 * @returns {Array<{index: number, bankroll: number, loggedAt: string}>}
 */
const computeBankrollSeries = (bankrollLogs) =>
    bankrollLogs.map((log, index) => ({
        index,
        bankroll: log.bankroll_after,
        loggedAt: log.logged_at,
    }))

export { computeBankrollSeries }
