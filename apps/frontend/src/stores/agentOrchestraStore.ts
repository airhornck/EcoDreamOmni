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

interface AgentOrchestraState {
  agents: Agent[]
  isLoading: boolean
  error: string | null
  fetchAgents: () => Promise<void>
  createAgent: (payload: Partial<Agent>) => Promise<Agent | null>
  updateAgent: (id: string, payload: Partial<Agent>) => Promise<Agent | null>
  deleteAgent: (id: string) => Promise<boolean>
  setError: (msg: string | null) => void
  clearError: () => void
}

export const useAgentOrchestraStore = create<AgentOrchestraState>((set) => ({
  agents: [],
  isLoading: false,
  error: null,

  fetchAgents: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/agent-orchestra/agents', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Agents: ${res.status}`)
      const data = await res.json()
      set({ agents: data.agents || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载 Agent 失败' })
    }
  },

  createAgent: async (payload) => {
    try {
      const res = await fetch('/api/agent-orchestra/agents', {
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

  updateAgent: async (id, payload) => {
    try {
      const res = await fetch(`/api/agent-orchestra/agents/${id}`, {
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
      const res = await fetch(`/api/agent-orchestra/agents/${id}`, {
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

  setError: (msg) => set({ error: msg }),
  clearError: () => set({ error: null }),
}))
