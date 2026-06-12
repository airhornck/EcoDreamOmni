import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface LLMModel {
  id: string
  provider: string
  model_name: string
  api_key_masked: string
  endpoint_base_url?: string
  status: 'active' | 'inactive'
  data_training_opt_out: boolean
}

export interface ScopeConfig {
  id: string
  scope_type: 'global' | 'node'
  node_id?: string
  node_type?: string
  model_id: string
  model_name: string
  temperature: number
  timeout_seconds: number
  source: 'global_default' | 'override'
}

export interface CostSummary {
  period_days: number
  total_calls: number
  total_input_tokens: number
  total_output_tokens: number
  estimated_cost_cny: number
  by_model: Array<{ model_id: string; model_name: string; calls: number; cost_cny: number }>
  by_node: Array<{ node_id: string; calls: number; cost_cny: number }>
  trend: Array<{ date: string; calls: number; cost_cny: number }>
}

export interface UsageLog {
  id: string
  model_id: string
  model_name: string
  node_id: string
  provider_region: string
  input_tokens: number
  output_tokens: number
  latency_ms: number
  status: string
  created_at: string
}

interface LlmCockpitState {
  models: LLMModel[]
  scopeConfigs: ScopeConfig[]
  costSummary: CostSummary | null
  usageLogs: UsageLog[]
  isLoading: boolean
  error: string | null
  activeTab: 'models' | 'scopes' | 'costs' | 'logs'
  fetchModels: () => Promise<void>
  createModel: (data: {
    provider: string
    model_name: string
    api_key: string
    endpoint_base_url?: string
    status?: 'active' | 'inactive'
  }) => Promise<LLMModel | null>
  updateModel: (id: string, data: Partial<LLMModel>) => Promise<boolean>
  deleteModel: (id: string) => Promise<boolean>
  testConnectivity: (id: string) => Promise<boolean>
  fetchScopeConfigs: () => Promise<void>
  setGlobalDefault: (model_id: string, temperature?: number, timeout?: number) => Promise<boolean>
  setNodeOverride: (node_id: string, model_id: string, temperature?: number, timeout?: number) => Promise<boolean>
  removeNodeOverride: (config_id: string) => Promise<boolean>
  fetchCostSummary: (period_days?: number) => Promise<void>
  fetchUsageLogs: (filters?: Record<string, string>) => Promise<void>
  setActiveTab: (tab: 'models' | 'scopes' | 'costs' | 'logs') => void
  clearError: () => void
}

export const useLlmCockpitStore = create<LlmCockpitState>((set, get) => ({
  models: [],
  scopeConfigs: [],
  costSummary: null,
  usageLogs: [],
  isLoading: false,
  error: null,
  activeTab: 'models',

  fetchModels: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/llm-hub/models', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取模型失败: ${res.status}`)
      const data = await res.json()
      set({ models: data.items || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载模型失败' })
    }
  },

  createModel: async (payload) => {
    try {
      const res = await fetch('/api/llm-hub/models', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`创建模型失败: ${res.status}`)
      const model = await res.json()
      set((s) => ({ models: [model, ...s.models] }))
      return model
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建模型失败' })
      return null
    }
  },

  updateModel: async (id, payload) => {
    try {
      const res = await fetch(`/api/llm-hub/models/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`更新模型失败: ${res.status}`)
      const updated = await res.json()
      set((s) => ({
        models: s.models.map((m) => (m.id === id ? updated : m)),
      }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新模型失败' })
      return false
    }
  },

  deleteModel: async (id) => {
    try {
      const res = await fetch(`/api/llm-hub/models/${id}`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`删除模型失败: ${res.status}`)
      set((s) => ({ models: s.models.filter((m) => m.id !== id) }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除模型失败' })
      return false
    }
  },

  testConnectivity: async (id) => {
    try {
      const res = await fetch(`/api/llm-hub/models/${id}/test`, {
        method: 'POST',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`连通性测试失败: ${res.status}`)
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '连通性测试失败' })
      return false
    }
  },

  fetchScopeConfigs: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/llm-hub/scope-configs', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取应用范围失败: ${res.status}`)
      const data = await res.json()
      const configs = (data || []).map((c: { model_name?: string; current_model?: string; model_id?: string } & Record<string, unknown>) => ({
        ...c,
        model_name: c.model_name || c.current_model || c.model_id || '-',
      }))
      set({ scopeConfigs: configs, isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载应用范围失败' })
    }
  },

  setGlobalDefault: async (model_id, temperature, timeout) => {
    try {
      const res = await fetch('/api/llm-hub/scope-configs', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ scope_type: 'global', model_id, temperature, timeout_seconds: timeout }),
      })
      if (!res.ok) throw new Error(`设置全局默认失败: ${res.status}`)
      await get().fetchScopeConfigs()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '设置全局默认失败' })
      return false
    }
  },

  setNodeOverride: async (node_id, model_id, temperature, timeout) => {
    try {
      const res = await fetch('/api/llm-hub/scope-configs', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ scope_type: 'node', node_id, model_id, temperature, timeout_seconds: timeout }),
      })
      if (!res.ok) throw new Error(`设置节点覆盖失败: ${res.status}`)
      await get().fetchScopeConfigs()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '设置节点覆盖失败' })
      return false
    }
  },

  removeNodeOverride: async (config_id) => {
    try {
      const res = await fetch(`/api/llm-hub/scope-configs/${config_id}`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`恢复节点默认失败: ${res.status}`)
      await get().fetchScopeConfigs()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '恢复节点默认失败' })
      return false
    }
  },

  fetchCostSummary: async (period_days = 7) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch(`/api/llm-hub/cost-summary?period_days=${period_days}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取成本摘要失败: ${res.status}`)
      const data = await res.json()
      set({ costSummary: data || null, isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载成本摘要失败' })
    }
  },

  fetchUsageLogs: async (filters) => {
    set({ isLoading: true, error: null })
    try {
      const params = new URLSearchParams()
      if (filters) {
        Object.entries(filters).forEach(([k, v]) => {
          if (v) params.append(k, v)
        })
      }
      const url = `/api/llm-hub/usage-logs${params.toString() ? '?' + params.toString() : ''}`
      const res = await fetch(url, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取调用日志失败: ${res.status}`)
      const data = await res.json()
      set({ usageLogs: Array.isArray(data) ? data : (data.logs || []), isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载调用日志失败' })
    }
  },

  setActiveTab: (tab) => set({ activeTab: tab }),
  clearError: () => set({ error: null }),
}))
