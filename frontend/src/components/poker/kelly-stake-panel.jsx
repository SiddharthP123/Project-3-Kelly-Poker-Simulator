import { formatCurrency, formatPercent } from '@/lib/format'

/**
 * equity/kellyRecommendedStake come straight from the backend's live
 * per-decision fields (HandResponse.equity_at_decision/
 * kelly_recommended_stake) -- kellyRecommendedStake is null whenever
 * hero can check for free (nothing to call), since Kelly sizing needs a
 * real bet size to anchor to (see backend/services/game_engine.py's
 * _compute_hero_kelly_info). No border/background of its own -- it's one
 * section of the single merged card poker-table.jsx renders on the right
 * (Your hand/Kelly sizing/Action controls used to each be their own
 * separate card; now they're stacked sections inside one, divided by
 * poker-table.jsx's own border-t separators).
 */
const KellyStakePanel = ({ equity, kellyRecommendedStake, potSize, callAmount, bankroll }) => {
    const kellyPercentOfBankroll = bankroll > 0 && kellyRecommendedStake != null ? kellyRecommendedStake / bankroll : 0

    return (
        <div className="flex w-full flex-col gap-2 text-white">
            <p className="text-sm font-medium text-white/70">Your Equity and Kelly-Recommended Sizing:</p>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                    <p className="text-white/50">Pot:</p>
                    <p className="font-semibold">{formatCurrency(potSize)}</p>
                </div>
                <div>
                    <p className="text-white/50">Facing Bet:</p>
                    <p className="font-semibold">{callAmount > 0 ? formatCurrency(callAmount) : 'Free to check'}</p>
                </div>
                <div>
                    <p className="text-white/50">Your Equity:</p>
                    <p className="font-semibold">{formatPercent(equity)}</p>
                </div>
                <div>
                    <p className="text-white/50">Kelly-Recommended Stake:</p>
                    <p className="font-semibold">
                        {kellyRecommendedStake != null
                            ? `${formatCurrency(kellyRecommendedStake)} (${formatPercent(kellyPercentOfBankroll)} of bankroll)`
                            : '—'}
                    </p>
                </div>
            </div>
        </div>
    )
}

export { KellyStakePanel }
