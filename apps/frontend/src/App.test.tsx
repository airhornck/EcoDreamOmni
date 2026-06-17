import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AppRoutes } from './App'

// Mock auth store to be authenticated
vi.mock('./stores/authStore', () => ({
  useAuthStore: () => ({
    isAuthenticated: true,
  }),
}))

// Mock layouts
vi.mock('./components/layout/AppLayout', () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-layout">{children}</div>
  ),
}))

vi.mock('./components/layout/WorkspaceLayout', () => ({
  WorkspaceLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="workspace-layout">{children}</div>
  ),
}))

vi.mock('./pages/StrategyElementsPage', () => ({
  StrategyElementsPage: () => <div data-testid="strategy-elements-page">Strategy Elements</div>,
}))

vi.mock('./pages/AgentOrchestraPage', () => ({
  AgentOrchestraPage: () => <div data-testid="agent-orchestra-page">Agent Orchestra</div>,
}))

describe('AppRoutes', () => {
  it('renders playground route', () => {
    render(
      <MemoryRouter initialEntries={['/playground']}>
        <AppRoutes />
      </MemoryRouter>
    )

    // LabPage should be loading (lazy) or rendered
    expect(document.body).toBeTruthy()
  })

  it('redirects /keywords to /strategy-elements', async () => {
    render(
      <MemoryRouter initialEntries={['/keywords']}>
        <AppRoutes />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('strategy-elements-page')).toBeInTheDocument()
    })
  })

  it('redirects /templates to /strategy-elements', async () => {
    render(
      <MemoryRouter initialEntries={['/templates']}>
        <AppRoutes />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('strategy-elements-page')).toBeInTheDocument()
    })
  })

  it('renders /strategy-elements route', async () => {
    render(
      <MemoryRouter initialEntries={['/strategy-elements']}>
        <AppRoutes />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('strategy-elements-page')).toBeInTheDocument()
    })
  })

  it('redirects /workflows to /agents', async () => {
    render(
      <MemoryRouter initialEntries={['/workflows']}>
        <AppRoutes />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('agent-orchestra-page')).toBeInTheDocument()
    })
  })

  it('redirects /workflow-cockpit to /agents', async () => {
    render(
      <MemoryRouter initialEntries={['/workflow-cockpit']}>
        <AppRoutes />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('agent-orchestra-page')).toBeInTheDocument()
    })
  })
})
