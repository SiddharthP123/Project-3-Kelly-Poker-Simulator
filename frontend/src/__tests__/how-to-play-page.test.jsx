import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/context/auth-context'
import { HowToPlayPage } from '@/pages/how-to-play-page'

describe('HowToPlayPage', () => {
    beforeEach(() => {
        localStorage.clear()
        // No token stored -- renders exactly as an unauthenticated, first-time
        // visitor would see it (this page needs no login).
        global.fetch = vi.fn().mockResolvedValue({
            ok: false, status: 401, headers: { get: () => null }, json: async () => null,
        })
    })

    it('renders without requiring a logged-in user', () => {
        render(
            <MemoryRouter>
                <AuthProvider>
                    <HowToPlayPage />
                </AuthProvider>
            </MemoryRouter>,
        )

        expect(screen.getByRole('heading', { name: /beginner's guide/i })).toBeInTheDocument()
    })

    it('covers hands, streets, actions, showdown, and a glossary', () => {
        render(
            <MemoryRouter>
                <AuthProvider>
                    <HowToPlayPage />
                </AuthProvider>
            </MemoryRouter>,
        )

        expect(screen.getByRole('heading', { name: /your hand/i })).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /the four stages/i })).toBeInTheDocument()
        expect(screen.getByText(/checking, calling, folding, and raising/i)).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /showdown/i })).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /common tactics/i })).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: /glossary/i })).toBeInTheDocument()
        expect(screen.getByText('Equity:')).toBeInTheDocument()
        expect(screen.getByText('All-In:')).toBeInTheDocument()
    })

    it('illustrates all 10 hand rankings, worst to best', () => {
        render(
            <MemoryRouter>
                <AuthProvider>
                    <HowToPlayPage />
                </AuthProvider>
            </MemoryRouter>,
        )

        expect(screen.getByRole('heading', { name: /hand rankings/i })).toBeInTheDocument()
        ;[
            'High Card:',
            'Pair:',
            'Two Pair:',
            'Three of a Kind',
            'Straight:',
            'Flush:',
            'Full House:',
            'Four of a Kind',
            'Straight Flush:',
            'Royal Flush',
        ].forEach((handName) => {
            expect(screen.getByText(handName)).toBeInTheDocument()
        })
    })

    it('illustrates the board building up across all 4 streets', () => {
        render(
            <MemoryRouter>
                <AuthProvider>
                    <HowToPlayPage />
                </AuthProvider>
            </MemoryRouter>,
        )

        ;['Preflop:', 'Flop:', 'Turn:', 'River'].forEach((streetName) => {
            expect(screen.getByText(streetName)).toBeInTheDocument()
        })
    })

    it('renders the 169-cell starting hand strength matrix', () => {
        render(
            <MemoryRouter>
                <AuthProvider>
                    <HowToPlayPage />
                </AuthProvider>
            </MemoryRouter>,
        )

        expect(screen.getByRole('heading', { name: /starting hand strength/i })).toBeInTheDocument()
        expect(screen.getAllByTitle('AA')).toHaveLength(1)
        expect(screen.getAllByTitle('72o')).toHaveLength(1)
        expect(screen.getAllByTitle('AKs')).toHaveLength(1)
    })
})
