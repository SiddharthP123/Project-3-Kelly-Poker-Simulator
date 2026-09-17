/**
 * Flowing rainbow gradient text -- adapted from the 21st.dev "Text
 * Gradient" bookmark's own description (background-clip:text with an
 * animated, oversized background so the colors visibly travel through
 * the letters, not just a static multi-color fill) since the bookmark's
 * exact source was locked behind this session's daily retrieval quota.
 * The moving keyframe itself lives in index.css (see rainbow-text-flow)
 * since background-position can't be expressed as a Tailwind utility.
 */
const RainbowText = ({ children, className = '' }) => (
    <span
        className={`inline-block bg-clip-text text-transparent ${className}`}
        style={{
            backgroundImage:
                'linear-gradient(90deg, #ff5f6d, #ffc371, #4ade80, #38bdf8, #a78bfa, #ff5f6d)',
            backgroundSize: '200% auto',
            animation: 'rainbow-text-flow 4s linear infinite',
        }}
    >
        {children}
    </span>
)

export { RainbowText }
