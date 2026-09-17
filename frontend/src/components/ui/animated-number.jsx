import { animate, useMotionValue } from 'framer-motion'
import { useEffect, useState } from 'react'

/**
 * Counts up from 0 to `value` on every value change (not just on mount)
 * -- adapted from the 21st.dev "Marketing Dashboard" bookmark's
 * AnimatedNumber, generalized with a `format` fn so callers can render
 * currency/percent/plain numbers through the same animated span instead
 * of duplicating the tween per stat type.
 */
const AnimatedNumber = ({ value, format = (n) => `${Math.round(n)}`, duration = 1.2 }) => {
    const motionValue = useMotionValue(0)
    const [display, setDisplay] = useState(() => format(0))

    // `format` deliberately excluded from deps -- callers typically pass an
    // inline arrow (a new reference every render), and re-running the tween
    // on every parent re-render (instead of only on a real value change)
    // would restart the count-up mid-animation for no reason.
    useEffect(() => {
        const controls = animate(motionValue, value, {
            duration,
            ease: 'easeOut',
            onUpdate: (latest) => setDisplay(format(latest)),
        })
        return controls.stop
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [value, duration, motionValue])

    return <span>{display}</span>
}

export { AnimatedNumber }
