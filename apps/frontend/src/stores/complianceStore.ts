import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface ViolationItem {
  rule_id: string
  level: string
  category: string
  matched: string
  message: string
  suggestion: string
  replacement?: string
}

export interface ComplianceResult {
  evidence_id: string
  content_id: string
  level: string
  violations: ViolationItem[]
  suggestions: string[]
  checked_at: string
  original_text?: string
}

export interface ComplianceRule {
  rule_id: string
  level: string
  category: string
  description: string
  action: string
  hit_count?: number
}

export interface ComplianceStats {
  l1: { today: number; total: number }
  l2: { today: number; total: number }
  l3: { today: number }
  l4: { today: number }
}

export interface ScanHistoryItem {
  id: string
  content_preview: string
  status: 'pass' | 'fail'
  violation_count: number
  checked_at: string
}

interface ComplianceState {
  results: ComplianceResult[]
  rules: ComplianceRule[]
  stats: ComplianceStats | null
  history: ScanHistoryItem[]
  isLoading: boolean
  error: string | null
  activeTab: 'single' | 'batch'
  levelFilter: string
  searchQuery: string
  fetchRules: () => Promise<void>
  checkContent: (text: string, contentId?: string) => Promise<ComplianceResult | null>
  batchCheck: (items: Array<{ text: string; content_id?: string }>) => Promise<ComplianceResult[] | null>
  fetchStats: () => Promise<void>
  fetchHistory: (limit?: number) => Promise<void>
  clearHistory: () => Promise<void>
  setActiveTab: (tab: 'single' | 'batch') => void
  setLevelFilter: (filter: string) => void
  setSearchQuery: (query: string) => void
}

export const useComplianceStore = create<ComplianceState>((set) => ({
  results: [],
  rules: [],
  stats: null,
  history: [],
  isLoading: false,
  error: null,
  activeTab: 'single',
  levelFilter: 'all',
  searchQuery: '',

  fetchRules: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/compliance/rules', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取规则失败: ${res.status}`)
      const data = await res.json()
      set({ rules: data.rules || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  checkContent: async (text, contentId = '') => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/compliance/check', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ text, content_id: contentId }),
      })
      if (!res.ok) throw new Error('合规检查失败')
      const data = await res.json()
      const result: ComplianceResult = { ...data, original_text: text }
      set((state) => ({ results: [result, ...state.results], isLoading: false }))
      return result
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '检查失败' })
      return null
    }
  },

  batchCheck: async (items) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/compliance/batch-check', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ items }),
      })
      if (!res.ok) throw new Error('批量检查失败')
      const data = await res.json()
      const results: ComplianceResult[] = (data.results || []).map((r: ComplianceResult, idx: number) => ({
        ...r,
        original_text: items[idx]?.text,
      }))
      set((state) => ({ results: [...results, ...state.results], isLoading: false }))
      return results
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '检查失败' })
      return null
    }
  },

  fetchStats: async () => {
    try {
      const res = await fetch('/api/compliance/stats', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取统计失败: ${res.status}`)
      const data = await res.json()
      set({ stats: data })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取统计失败' })
    }
  },

  fetchHistory: async (limit = 20) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch(`/api/compliance/history?limit=${limit}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取历史记录失败: ${res.status}`)
      const data = await res.json()
      set({ history: data.history || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '获取历史记录失败' })
    }
  },

  clearHistory: async () => {
    try {
      const res = await fetch('/api/compliance/history', {
        method: 'DELETE',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('清空历史记录失败')
      set({ history: [] })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '清空历史记录失败' })
    }
  },

  setActiveTab: (tab) => set({ activeTab: tab }),
  setLevelFilter: (filter) => set({ levelFilter: filter }),
  setSearchQuery: (query) => set({ searchQuery: query }),
}))
