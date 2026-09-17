import '@testing-library/jest-dom/vitest'

// jsdom doesn't implement matchMedia at all -- needed by border-beam's
// theme="auto" (which reads prefers-color-scheme) so it doesn't throw the
// moment any component using it mounts under a test.
window.matchMedia =
    window.matchMedia ||
    ((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
    }))
