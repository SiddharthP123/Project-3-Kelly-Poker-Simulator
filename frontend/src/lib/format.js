/**
 * Formats a number of dollars as a currency string.
 * @param {number} amount
 * @returns {string} e.g. '$1,250.00'
 */
const formatCurrency = (amount) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)

/**
 * Formats a 0-1 fraction as a percentage string.
 * @param {number} fraction
 * @param {number} [decimals=1]
 * @returns {string} e.g. '54.0%'
 */
const formatPercent = (fraction, decimals = 1) => `${(fraction * 100).toFixed(decimals)}%`

/**
 * Turns a persona key (e.g. 'very-tight-aggressive') into a display label
 * ('Very-Tight-Aggressive') -- matches poker/bots.py's own persona names
 * exactly, just derived from the key instead of duplicating a lookup
 * table that would drift from the backend's PERSONA_REGISTRY over time.
 * @param {string} personaKey
 * @returns {string}
 */
const formatPersonaLabel = (personaKey) =>
    personaKey
        .split('-')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join('-')

export { formatCurrency, formatPercent, formatPersonaLabel }
