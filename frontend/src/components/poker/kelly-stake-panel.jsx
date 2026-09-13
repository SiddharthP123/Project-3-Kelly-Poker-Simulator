import { formatCurrency, formatPercent } from '@/lib/format'

/**
 * equity/kellyRecommendedStake come straight from the backend's live
 * per-decision fields (HandResponse.equity_at_decision/
 * kelly_recommended_stake) -- kellyRecommendedStake is null whenever
 * hero can check for free (nothing to call), since Kelly sizing needs a
 * real bet size to anchor to (see backend/services/game_engine.py's
 * _compute_hero_kelly_info). Styled dark/white to match the rest of the
 * game screen (ActionControls, the felt table) rather than the app's
 * default theme-dependent Card, since this only ever sits inside the
 * always-dark poker table screen.
 */
const KellyStakePanel = ({ equity, kellyRecommendedStake, potSize, callAmount, bankroll }) => {
    const kellyPercentOfBankroll = bankroll > 0 && kellyRecommendedStake != null ? kellyRecommendedStake / bankroll : 0

    return (
        <div className="flex w-full max-w-md flex-col gap-2 rounded-lg border border-white/15 bg-black/60 p-4 text-white">
            <p className="text-sm font-medium text-white/70">Your equity &amp; Kelly-recommended sizing</p>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                    <p className="text-white/50">Pot</p>
                    <p className="font-semibold">{formatCurrency(potSize)}</p>
                </div>
                <div>
                    <p className="text-white/50">Facing bet</p>
                    <p className="font-semibold">{callAmount > 0 ? formatCurrency(callAmount) : 'Free to check'}</p>
                </div>
                <div>
                    <p className="text-white/50">Your equity</p>
                    <p className="font-semibold">{formatPercent(equity)}</p>
                </div>
                <div>
                    <p className="text-white/50">Kelly-recommended stake</p>
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
