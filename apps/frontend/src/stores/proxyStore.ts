import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface ProxyEntry {
  id: string
  name: string
  provider: string
  protocol: string
  host: string
  port: number
  username: string
  password: string
  region: string
  rotation_type: string
  is_active: boolean
  health_status: string
  last_check_at: string | null
  fail_count: number
  success_count: number
  created_at: string
  updated_at: string
}

interface ProxyState {
  proxies: ProxyEntry[]
  isLoading: boolean
  error: string | null
  fetchProxies: () => Promise<void>
  createProxy: (data: Partial<ProxyEntry>) => Promise<boolean>
  updateProxy: (id: string, data: Partial<ProxyEntry>) => Promise<boolean>
  deleteProxy: (id: string) => Promise<boolean>
  testProxy: (id: string) => Promise<{ success: boolean; error?: string }>
}

export const useProxyStore = create<ProxyState>((set, get) => ({
  proxies: [],
  isLoading: false,
  error: null,

  fetchProxies: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/proxies', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取代理列表失败: ${res.status}`)
      const data = await res.json()
      set({ proxies: data.proxies || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  createProxy: async (data) => {
    try {
      const res = await fetch('/api/proxies', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('创建失败')
      await get().fetchProxies()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败' })
      return false
    }
  },

  updateProxy: async (id, data) => {
    try {
      const res = await fetch(`/api/proxies/${id}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('更新失败')
      await get().fetchProxies()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新失败' })
      return false
    }
  },

  deleteProxy: async (id) => {
    try {
      const res = await fetch(`/api/proxies/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('删除失败')
      await get().fetchProxies()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },

  testProxy: async (id) => {
    try {
      const res = await fetch(`/api/proxies/${id}/test`, {
        method: 'POST',
        headers: authHeaders(),
      })
      const data = await res.json()
      await get().fetchProxies()
      return { success: data.success, error: data.error }
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '测试失败' }
    }
  },
}))
