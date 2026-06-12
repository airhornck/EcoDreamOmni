import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { WorkspaceLayout } from '../WorkspaceLayout'

// Mock child components to isolate layout testing
vi.mock('../IconNav', () => ({
  IconNav: () => <nav data-testid="icon-nav">IconNav</nav>,
}))

vi.mock('../Header', () => ({
  Header: () => <header data-testid="header">Header</header>,
}))

vi.mock('../../ai-copilot/AICopilotPanel', () => ({
  AICopilotPanel: () => <aside data-testid="ai-copilot">AICopilotPanel</aside>,
}))

describe('WorkspaceLayout', () => {
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

  it('main canvas uses flex layout with min-w-0 in Three-Panel layout', () => {
    const { container } = render(
      <MemoryRouter>
        <WorkspaceLayout>
          <div>Content</div>
        </WorkspaceLayout>
      </MemoryRouter>
    )

    const mainWrapper = container.querySelector('main')
    expect(mainWrapper).toBeInTheDocument()
    expect(mainWrapper).toHaveClass('flex')
    expect(mainWrapper).toHaveClass('min-w-0')
  })
})
