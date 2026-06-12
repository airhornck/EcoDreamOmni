import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface Agent {
  id: string
  name: string
  role: string
  description: string
  skills: string[]
  config: Record<string, unknown>
  status: string
  created_at: string
  updated_at: string
}

export interface WorkflowStep {
  agent_id: string
  name: string
  input_from: string
  output_to: string
}

export interface Workflow {
  id: string
  name: string
  description: string
  steps: WorkflowStep[]
  status: string
  created_at: string
}

export interface Pipeline {
  id: string
  workflow_id: string
  status: string
  current_step: number
  context: Record<string, unknown>
  results: unknown[]
  created_at: string
  updated_at: string
}

interface AgentOrchestraState {
  agents: Agent[]
  workflows: Workflow[]
  pipelines: Pipeline[]
  isLoading: boolean
  error: string | null
  activeTab: 'agents' | 'workflows' | 'pipelines'
  fetchAgents: () => Promise<void>
  createAgent: (payload: Partial<Agent>) => Promise<Agent | null>
  fetchWorkflows: () => Promise<void>
  createWorkflow: (payload: Partial<Workflow>) => Promise<Workflow | null>
  createPipeline: (workflowId: string, context: Record<string, unknown>) => Promise<Pipeline | null>
  updateAgent: (id: string, payload: Partial<Agent>) => Promise<Agent | null>
  deleteAgent: (id: string) => Promise<boolean>
  setActiveTab: (tab: 'agents' | 'workflows' | 'pipelines') => void
  setError: (msg: string | null) => void
  clearError: () => void
}



export const useAgentOrchestraStore = create<AgentOrchestraState>((set) => ({
  agents: [],
  workflows: [],
  pipelines: [],
  isLoading: false,
  error: null,
  activeTab: 'agents',

  fetchAgents: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/agents', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Agents: ${res.status}`)
      const data = await res.json()
      set({ agents: data.agents || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载 Agent 失败' })
    }
  },

  createAgent: async (payload) => {
    try {
      const res = await fetch('/agents', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`Create: ${res.status}`)
      const agent = await res.json()
      set((s) => ({ agents: [agent, ...s.agents] }))
      return agent
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建 Agent 失败' })
      return null
    }
  },

  fetchWorkflows: async () => {
    try {
      const res = await fetch('/api/workflows', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Workflows: ${res.status}`)
      const data = await res.json()
      set({ workflows: data.workflows || [] })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '加载工作流失败' })
    }
  },

  createWorkflow: async (payload) => {
    try {
      const res = await fetch('/api/workflows', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`CreateWF: ${res.status}`)
      const wf = await res.json()
      set((s) => ({ workflows: [wf, ...s.workflows] }))
      return wf
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建工作流失败' })
      return null
    }
  },

  createPipeline: async (workflowId, context) => {
    try {
      const res = await fetch('/api/pipelines', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ workflow_id: workflowId, context }),
      })
      if (!res.ok) throw new Error(`Pipeline: ${res.status}`)
      const pipe = await res.json()
      set((s) => ({ pipelines: [pipe, ...s.pipelines] }))
      return pipe
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '执行流水线失败' })
      return null
    }
  },

  updateAgent: async (id, payload) => {
    try {
      const res = await fetch(`/agents/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`Update: ${res.status}`)
      const agent = await res.json()
      set((s) => ({
        agents: s.agents.map((a) => (a.id === id ? agent : a)),
      }))
      return agent
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新 Agent 失败' })
      return null
    }
  },

  deleteAgent: async (id) => {
    try {
      const res = await fetch(`/agents/${id}`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`Delete: ${res.status}`)
      set((s) => ({
        agents: s.agents.filter((a) => a.id !== id),
      }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除 Agent 失败' })
      return false
    }
  },

  setActiveTab: (tab) => set({ activeTab: tab }),
  setError: (msg) => set({ error: msg }),
  clearError: () => set({ error: null }),
}))
