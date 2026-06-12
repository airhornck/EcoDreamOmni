import { create } from 'zustand'
import { authHeaders } from '../lib/api'

// ─── Types ───

export interface DashboardAgent {
  agent_id: string
  name: string
  role: string
  status: string
  healthy: boolean
  queue_depth: number
  version: string
  completion_rate: number
  total_tasks_1h: number
}

export interface AgentSummary {
  total: number
  healthy: number
  unhealthy: number
}

export interface AlertSummaryItem {
  id: string
  severity: string
  alert_type: string
  agent_id: string
  message: string
  created_at: string
}

export interface CockpitDashboard {
  agents: DashboardAgent[]
  agent_summary: AgentSummary
  watch_dashboard: unknown
  overall_metrics: OverallMetrics
  open_alerts: AlertSummaryItem[]
  active_traces: unknown[]
}

export interface HubAgent {
  id: string
  name: string
  role: string
  description: string
  owner: string
  status: string
  created_at: string
  updated_at: string
}

export interface AgentConfig {
  id: string
  agent_id: string
  version: number
  env: string
  sha256: string
  config_payload: Record<string, unknown>
  created_by: string
  created_at: string
}

export interface AlertItem {
  id: string
  severity: string
  alert_type: string
  agent_id: string
  message: string
  created_at: string
  status: string
}

export interface OverallMetrics {
  window_start: string
  window_end: string
  total_tasks: number
  total_agents: number
  overall_completion_rate: number
  total_tokens: number
  total_cost_usd: number
}

export interface CostByAgent {
  agent_id: string
  agent_role: string
  task_count: number
  total_tokens: number
  total_cost_usd: number
}

export interface ActivityItem {
  type: 'task' | 'alert' | 'heartbeat'
  timestamp: string
  agent_id: string
  agent_role?: string
  outcome?: string
  content_id?: string
  severity?: string
  alert_type?: string
  message?: string
  status?: string
  queue_depth?: number
}

export interface AlertSummary {
  total: number
  by_severity: Record<string, number>
  by_type: Record<string, number>
  by_status: Record<string, number>
  latest: { id: string; severity: string; message: string; created_at: string }[]
}

// ─── State ───

interface AgentCockpitState {
  dashboard: CockpitDashboard | null
  agents: HubAgent[]
  agentDetail: Record<string, unknown> | null
  agentConfigs: AgentConfig[]
  alerts: AlertItem[]
  overallMetrics: OverallMetrics | null
  costByAgent: CostByAgent[]
  activity: ActivityItem[]
  alertSummary: AlertSummary | null
  isLoading: boolean
  error: string | null
  activeTab: 'dashboard' | 'agents' | 'metrics' | 'alerts'

  fetchDashboard: () => Promise<void>
  fetchAgents: () => Promise<void>
  fetchAgentDetail: (id: string) => Promise<void>
  fetchAgentConfigs: (id: string) => Promise<void>
  fetchAlerts: () => Promise<void>
  ackAlert: (id: string, ackedBy: string) => Promise<boolean>
  fetchOverallMetrics: () => Promise<void>
  fetchCostByAgent: () => Promise<void>
  fetchActivity: () => Promise<void>
  fetchAlertSummary: () => Promise<void>
  setActiveTab: (tab: AgentCockpitState['activeTab']) => void
  setError: (msg: string | null) => void
  clearError: () => void
}

// ─── Store ───

export const useAgentCockpitStore = create<AgentCockpitState>((set) => ({
  dashboard: null,
  agents: [],
  agentDetail: null,
  agentConfigs: [],
  alerts: [],
  overallMetrics: null,
  costByAgent: [],
  activity: [],
  alertSummary: null,
  isLoading: false,
  error: null,
  activeTab: 'dashboard',

  fetchDashboard: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/agent-cockpit/dashboard', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Dashboard: ${res.status}`)
      const data = await res.json()
      set({ dashboard: data, isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载驾驶舱数据失败' })
    }
  },

  fetchAgents: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/agent-hub/agents', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Agents: ${res.status}`)
      const data = await res.json()
      set({ agents: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载 Agent 列表失败' })
    }
  },

  fetchAgentDetail: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch(`/agent-cockpit/agents/${id}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`Agent detail: ${res.status}`)
      const data = await res.json()
      set({ agentDetail: data, isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载 Agent 详情失败' })
    }
  },

  fetchAgentConfigs: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch(`/agent-hub/agents/${id}/configs`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`Configs: ${res.status}`)
      const data = await res.json()
      set({ agentConfigs: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载配置历史失败' })
    }
  },

  fetchAlerts: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/agent-watch/alerts', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Alerts: ${res.status}`)
      const data = await res.json()
      set({ alerts: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载告警失败' })
    }
  },

  ackAlert: async (id: string, ackedBy: string) => {
    try {
      const res = await fetch(`/agent-watch/alerts/${id}/ack`, {
        method: 'PATCH',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ acked_by: ackedBy }),
      })
      return res.ok
    } catch {
      return false
    }
  },

  fetchOverallMetrics: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/agent-metrics/overall', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Metrics: ${res.status}`)
      const data = await res.json()
      set({ overallMetrics: data, isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载统计指标失败' })
    }
  },

  fetchCostByAgent: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/agent-metrics/cost/by-agent', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Cost: ${res.status}`)
      const data = await res.json()
      set({ costByAgent: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载成本归因失败' })
    }
  },

  fetchActivity: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/agent-cockpit/activity', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Activity: ${res.status}`)
      const data = await res.json()
      set({ activity: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载活动流失败' })
    }
  },

  fetchAlertSummary: async () => {
    try {
      const res = await fetch('/agent-cockpit/alerts/summary', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Alert summary: ${res.status}`)
      const data = await res.json()
      set({ alertSummary: data })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '加载告警摘要失败' })
    }
  },

  setActiveTab: (tab) => set({ activeTab: tab }),
  setError: (msg) => set({ error: msg }),
  clearError: () => set({ error: null }),
}))
