import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Header } from '../Header'

const mockToggle = vi.fn()

const mockAuthStore = {
  user: {
    id: 'u1',
    username: 'alice',
    email: 'alice@ecodream.local',
    role: 'admin',
  },
  logout: vi.fn(),
}

const mockAICopilotStore = {
  isOpen: false,
  toggle: mockToggle,
}

vi.mock('../../../stores/authStore', () => ({
  useAuthStore: (selector?: (s: typeof mockAuthStore) => unknown) => {
    return selector ? selector(mockAuthStore) : mockAuthStore
  },
}))

vi.mock('../../../stores/aiCopilotStore', () => ({
  useAICopilotStore: (selector?: (s: typeof mockAICopilotStore) => unknown) => {
    return selector ? selector(mockAICopilotStore) : mockAICopilotStore
  },
}))

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthStore.user = {
      id: 'u1',
      username: 'alice',
      email: 'alice@ecodream.local',
      role: 'admin',
    }
    mockAICopilotStore.isOpen = false
  })

  function Wrapper({ children }: { children: React.ReactNode }) {
    return <MemoryRouter>{children}</MemoryRouter>
  }

  it('renders username and avatar initial', () => {
    render(
      <Wrapper>
        <Header />
      </Wrapper>
    )

    expect(screen.getByText('alice')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
  })

  it('opens user menu dropdown when user area is clicked', () => {
    render(
      <Wrapper>
        <Header />
      </Wrapper>
    )

    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    expect(screen.getByTestId('user-menu-dropdown')).toBeInTheDocument()
    expect(screen.getByTestId('user-menu-profile')).toHaveTextContent('个人信息')
    expect(screen.getByTestId('user-menu-settings')).toHaveTextContent('系统设置')
    expect(screen.getByTestId('user-menu-logout')).toHaveTextContent('登出')
  })

  it('toggles AI Copilot when copilot button clicked', () => {
    render(
      <Wrapper>
        <Header />
      </Wrapper>
    )

    fireEvent.click(screen.getByLabelText('打开 AI Copilot'))
    expect(mockToggle).toHaveBeenCalled()
  })

  it('falls back to default username when user is null', () => {
    mockAuthStore.user = null as unknown as typeof mockAuthStore.user

    render(
      <Wrapper>
        <Header />
      </Wrapper>
    )

    expect(screen.getByText('用户')).toBeInTheDocument()
  })
})
