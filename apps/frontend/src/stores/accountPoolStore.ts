import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface Violation {
  id: string
  rule: string
  occurred_at: string
  severity: 'low' | 'medium' | 'high'
}

export interface HealthDetail {
  activity_score: number
  content_quality_score: number
  engagement_rate: number
  compliance_score: number
}

export interface AccountEntry {
  id: string
  platform: string
  username: string
  account_id?: string
  nickname?: string
  status: 'active' | 'paused' | 'suspended'
  health_score: number
  created_at: string

  /* enhanced fields */
  followers_count?: number
  risk_level?: 'safe' | 'warning' | 'danger'
  persona_id?: string | null
  persona_name?: string | null
  persona?: string
  content_vertical?: string
  lifecycle_phase?: string
  cookie?: string
  posts_last_7d?: number
  last_posted_at?: string | null
  weekly_posts?: number[]
  health_detail?: HealthDetail
  violations?: Violation[]
  suggestions?: string[]
  cookie_note?: string
  proxy_config?: {
    proxy_id: string
    type: string
    region: string
  } | null
  /* daily quota */
  daily_quota?: number
  posts_today?: number
  quota_utilization?: number
  quota_remaining?: number
  quota_exceeded?: boolean
  last_post_reset?: string
  /* engagement data recovery */
  auto_engagement_fetch?: boolean
}

export interface AccountPoolStats {
  total: number
  active: number
  avg_health_score: number
  today_posts: number
  total_quota?: number
  quota_utilization_avg?: number
  quota_exceeded_count?: number
}

export interface PersonaOption {
  id: string
  name: string
}

interface AccountPoolState {
  accounts: AccountEntry[]
  personas: PersonaOption[]
  stats: AccountPoolStats
  isLoading: boolean
  isFormLoading: boolean
  error: string | null
  fetchAccounts: () => Promise<void>
  fetchPersonas: () => Promise<void>
  createAccount: (data: Record<string, unknown>) => Promise<boolean>
  updateAccount: (id: string, data: Record<string, unknown>) => Promise<boolean>
  deleteAccount: (id: string) => Promise<boolean>
  updateAccountStatus: (id: string, status: AccountEntry['status']) => Promise<boolean>
  bindPersona: (id: string, personaId: string | null) => Promise<boolean>
}

const defaultStats: AccountPoolStats = {
  total: 0,
  active: 0,
  avg_health_score: 0,
  today_posts: 0,
}

export const useAccountPoolStore = create<AccountPoolState>((set, get) => ({
  accounts: [],
  personas: [],
  stats: defaultStats,
  isLoading: false,
  isFormLoading: false,
  error: null,

  fetchAccounts: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/account-pool', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取账号列表失败: ${res.status}`)
      const data = await res.json()
      set({
        accounts: data.accounts || [],
        stats: data.stats || defaultStats,
        isLoading: false,
      })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  fetchPersonas: async () => {
    try {
      const res = await fetch('/api/personas', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取人设列表失败: ${res.status}`)
      const data = await res.json()
      const personas = (data.personas || []).map((p: { id: string; name?: string; nickname?: string }) => ({
        id: p.id,
        name: p.name || p.nickname || '未命名',
      }))
      set({ personas })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取人设列表失败' })
    }
  },

  createAccount: async (data) => {
    set({ isFormLoading: true, error: null })
    try {
      const res = await fetch('/api/account-pool', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('创建失败')
      await get().fetchAccounts()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败', isFormLoading: false })
      return false
    } finally {
      set({ isFormLoading: false })
    }
  },

  updateAccount: async (id, data) => {
    set({ isFormLoading: true, error: null })
    try {
      const res = await fetch(`/api/account-pool/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('更新失败')
      await get().fetchAccounts()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新失败', isFormLoading: false })
      return false
    } finally {
      set({ isFormLoading: false })
    }
  },

  deleteAccount: async (id) => {
    try {
      const res = await fetch(`/api/account-pool/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('删除失败')
      await get().fetchAccounts()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },

  updateAccountStatus: async (id, status) => {
    try {
      const res = await fetch(`/api/account-pool/${id}/status`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify({ status }),
      })
      if (!res.ok) throw new Error('状态更新失败')
      await get().fetchAccounts()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '状态更新失败' })
      return false
    }
  },

  bindPersona: async (id, personaId) => {
    try {
      const res = await fetch(`/api/account-pool/${id}/persona`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify({ persona_id: personaId }),
      })
      if (!res.ok) throw new Error('绑定失败')
      await get().fetchAccounts()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '绑定失败' })
      return false
    }
  },
}))
