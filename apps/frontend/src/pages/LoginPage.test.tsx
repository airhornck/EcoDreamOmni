import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { LoginPage } from './LoginPage'

// Mutable mock state that tests can control
const mockStore = {
  login: vi.fn(),
  isLoading: false,
  error: null as string | null,
  isAuthenticated: false,
}

vi.mock('../stores/authStore', () => ({
  useAuthStore: (selector?: (s: typeof mockStore) => unknown) => {
    // If selector is provided, call it; otherwise return the whole store
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('LoginPage', () => {
  beforeEach(() => {
    mockStore.login.mockClear()
    mockStore.isLoading = false
    mockStore.error = null
    mockStore.isAuthenticated = false
  })

  function renderWithRouter(ui: React.ReactNode) {
    return render(<MemoryRouter>{ui}</MemoryRouter>)
  }

  it('renders login form with email, password inputs and submit button', () => {
    renderWithRouter(<LoginPage />)
    expect(screen.getByLabelText(/邮箱/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument()
  })

  it('shows validation error when email is empty', async () => {
    renderWithRouter(<LoginPage />)
    fireEvent.click(screen.getByRole('button', { name: /登录/i }))
    await waitFor(() => {
      expect(screen.getByText(/请输入邮箱/i)).toBeInTheDocument()
    })
  })

  it('shows validation error when password is empty', async () => {
    renderWithRouter(<LoginPage />)
    fireEvent.click(screen.getByRole('button', { name: /登录/i }))
    await waitFor(() => {
      expect(screen.getByText(/请输入密码/i)).toBeInTheDocument()
    })
  })

  it('calls login with email and password on valid submit', async () => {
    mockStore.login.mockResolvedValue(undefined)
    renderWithRouter(<LoginPage />)

    fireEvent.change(screen.getByLabelText(/邮箱/i), {
      target: { value: 'test@ecodream.com' },
    })
    fireEvent.change(screen.getByLabelText(/密码/i), {
      target: { value: 'SecurePass123!' },
    })
    fireEvent.click(screen.getByRole('button', { name: /登录/i }))

    await waitFor(() => {
      expect(mockStore.login).toHaveBeenCalledWith('test@ecodream.com', 'SecurePass123!')
    })
  })

  it('disables submit button and shows loading state during login', () => {
    mockStore.isLoading = true
    renderWithRouter(<LoginPage />)
    const button = screen.getByRole('button', { name: /登录中/i })
    expect(button).toBeDisabled()
  })

  it('displays error message when login fails', () => {
    mockStore.error = '邮箱或密码错误'
    renderWithRouter(<LoginPage />)
    expect(screen.getByText(/邮箱或密码错误/i)).toBeInTheDocument()
  })
})
