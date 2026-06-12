import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { BentoCard, BentoGrid } from '../BentoCard'

describe('BentoCard', () => {
  it('renders with size small', () => {
    render(<BentoCard size="small" data-testid="bento">Content</BentoCard>)
    const el = screen.getByTestId('bento')
    expect(el.className).toContain('aspect-square')
    expect(el.className).toContain('col-span-1')
    expect(el.textContent).toBe('Content')
  })

  it('renders with size wide', () => {
    render(<BentoCard size="wide" data-testid="bento">Content</BentoCard>)
    const el = screen.getByTestId('bento')
    expect(el.className).toContain('aspect-[2/1]')
    expect(el.className).toContain('col-span-2')
  })

  it('renders with size large', () => {
    render(<BentoCard size="large" data-testid="bento">Content</BentoCard>)
    const el = screen.getByTestId('bento')
    expect(el.className).toContain('row-span-2')
    expect(el.className).toContain('col-span-2')
  })

  it('renders with size full', () => {
    render(<BentoCard size="full" data-testid="bento">Content</BentoCard>)
    const el = screen.getByTestId('bento')
    expect(el.className).toContain('col-span-4')
  })

  it('applies aiHighlight glow class', () => {
    render(<BentoCard size="small" aiHighlight data-testid="bento">Content</BentoCard>)
    const el = screen.getByTestId('bento')
    expect(el.className).toContain('animate-pulse-glow')
  })

  it('renders title and badge', () => {
    render(
      <BentoCard size="small" title="待办" badge={<span data-testid="badge">5</span>}>
        Content
      </BentoCard>
    )
    expect(screen.getByText('待办')).toBeInTheDocument()
    expect(screen.getByTestId('badge')).toBeInTheDocument()
  })
})

describe('BentoGrid', () => {
  it('renders children in grid layout', () => {
    render(
      <BentoGrid data-testid="grid">
        <div>Item 1</div>
        <div>Item 2</div>
      </BentoGrid>
    )
    const el = screen.getByTestId('grid')
    expect(el.className).toContain('grid')
    expect(el.className).toContain('grid-cols-2')
    expect(el.children.length).toBe(2)
  })
})
