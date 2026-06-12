import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface TrendReport {
  id: string
  query: string
  stage_filter?: string
  crawl_time: string
  results: TrendItem[]
}

export interface TrendItem {
  rank: number
  title: string
  title_structure?: string
  engagement_hint?: string
  stage?: string
  tags: string[]
  post_time?: string
  post_day?: string
}

export interface Topic {
  id: string
  title: string
  source_report_id?: string
  source_report_query?: string
  estimated_engagement?: number
  tags: string[]
  status: 'pending' | 'adopted' | 'abandoned'
  created_at: string
}

export interface HotKeyword {
  word: string
  heat: number
  trend: 'up' | 'down' | 'stable'
}

export interface TrendScoutStats {
  totalReports: number
  weekReports: number
  hotTopics: number
  adoptedTopics: number
}

interface TrendScoutState {
  reports: TrendReport[]
  currentReport: TrendReport | null
  topics: Topic[]
  hotKeywords: HotKeyword[]
  stats: TrendScoutStats | null
  isLoading: boolean
  error: string | null
  fetchReports: () => Promise<void>
  createReport: (query: string, stageFilter?: string) => Promise<TrendReport | null>
  getReport: (id: string) => Promise<TrendReport | null>
  createPersonaDraft: (data: unknown) => Promise<unknown | null>
  fetchTopics: () => Promise<void>
  updateTopic: (id: string, status: Topic['status']) => Promise<void>
  deleteTopic: (id: string) => Promise<void>
  fetchHotKeywords: () => Promise<void>
  createTopicFromReport: (reportId: string, title: string, tags?: string[]) => Promise<Topic | null>
  fetchStats: () => Promise<void>
}

export const useTrendScoutStore = create<TrendScoutState>((set, get) => ({
  reports: [],
  currentReport: null,
  topics: [],
  hotKeywords: [],
  stats: null,
  isLoading: false,
  error: null,

  fetchReports: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/trend-scout/reports', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取趋势报告失败: ${res.status}`)
      const data = await res.json()
      set({ reports: data.reports || data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  createReport: async (query, stageFilter) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/trend-scout/reports', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ query, stage_filter: stageFilter }),
      })
      if (!res.ok) throw new Error('创建趋势报告失败')
      const data = await res.json()
      await get().fetchReports()
      set({ isLoading: false })
      return data
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '创建失败' })
      return null
    }
  },

  getReport: async (id) => {
    try {
      const res = await fetch(`/api/trend-scout/reports/${id}`, { headers: authHeaders() })
      if (!res.ok) throw new Error('获取报告详情失败')
      const data = await res.json()
      set({ currentReport: data })
      return data
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取失败' })
      return null
    }
  },

  createPersonaDraft: async (data) => {
    try {
      const res = await fetch('/api/trend-scout/persona-draft', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('创建人设草案失败')
      return await res.json()
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败' })
      return null
    }
  },

  fetchTopics: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/trend-scout/topics', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取选题失败')
      const data = await res.json()
      set({ topics: data.topics || data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '获取选题失败' })
    }
  },

  updateTopic: async (id, status) => {
    try {
      const res = await fetch(`/api/trend-scout/topics/${id}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify({ status }),
      })
      if (!res.ok) throw new Error('更新选题失败')
      await get().fetchTopics()
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新失败' })
    }
  },

  deleteTopic: async (id) => {
    try {
      const res = await fetch(`/api/trend-scout/topics/${id}`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('删除选题失败')
      await get().fetchTopics()
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
    }
  },

  fetchHotKeywords: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/trend-scout/hot-keywords', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取热搜失败')
      const data = await res.json()
      set({ hotKeywords: data.keywords || data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '获取热搜失败' })
    }
  },

  createTopicFromReport: async (reportId, title, tags = []) => {
    try {
      const res = await fetch('/api/trend-scout/topics', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ source_report_id: reportId, title, tags }),
      })
      if (!res.ok) throw new Error('创建选题失败')
      const data = await res.json()
      await get().fetchTopics()
      return data
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建选题失败' })
      return null
    }
  },

  fetchStats: async () => {
    try {
      const res = await fetch('/api/trend-scout/stats', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取统计失败')
      const data = await res.json()
      set({ stats: data })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取统计失败' })
    }
  },
}))
