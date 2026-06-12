import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Skeleton, SkeletonCard, SkeletonTable, SkeletonShimmerCard, SkeletonShimmerList, SkeletonShimmerBento } from '../Skeleton'

describe('Skeleton', () => {
  it('renders with default classes', () => {
    render(<Skeleton data-testid="sk" />)
    const el = screen.getByTestId('sk')
    expect(el.className).toContain('animate-pulse')
    expect(el.className).toContain('bg-muted')
    expect(el.className).toContain('rounded-md')
  })

  it('merges custom className', () => {
    render(<Skeleton data-testid="sk" className="h-24 w-48" />)
    const el = screen.getByTestId('sk')
    expect(el.className).toContain('h-24')
    expect(el.className).toContain('w-48')
  })
})

describe('SkeletonCard', () => {
  it('renders header and default 3 rows', () => {
    render(<SkeletonCard data-testid="card" />)
    const card = screen.getByTestId('card')
    expect(card.querySelectorAll('.animate-pulse').length).toBe(4) // 1 header + 3 rows
  })

  it('renders custom row count', () => {
    render(<SkeletonCard data-testid="card" rows={5} />)
    const card = screen.getByTestId('card')
    expect(card.querySelectorAll('.animate-pulse').length).toBe(6) // 1 header + 5 rows
  })
})

describe('SkeletonTable', () => {
  it('renders header and rows', () => {
    render(<SkeletonTable rows={2} cols={3} />)
    const pulses = document.querySelectorAll('.animate-pulse')
    expect(pulses.length).toBe(9) // (1 header + 2 rows) * 3 cols
  })
})

describe('Skeleton shimmer variant', () => {
  it('renders shimmer class', () => {
    render(<Skeleton data-testid="sk" variant="shimmer" />)
    const el = screen.getByTestId('sk')
    expect(el.className).toContain('animate-shimmer')
  })

  it('defaults to pulse', () => {
    render(<Skeleton data-testid="sk" />)
    const el = screen.getByTestId('sk')
    expect(el.className).toContain('animate-pulse')
  })
})

describe('SkeletonShimmerCard', () => {
  it('renders shimmer skeletons', () => {
    render(<SkeletonShimmerCard data-testid="card" />)
    const card = screen.getByTestId('card')
    const shimmers = card.querySelectorAll('.animate-shimmer')
    expect(shimmers.length).toBeGreaterThan(0)
  })
})

describe('SkeletonShimmerList', () => {
  it('renders default 4 items', () => {
    render(<SkeletonShimmerList data-testid="list" />)
    const list = screen.getByTestId('list')
    const shimmers = list.querySelectorAll('.animate-shimmer')
    expect(shimmers.length).toBeGreaterThan(0)
  })

  it('renders custom item count', () => {
    render(<SkeletonShimmerList data-testid="list" items={2} />)
    const list = screen.getByTestId('list')
    const shimmers = list.querySelectorAll('.animate-shimmer')
    expect(shimmers.length).toBeGreaterThan(0)
  })
})

describe('SkeletonShimmerBento', () => {
  it('renders bento grid skeletons', () => {
    render(<SkeletonShimmerBento data-testid="bento" />)
    const bento = screen.getByTestId('bento')
    const shimmers = bento.querySelectorAll('.animate-shimmer')
    expect(shimmers.length).toBeGreaterThan(0)
    expect(bento.querySelector('.grid')).toBeInTheDocument()
  })
})
