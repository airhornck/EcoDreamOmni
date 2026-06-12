import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface TimelineEvent {
  id: string
  name: string
  event_type: 'SEASONAL' | 'PRODUCT_LAUNCH' | 'PLATFORM_PROMO' | 'CUSTOM'
  description?: string
  start_date: string
  end_date: string
  recurring: boolean
  cron_expression?: string
  year: number
  brand_knowledge_ids: string[]
  product_ids: string[]
  prohibited_claims: string[]
  is_commercial: boolean
  status: 'active' | 'archived' | 'draft'
  priority: number
  color_code?: string
  created_by: string
  created_at: string
  updated_at: string
}

interface TimelineState {
  events: TimelineEvent[]
  isLoading: boolean
  error: string | null
  fetchEvents: (filters?: Record<string, string>) => Promise<void>
  createEvent: (data: Partial<TimelineEvent>) => Promise<boolean>
  updateEvent: (id: string, data: Partial<TimelineEvent>) => Promise<boolean>
  deleteEvent: (id: string) => Promise<boolean>
}

export const useTimelineStore = create<TimelineState>((set, get) => ({
  events: [],
  isLoading: false,
  error: null,

  fetchEvents: async (filters = {}) => {
    set({ isLoading: true, error: null })
    try {
      const qs = new URLSearchParams(filters).toString()
      const res = await fetch(`/api/timeline/events?${qs}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取失败: ${res.status}`)
      const data = await res.json()
      set({ events: data.items || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  createEvent: async (data) => {
    try {
      const res = await fetch('/api/timeline/events', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('创建失败')
      await get().fetchEvents()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败' })
      return false
    }
  },

  updateEvent: async (id, data) => {
    try {
      const res = await fetch(`/api/timeline/events/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('更新失败')
      await get().fetchEvents()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新失败' })
      return false
    }
  },

  deleteEvent: async (id) => {
    try {
      const res = await fetch(`/api/timeline/events/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('删除失败')
      await get().fetchEvents()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },
}))
