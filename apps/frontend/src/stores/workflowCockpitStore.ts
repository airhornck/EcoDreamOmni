import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface WfTask {
  id: string
  name: string
  status: string
  account_id: string
  workflow_template_id: string
  priority: number
  current_node_index: number
  created_at: string
}

export interface WfTemplate {
  id: string
  name: string
  description: string
  status: string
  nodes: Array<{
    node_index: number
    node_type: string
    node_name: string
    agent_id?: string
    fail_strategy?: string
  }>
}

export interface WfExecution {
  id: string
  task_id: string
  template_id: string
  status: string
  current_node_index: number
  context: Record<string, unknown>
  started_at: string | null
  ended_at: string | null
}

interface WorkflowCockpitState {
  tasks: WfTask[]
  templates: WfTemplate[]
  executions: WfExecution[]
  isLoading: boolean
  error: string | null
  activeTab: 'kanban' | 'templates' | 'executions'
  fetchTasks: () => Promise<void>
  fetchTemplates: () => Promise<void>
  fetchExecutions: () => Promise<void>
  startExecution: (templateId: string, taskId: string) => Promise<boolean>
  executeNext: (executionId: string) => Promise<boolean>
  transitionTask: (taskId: string, status: string) => Promise<boolean>
  setActiveTab: (tab: 'kanban' | 'templates' | 'executions') => void
  clearError: () => void
}

export const useWorkflowCockpitStore = create<WorkflowCockpitState>((set) => ({
  tasks: [],
  templates: [],
  executions: [],
  isLoading: false,
  error: null,
  activeTab: 'kanban',

  fetchTasks: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/task-hub/tasks', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Tasks: ${res.status}`)
      const data = await res.json()
      set({ tasks: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载任务失败' })
    }
  },

  fetchTemplates: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/workflow-engine/templates', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Templates: ${res.status}`)
      const data = await res.json()
      set({ templates: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载模板失败' })
    }
  },

  fetchExecutions: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/workflow-engine/executions', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Executions: ${res.status}`)
      const data = await res.json()
      set({ executions: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载执行记录失败' })
    }
  },

  startExecution: async (templateId, taskId) => {
    try {
      const res = await fetch(`/api/workflow-engine/templates/${templateId}/executions`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ task_id: taskId }),
      })
      if (!res.ok) throw new Error(`Start: ${res.status}`)
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '启动执行失败' })
      return false
    }
  },

  executeNext: async (executionId) => {
    try {
      const res = await fetch(`/api/workflow-engine/executions/${executionId}/next`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({}),
      })
      if (!res.ok) throw new Error(`Next: ${res.status}`)
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '执行下一步失败' })
      return false
    }
  },

  transitionTask: async (taskId, status) => {
    try {
      const res = await fetch(`/api/task-hub/tasks/${taskId}/transition`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ status }),
      })
      if (!res.ok) throw new Error(`Transition: ${res.status}`)
      const updated = await res.json()
      set((s) => ({
        tasks: s.tasks.map((t) => (t.id === taskId ? { ...t, ...updated } : t)),
      }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '状态转换失败' })
      return false
    }
  },

  setActiveTab: (tab) => set({ activeTab: tab }),
  clearError: () => set({ error: null }),
}))
