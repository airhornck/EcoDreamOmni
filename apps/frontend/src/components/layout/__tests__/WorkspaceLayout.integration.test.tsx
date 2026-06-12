import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { WorkspaceLayout } from '../WorkspaceLayout'
import { useAICopilotStore } from '../../../stores/aiCopilotStore'

// Mock child components to isolate layout structure testing
vi.mock('../IconNav', () => ({
  IconNav: () => <nav data-testid="icon-nav">IconNav</nav>,
}))

vi.mock('../Header', () => ({
  Header: () => <header data-testid="header">Header</header>,
}))

vi.mock('../../ai-copilot/AICopilotPanel', () => ({
  AICopilotPanel: () => <aside data-testid="ai-copilot">AICopilotPanel</aside>,
}))

vi.mock('../../ui/CommandPalette', () => ({
  CommandPalette: () => null,
}))

describe('WorkspaceLayout — Three-Panel Grid Integration', () => {
  beforeEach(() => {
    useAICopilotStore.setState({ isOpen: true })
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('renders Three-Panel structure: IconNav + MainCanvas + AICopilotPanel', () => {
    render(
      <MemoryRouter>
        <WorkspaceLayout>
          <div data-testid="main-content">Main Content</div>
        </WorkspaceLayout>
      </MemoryRouter>
    )

    expect(screen.getByTestId('icon-nav')).toBeInTheDocument()
    expect(screen.getByTestId('header')).toBeInTheDocument()
    expect(screen.getByTestId('main-content')).toBeInTheDocument()
    expect(screen.getByTestId('ai-copilot')).toBeInTheDocument()
  })

  it('uses CSS Grid with 48px + 1fr + 320px columns when Copilot is open', () => {
    const { container } = render(
      <MemoryRouter>
        <WorkspaceLayout>
          <div>Content</div>
        </WorkspaceLayout>
      </MemoryRouter>
    )

    const root = container.firstElementChild as HTMLElement
    expect(root.style.gridTemplateColumns).toBe('48px 1fr 320px')
  })

  it('uses CSS Grid with 48px + 1fr + 0fr columns when Copilot is closed', () => {
    useAICopilotStore.setState({ isOpen: false })

    const { container } = render(
      <MemoryRouter>
        <WorkspaceLayout>
          <div>Content</div>
        </WorkspaceLayout>
      </MemoryRouter>
    )

    const root = container.firstElementChild as HTMLElement
    expect(root.style.gridTemplateColumns).toBe('48px 1fr 0fr')
  })

  it('Header spans full top row (col-start-2 col-span-2) independent of Copilot state', () => {
    const { container } = render(
      <MemoryRouter>
        <WorkspaceLayout>
          <div>Content</div>
        </WorkspaceLayout>
      </MemoryRouter>
    )

    const headerWrapper = container.querySelector('.col-start-2.col-span-2')
    expect(headerWrapper).toBeInTheDocument()
    expect(headerWrapper).toContainElement(screen.getByTestId('header'))
  })

  it('IconNav spans both rows (row-span-2)', () => {
    const { container } = render(
      <MemoryRouter>
        <WorkspaceLayout>
          <div>Content</div>
        </WorkspaceLayout>
      </MemoryRouter>
    )

    const iconNavWrapper = container.querySelector('.row-span-2')
    expect(iconNavWrapper).toBeInTheDocument()
    expect(iconNavWrapper).toContainElement(screen.getByTestId('icon-nav'))
  })

  it('main canvas has flex layout and min-w-0 to prevent overflow', () => {
    const { container } = render(
      <MemoryRouter>
        <WorkspaceLayout>
          <div>Content</div>
        </WorkspaceLayout>
      </MemoryRouter>
    )

    const main = container.querySelector('main')
    expect(main).toHaveClass('flex', 'flex-col', 'min-w-0')
  })

  it('grid column count transitions smoothly', () => {
    const { container } = render(
      <MemoryRouter>
        <WorkspaceLayout>
          <div>Content</div>
        </WorkspaceLayout>
      </MemoryRouter>
    )

    const root = container.firstElementChild as HTMLElement
    expect(root.style.transition).toMatch(/grid-template-columns/)
  })
})
