import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { UserMenuDropdown } from '../UserMenuDropdown'

const mockLogout = vi.fn()

const mockAuthStore = {
  user: {
    id: 'u1',
    username: 'admin',
    email: 'admin@ecodream.local',
    role: 'admin',
  },
  logout: mockLogout,
}

vi.mock('../../../stores/authStore', () => ({
  useAuthStore: (selector?: (s: typeof mockAuthStore) => unknown) => {
    return selector ? selector(mockAuthStore) : mockAuthStore
  },
}))

describe('UserMenuDropdown', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    mockAuthStore.user = {
      id: 'u1',
      username: 'admin',
      email: 'admin@ecodream.local',
      role: 'admin',
    }
    mockAuthStore.logout = mockLogout
  })

  function Wrapper({ children }: { children: React.ReactNode }) {
    return <MemoryRouter>{children}</MemoryRouter>
  }

  it('renders trigger and opens menu on click', () => {
    render(
      <Wrapper>
        <UserMenuDropdown trigger={<span>Open</span>} />
      </Wrapper>
    )

    expect(screen.getByTestId('user-menu-trigger')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    expect(screen.getByTestId('user-menu-dropdown')).toBeInTheDocument()
  })

  it('displays user info in menu header', () => {
    render(
      <Wrapper>
        <UserMenuDropdown trigger={<span>Open</span>} />
      </Wrapper>
    )

    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    expect(screen.getByTestId('user-menu-username')).toHaveTextContent('admin')
    expect(screen.getByTestId('user-menu-email')).toHaveTextContent('admin@ecodream.local')
    expect(screen.getByTestId('user-menu-role')).toHaveTextContent('admin')
  })

  it('shows profile, settings and logout menu items', () => {
    render(
      <Wrapper>
        <UserMenuDropdown trigger={<span>Open</span>} />
      </Wrapper>
    )

    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    expect(screen.getByTestId('user-menu-profile')).toHaveTextContent('个人信息')
    expect(screen.getByTestId('user-menu-settings')).toHaveTextContent('系统设置')
    expect(screen.getByTestId('user-menu-logout')).toHaveTextContent('登出')
  })

  it('closes menu when profile item clicked', () => {
    const onOpenChange = vi.fn()
    render(
      <Wrapper>
        <UserMenuDropdown trigger={<span>Open</span>} onOpenChange={onOpenChange} />
      </Wrapper>
    )

    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    expect(screen.getByTestId('user-menu-dropdown')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('user-menu-profile'))
    expect(screen.queryByTestId('user-menu-dropdown')).not.toBeInTheDocument()
    expect(onOpenChange).toHaveBeenLastCalledWith(false)
  })

  it('closes menu when settings item clicked', () => {
    const onOpenChange = vi.fn()
    render(
      <Wrapper>
        <UserMenuDropdown trigger={<span>Open</span>} onOpenChange={onOpenChange} />
      </Wrapper>
    )

    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    fireEvent.click(screen.getByTestId('user-menu-settings'))
    expect(screen.queryByTestId('user-menu-dropdown')).not.toBeInTheDocument()
    expect(onOpenChange).toHaveBeenLastCalledWith(false)
  })

  it('calls logout when logout clicked', async () => {
    render(
      <Wrapper>
        <UserMenuDropdown trigger={<span>Open</span>} />
      </Wrapper>
    )

    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    fireEvent.click(screen.getByTestId('user-menu-logout'))

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalled()
    })
  })

  it('closes menu when clicking outside', () => {
    render(
      <Wrapper>
        <UserMenuDropdown trigger={<span>Open</span>} />
      </Wrapper>
    )

    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    expect(screen.getByTestId('user-menu-dropdown')).toBeInTheDocument()

    fireEvent.mouseDown(document.body)
    expect(screen.queryByTestId('user-menu-dropdown')).not.toBeInTheDocument()
  })

  it('closes menu on Escape key', () => {
    render(
      <Wrapper>
        <UserMenuDropdown trigger={<span>Open</span>} />
      </Wrapper>
    )

    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    expect(screen.getByTestId('user-menu-dropdown')).toBeInTheDocument()

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByTestId('user-menu-dropdown')).not.toBeInTheDocument()
  })

  it('renders with portal mode without crashing', () => {
    render(
      <Wrapper>
        <UserMenuDropdown trigger={<span>Open</span>} usePortal align="left" />
      </Wrapper>
    )

    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    expect(screen.getByTestId('user-menu-dropdown')).toBeInTheDocument()
  })

  it('shows fallback when user is null', () => {
    mockAuthStore.user = null as unknown as typeof mockAuthStore.user

    render(
      <Wrapper>
        <UserMenuDropdown trigger={<span>Open</span>} />
      </Wrapper>
    )

    fireEvent.click(screen.getByTestId('user-menu-trigger'))
    expect(screen.getByText('用户')).toBeInTheDocument()
  })
})
