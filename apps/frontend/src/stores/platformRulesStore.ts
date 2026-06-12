import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface PlatformRule {
  id: string
  layer: string
  name: string
  description?: string
  condition_json?: Record<string, unknown>
  action: string
  priority: number
  enabled: boolean
  version: number
  effective_from?: string
  created_by?: string
  platform: string
  applicable_lifecycle?: string[]
}

export interface RuleHistoryItem {
  id: string
  rule_id: string
  name: string
  layer: string
  condition_json: Record<string, unknown>
  action: string
  priority: number
  enabled: boolean
  version: number
  change_reason?: string
  changed_by?: string
  created_at?: string
}

export interface EvaluateResult {
  pass: boolean
  violations: Array<{
    rule_id: string
    layer: string
    name: string
    action: string
    matched?: string
  }>
  warnings: Array<{
    rule_id: string
    layer: string
    name: string
    action: string
    matched?: string
  }>
  suggestions: Array<{
    rule_id: string
    layer: string
    name: string
    action: string
    matched?: string
  }>
  violation_count: number
  warning_count: number
  suggestion_count: number
}

interface PlatformRulesState {
  rules: PlatformRule[]
  isLoading: boolean
  error: string | null
  selectedPlatform: string
  fetchRules: (platform?: string) => Promise<void>
  createRule: (data: Partial<PlatformRule>) => Promise<boolean>
  updateRule: (id: string, data: Partial<PlatformRule>) => Promise<boolean>
  deleteRule: (id: string) => Promise<boolean>
  // history
  ruleHistory: RuleHistoryItem[]
  historyLoading: boolean
  fetchRuleHistory: (id: string) => Promise<void>
  // evaluate
  evaluateResult: EvaluateResult | null
  evaluateLoading: boolean
  evaluateContent: (content: { title: string; body: string; tags: string[]; platform?: string }) => Promise<void>
  clearEvaluate: () => void
}

export const usePlatformRulesStore = create<PlatformRulesState>((set, get) => ({
  rules: [],
  isLoading: false,
  error: null,
  selectedPlatform: 'all',
  ruleHistory: [],
  historyLoading: false,
  evaluateResult: null,
  evaluateLoading: false,

  fetchRules: async (platform) => {
    set({ isLoading: true, error: null })
    try {
      const url = platform && platform !== 'all'
        ? `/api/platform-rules?platform=${encodeURIComponent(platform)}`
        : '/api/platform-rules'
      const res = await fetch(url, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取规则列表失败: ${res.status}`)
      const data = await res.json()
      set({ rules: data.rules || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  createRule: async (data) => {
    try {
      const res = await fetch('/api/platform-rules', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('创建失败')
      await get().fetchRules(get().selectedPlatform)
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败' })
      return false
    }
  },

  updateRule: async (id, data) => {
    try {
      const res = await fetch(`/api/platform-rules/${id}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('更新失败')
      await get().fetchRules(get().selectedPlatform)
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新失败' })
      return false
    }
  },

  deleteRule: async (id) => {
    try {
      const res = await fetch(`/api/platform-rules/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('删除失败')
      await get().fetchRules(get().selectedPlatform)
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },

  fetchRuleHistory: async (id) => {
    set({ historyLoading: true })
    try {
      const res = await fetch(`/api/platform-rules/${id}/history`, { headers: authHeaders() })
      if (!res.ok) throw new Error('获取历史失败')
      const data = await res.json()
      set({ ruleHistory: data.history || [], historyLoading: false })
    } catch (err) {
      set({ historyLoading: false, error: err instanceof Error ? err.message : '获取历史失败' })
    }
  },

  evaluateContent: async (content) => {
    set({ evaluateLoading: true })
    try {
      const res = await fetch('/api/platform-rules/evaluate', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(content),
      })
      if (!res.ok) throw new Error('评估失败')
      const data = await res.json()
      set({
        evaluateResult: {
          pass: data.pass_v,
          violations: data.violations || [],
          warnings: data.warnings || [],
          suggestions: data.suggestions || [],
          violation_count: data.violation_count || 0,
          warning_count: data.warning_count || 0,
          suggestion_count: data.suggestion_count || 0,
        },
        evaluateLoading: false,
      })
    } catch (err) {
      set({ evaluateLoading: false, error: err instanceof Error ? err.message : '评估失败' })
    }
  },

  clearEvaluate: () => set({ evaluateResult: null }),
}))
