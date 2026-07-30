import { Card, CardContent } from '@/components/ui/card'

// Status-meaning tokens, not the generic categorical ramp -- these
// colors mean "good/bad/neutral", so they must never share a chart with
// plain arbitrary category hues.
const VARIANT_CLASSES = {
    good: 'text-green-600',
    critical: 'text-red-600',
    warning: 'text-amber-600',
    neutral: 'text-foreground',
}

const StatTile = ({ label, value, variant = 'neutral' }) => (
    <Card>
        <CardContent className="flex flex-col items-center gap-1 py-4">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className={`text-xl font-semibold ${VARIANT_CLASSES[variant]}`}>{value}</p>
        </CardContent>
    </Card>
)

export { StatTile }
