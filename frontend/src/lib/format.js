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

export { formatCurrency, formatPercent }
