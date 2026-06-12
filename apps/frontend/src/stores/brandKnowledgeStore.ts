import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface BKEntry {
  id: string
  entry_type: 'BRAND_INFO' | 'PRODUCT_INFO' | 'FAQ' | 'PROHIBITED_CLAIM'
  name: string
  content: string
  product_id?: string
  approval_number?: string
  sku_code?: string
  brand_name?: string
  prohibited_claims: string[]
  required_disclaimers: string[]
  version: number
  is_latest: boolean
  asset_ids: string[]
  created_by: string
  created_at: string
  updated_at: string
}

interface BKState {
  entries: BKEntry[]
  isLoading: boolean
  error: string | null
  fetchEntries: (filters?: Record<string, string>) => Promise<void>
  createEntry: (data: Partial<BKEntry>) => Promise<boolean>
  updateEntry: (id: string, data: Partial<BKEntry>) => Promise<boolean>
  deleteEntry: (id: string) => Promise<boolean>
}

export const useBrandKnowledgeStore = create<BKState>((set, get) => ({
  entries: [],
  isLoading: false,
  error: null,

  fetchEntries: async (filters = {}) => {
    set({ isLoading: true, error: null })
    try {
      const qs = new URLSearchParams(filters).toString()
      const res = await fetch(`/api/brand-knowledge/entries?${qs}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取失败: ${res.status}`)
      const data = await res.json()
      set({ entries: data.items || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  createEntry: async (data) => {
    try {
      const res = await fetch('/api/brand-knowledge/entries', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('创建失败')
      await get().fetchEntries()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败' })
      return false
    }
  },

  updateEntry: async (id, data) => {
    try {
      const res = await fetch(`/api/brand-knowledge/entries/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('更新失败')
      await get().fetchEntries()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新失败' })
      return false
    }
  },

  deleteEntry: async (id) => {
    try {
      const res = await fetch(`/api/brand-knowledge/entries/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('删除失败')
      await get().fetchEntries()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },
}))
