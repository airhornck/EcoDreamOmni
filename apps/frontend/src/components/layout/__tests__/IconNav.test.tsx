import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { IconNav } from '../IconNav'

describe('IconNav', () => {
  it('renders all navigation items as links', () => {
    render(
      <MemoryRouter>
        <IconNav />
      </MemoryRouter>
    )

    const links = screen.getAllByRole('link')
    expect(links.length).toBeGreaterThanOrEqual(9)
  })

  it('highlights active route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <IconNav />
      </MemoryRouter>
    )

    // Active link should have text-primary styling
    const activeLink = screen.getAllByRole('link').find((link) =>
      link.className.includes('text-primary')
    )
    expect(activeLink).toBeDefined()
  })

  it('has fixed width of 48px (w-12)', () => {
    const { container } = render(
      <MemoryRouter>
        <IconNav />
      </MemoryRouter>
    )

    const nav = container.querySelector('nav')
    expect(nav).toHaveClass('w-12')
  })
})
