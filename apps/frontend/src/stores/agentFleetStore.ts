import { create } from 'zustand'
import { apiClient } from '../lib/api'
import type { Agent } from '../types/api'

interface AgentFleetState {
  agents: Agent[]
  isLoading: boolean
  error: string | null
  selectedAgentId: string | null

  fetchAgents: () => Promise<void>
  selectAgent: (id: string | null) => void
  clearError: () => void
}

export const useAgentFleetStore = create<AgentFleetState>((set) => ({
  agents: [],
  isLoading: false,
  error: null,
  selectedAgentId: null,

  fetchAgents: async () => {
    set({ isLoading: true, error: null })
    try {
      // /api/agents 默认返回 ACTIVE 状态 Agent（与 TaskHub Step3 一致）
      const agents = await apiClient<Agent[]>('/agents')
      set({ agents: agents || [], isLoading: false })
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : '加载 Agent 列表失败',
      })
    }
  },

  selectAgent: (id) => set({ selectedAgentId: id }),

  clearError: () => set({ error: null }),
}))
