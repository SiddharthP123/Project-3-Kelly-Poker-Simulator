import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/context/auth-context'
import { KellyCriterionPage } from '@/pages/kelly-criterion-page'

describe('KellyCriterionPage', () => {
    beforeEach(() => {
        localStorage.clear()
        global.fetch = vi.fn().mockResolvedValue({
            ok: false, status: 401, headers: { get: () => null }, json: async () => null,
        })
    })

    it('renders without requiring a logged-in user', () => {
        render(
            <MemoryRouter>
                <AuthProvider>
                    <KellyCriterionPage />
                </AuthProvider>
            </MemoryRouter>,
        )

        expect(screen.getByRole('heading', { name: /the kelly criterion/i })).toBeInTheDocument()
    })

    it('covers the formula, both worked examples, the growth diagram, and a glossary', () => {
        render(
            <MemoryRouter>
                <AuthProvider>
                    <KellyCriterionPage />
                </AuthProvider>
            </MemoryRouter>,
        )

        expect(screen.getByText('f* = (bp − q) / b')).toBeInTheDocument()
        expect(screen.getByText(/f\* = \(1 × 0\.6 − 0\.4\) \/ 1 = 0\.2/)).toBeInTheDocument()
        expect(screen.getByText(/f\* = \(2 × 0\.6 − 0\.4\) \/ 2 = 0\.8 \/ 2 = 0\.4/)).toBeInTheDocument()
        expect(screen.getByText('Kelly-Optimal:')).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /beyond poker/i })).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /glossary/i })).toBeInTheDocument()
        expect(screen.getByText('Risk Of Ruin:')).toBeInTheDocument()
    })
})
