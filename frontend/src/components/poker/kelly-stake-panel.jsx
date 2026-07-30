import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatPercent } from '@/lib/format'

const KellyStakePanel = ({ equity, kellyRecommendedStake, potSize, betToCall, bankroll }) => {
    const kellyPercentOfBankroll = bankroll > 0 ? kellyRecommendedStake / bankroll : 0

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-base">Your equity &amp; Kelly-recommended sizing</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <p className="text-muted-foreground">Pot</p>
                    <p className="font-semibold">{formatCurrency(potSize)}</p>
                </div>
                <div>
                    <p className="text-muted-foreground">Facing bet</p>
                    <p className="font-semibold">{formatCurrency(betToCall)}</p>
                </div>
                <div>
                    <p className="text-muted-foreground">Your equity</p>
                    <p className="font-semibold">{formatPercent(equity)}</p>
                </div>
                <div>
                    <p className="text-muted-foreground">Kelly-recommended stake</p>
                    <p className="font-semibold">
                        {formatCurrency(kellyRecommendedStake)} ({formatPercent(kellyPercentOfBankroll)} of
                        bankroll)
                    </p>
                </div>
            </CardContent>
        </Card>
    )
}

export { KellyStakePanel }
