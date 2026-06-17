import { create } from 'zustand'

export interface UserProfile {
  id: string
  email: string
  username: string
  role: string
  avatar?: string
  remark?: string
}

interface AuthState {
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  user: UserProfile | null
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
  updateUser: (updates: Partial<Omit<UserProfile, 'id' | 'email' | 'role'>>) => void
  clearError: () => void
}

const storedToken = localStorage.getItem('token')
const storedUser = localStorage.getItem('user')

function safeParseUser(raw: string | null): AuthState['user'] | null {
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as AuthState['user']
    // 兼容旧数据：无 id 字段时清除，需重新登录
    if (!parsed?.id) {
      localStorage.removeItem('user')
      return null
    }
    return parsed
  } catch {
    localStorage.removeItem('user')
    return null
  }
}

function persistUser(user: AuthState['user']) {
  if (user) {
    localStorage.setItem('user', JSON.stringify(user))
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: !!storedToken,
  isLoading: false,
  error: null,
  user: safeParseUser(storedUser),

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || '邮箱或密码错误')
      }
      const data = await response.json()
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      set({
        isAuthenticated: true,
        isLoading: false,
        user: data.user,
        error: null,
      })
      return true
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : '登录失败',
      })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ isAuthenticated: false, user: null, error: null })
  },

  updateUser: (updates) => {
    set((state) => {
      if (!state.user) return state
      const next = { ...state.user, ...updates }
      persistUser(next)
      return { user: next }
    })
  },

  clearError: () => set({ error: null }),
}))
