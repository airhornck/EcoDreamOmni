import { create } from 'zustand'
import { authHeaders } from '../lib/api'
import type { Agent } from '../types/api'

export interface TaskItem {
  id: string
  name: string
  agent_id?: string              // ★ v4.0 Agent-First 新增
  agent_name?: string            // ★ v4.0 Agent-First 新增
  workflow_template_id?: string  // ★ deprecated，存量兼容
  workflow_template_name?: string
  workflow_version?: number
  account_id: string
  account_name?: string
  persona_id: string
  persona_name?: string
  persona_story_id?: string
  story_name?: string
  current_node_theme?: string
  content_series_id?: string
  content_series_name?: string
  platform?: string
  status: string
  priority: number
  current_node_index?: number
  current_step_label?: string
  estimated_completion_at?: string
  scheduled_at?: string
  created_at: string
  completed_at?: string
  dlq_info?: {
    error_reason: string
    retry_count: number
    last_failed_at: string
  }
}

export interface ContentSeries {
  id: string
  name: string
  persona_story_id?: string
  story_name?: string
  status: string
  total_tasks: number
  completed_tasks: number
  created_at: string
}

export interface DLQItem {
  id: string
  task_id: string
  task_name: string
  error_reason: string
  retry_count: number
  last_failed_at: string
}

export interface AccountOption {
  id: string
  username: string
  platform: string
}

export interface PersonaOption {
  id: string
  name: string
}

export interface PersonaStoryOption {
  id: string
  name: string
  nodes?: PersonaStoryNode[]
}

export interface PersonaStoryNode {
  id: string
  theme: string
  label?: string
}

export interface FieldConstraint {
  name: string
  label: string
  type: string
  required?: boolean
  min?: unknown
  max?: unknown
  min_chars?: number
  max_chars?: number
  max_count?: number
  default?: unknown
  supported?: string[]
  description?: string
}

export interface ContentFormat {
  format_name: string
  fields: FieldConstraint[]
}

export interface PlatformSchema {
  id: string
  platform_id: string
  display_name: string
  version: string
  content_dna: unknown[]
  audit_rules: unknown[]
  content_formats: ContentFormat[]
}

interface TaskHubState {
  tasks: TaskItem[]
  contentSeries: ContentSeries[]
  dlqItems: DLQItem[]
  accounts: AccountOption[]
  personas: PersonaOption[]
  personaStories: PersonaStoryOption[]
  platformSchemas: PlatformSchema[]
  agents: Agent[]                               // ★ v4.0 Agent-First 新增
  isLoading: boolean
  isFormLoading: boolean
  error: string | null
  fetchTasks: () => Promise<void>
  fetchContentSeries: () => Promise<void>
  fetchDLQ: () => Promise<void>
  fetchAccounts: () => Promise<void>
  fetchPersonas: () => Promise<void>
  fetchPersonaStories: (personaId: string) => Promise<void>
  fetchPersonaStoryNodes: (storyId: string) => Promise<PersonaStoryNode[]>
  fetchAgents: () => Promise<void>              // ★ v4.0 Agent-First 新增
  fetchPlatformSchemas: () => Promise<void>
  createTask: (data: Record<string, unknown>) => Promise<boolean>
  updateTaskStatus: (id: string, status: string) => Promise<boolean>
  configureTask: (id: string) => Promise<boolean>
  startWorkflow: (id: string) => Promise<boolean>
  deleteTask: (id: string) => Promise<boolean>
  retryDLQ: (id: string) => Promise<boolean>
  discardDLQ: (id: string) => Promise<boolean>
  humanDecision: (id: string, decision: string, feedback?: string) => Promise<boolean>
}

export const useTaskHubStore = create<TaskHubState>((set, get) => ({
  tasks: [],
  contentSeries: [],
  dlqItems: [],
  accounts: [],
  personas: [],
  personaStories: [],
  platformSchemas: [],
  agents: [],
  isLoading: false,
  isFormLoading: false,
  error: null,

  fetchTasks: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/task-hub/tasks', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取任务列表失败: ${res.status}`)
      const data = await res.json()
      // v4.0 后端返回 { items: TaskResponse[], copilot_summary: ... }
      set({ tasks: Array.isArray(data) ? data : (data.items || []), isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  fetchContentSeries: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/content-series', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取系列规划失败: ${res.status}`)
      const data = await res.json()
      set({ contentSeries: data.series || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  fetchDLQ: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/cron-hub/dlq', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取DLQ失败: ${res.status}`)
      const data = await res.json()
      set({ dlqItems: data.items || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  fetchAccounts: async () => {
    try {
      const res = await fetch('/api/account-pool', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取账号失败: ${res.status}`)
      const data = await res.json()
      set({ accounts: data.accounts || [] })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取账号失败' })
    }
  },

  fetchPersonas: async () => {
    try {
      const res = await fetch('/api/personas', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取Persona失败: ${res.status}`)
      const data = await res.json()
      set({ personas: data.personas || [] })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取Persona失败' })
    }
  },

  fetchPersonaStories: async (personaId: string) => {
    try {
      const res = await fetch(`/api/persona-stories?persona_id=${encodeURIComponent(personaId)}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取Story失败: ${res.status}`)
      const data = await res.json()
      set({ personaStories: data.items || [] })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取Story失败' })
    }
  },

  fetchPersonaStoryNodes: async (storyId: string) => {
    try {
      const res = await fetch(`/api/persona-stories/${storyId}/nodes`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取节点失败: ${res.status}`)
      const data = await res.json()
      return data || []
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取节点失败' })
      return []
    }
  },

  fetchAgents: async () => {
    // ★ v4.0 Agent-First 新增：获取可用 Agent 列表
    try {
      const res = await fetch('/api/agents', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取 Agent 列表失败: ${res.status}`)
      const json = await res.json()
      // 兼容多种响应格式：BaseResponse { code, data }、{ agents: [] }、直接数组
      let agents: Agent[] = []
      if (json && json.code === 'OK' && Array.isArray(json.data)) {
        agents = json.data
      } else if (Array.isArray(json.agents)) {
        agents = json.agents
      } else if (Array.isArray(json)) {
        agents = json
      }
      set({ agents })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取 Agent 列表失败' })
    }
  },

  fetchPlatformSchemas: async () => {
    try {
      const res = await fetch('/api/platform-schemas', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取平台规范失败: ${res.status}`)
      const data = await res.json()
      set({ platformSchemas: data.schemas || [] })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取平台规范失败' })
    }
  },

  createTask: async (data) => {
    set({ isFormLoading: true, error: null })
    try {
      const res = await fetch('/api/task-hub/tasks', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        let detail = ''
        try {
          const errJson = await res.json()
          detail = errJson.message || errJson.detail || JSON.stringify(errJson)
        } catch {
          detail = await res.text().catch(() => '')
        }
        throw new Error(`创建任务失败 (${res.status}${detail ? `: ${detail}` : ''})`)
      }
      await get().fetchTasks()
      set({ isFormLoading: false })
      return true
    } catch (err) {
      set({ isFormLoading: false, error: err instanceof Error ? err.message : '创建失败' })
      return false
    }
  },

  updateTaskStatus: async (id, status) => {
    try {
      const res = await fetch(`/api/task-hub/tasks/${id}/transition`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ status }),
      })
      if (!res.ok) throw new Error('更新状态失败')
      await get().fetchTasks()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新失败' })
      return false
    }
  },

  configureTask: async (id) => {
    try {
      const res = await fetch(`/api/task-hub/tasks/${id}/configure`, {
        method: 'POST',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('配置任务失败')
      await get().fetchTasks()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '配置失败' })
      return false
    }
  },

  startWorkflow: async (id) => {
    try {
      const res = await fetch(`/api/task-hub/tasks/${id}/start-workflow`, {
        method: 'POST',
        headers: authHeaders(),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || `启动工作流失败 (${res.status})`)
      }
      await get().fetchTasks()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '启动工作流失败' })
      return false
    }
  },

  deleteTask: async (id) => {
    try {
      const res = await fetch(`/api/task-hub/tasks/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('删除失败')
      await get().fetchTasks()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },

  retryDLQ: async (id) => {
    try {
      const res = await fetch(`/api/cron-hub/dlq/${id}/retry`, {
        method: 'POST',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('重试失败')
      await get().fetchDLQ()
      await get().fetchTasks()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '重试失败' })
      return false
    }
  },

  discardDLQ: async (id) => {
    try {
      const res = await fetch(`/api/cron-hub/dlq/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('丢弃失败')
      await get().fetchDLQ()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '丢弃失败' })
      return false
    }
  },

  humanDecision: async (id, decision, feedback) => {
    try {
      const res = await fetch(`/api/task-hub/tasks/${id}/human-decision`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ decision, feedback }),
      })
      if (!res.ok) throw new Error('决策提交失败')
      await get().fetchTasks()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '提交失败' })
      return false
    }
  },
}))
