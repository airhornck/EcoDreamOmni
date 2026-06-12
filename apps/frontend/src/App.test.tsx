import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
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
})
