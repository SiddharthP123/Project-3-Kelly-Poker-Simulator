import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AnimatedCard } from '@/components/poker/animated-card'

describe('AnimatedCard', () => {
    it('renders nothing when not yet dealt', () => {
        const { container } = render(<AnimatedCard dealt={false} card={null} />)
        expect(container).toBeEmptyDOMElement()
    })

    it('renders a face-down placeholder when dealt but hidden (card is null)', () => {
        render(<AnimatedCard dealt card={null} />)
        // The card-back marker is always present; no rank/suit text exists yet.
        expect(screen.queryByText('A')).not.toBeInTheDocument()
        expect(screen.queryByText('♥')).not.toBeInTheDocument()
    })

    it('renders the real rank and suit once dealt with a known card', () => {
        render(<AnimatedCard dealt card="Ah" />)
        expect(screen.getByText('A')).toBeInTheDocument()
        expect(screen.getByText('♥')).toBeInTheDocument()
    })

    it('renders black suit glyphs for clubs/spades, not red', () => {
        render(<AnimatedCard dealt card="Ks" />)
        const suitGlyph = screen.getByText('♠')
        expect(suitGlyph.parentElement.className).not.toContain('text-red-600')
    })

    it('renders red suit glyphs for hearts/diamonds', () => {
        render(<AnimatedCard dealt card="Kd" />)
        const suitGlyph = screen.getByText('♦')
        expect(suitGlyph.parentElement.className).toContain('text-red-600')
    })
})
