import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setupAuthIntercept } from './authIntercept'

const logout = vi.fn()

vi.mock('../stores/authStore', () => ({
  useAuthStore: {
    getState: () => ({ logout }),
  },
}))

describe('setupAuthIntercept', () => {
  let cleanup: () => void
  let originalLocation: Location
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    originalLocation = window.location
    // @ts-expect-error jsdom 允许替换 location 为普通对象以便测试
    delete window.location
    // @ts-expect-error jsdom 允许替换 window.location 为普通对象
    window.location = { href: 'http://localhost' }

    mockFetch = vi.fn()
    global.fetch = mockFetch
    cleanup = setupAuthIntercept()
  })

  afterEach(() => {
    cleanup()
    logout.mockClear()
    // @ts-expect-error jsdom 允许恢复 window.location 为原始对象
    window.location = originalLocation
  })

  it('logs out and redirects to /login on 401 with Authorization header', async () => {
    mockFetch.mockResolvedValue({ status: 401, ok: false })

    await window.fetch('/api/task-hub/tasks', {
      headers: { Authorization: 'Bearer invalid' },
    })

    expect(logout).toHaveBeenCalledTimes(1)
    expect(window.location.href).toBe('/login')
  })

  it('does not redirect on 401 without Authorization header (e.g. login failure)', async () => {
    mockFetch.mockResolvedValue({
      status: 401,
      ok: false,
      json: async () => ({ detail: 'Invalid credentials' }),
    })

    await window.fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'a', password: 'b' }),
    })

    expect(logout).not.toHaveBeenCalled()
    expect(window.location.href).not.toBe('/login')
  })

  it('does nothing on successful responses', async () => {
    mockFetch.mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => ({ items: [] }),
    })

    await window.fetch('/api/task-hub/tasks', {
      headers: { Authorization: 'Bearer valid' },
    })

    expect(logout).not.toHaveBeenCalled()
    expect(window.location.href).not.toBe('/login')
  })
})
