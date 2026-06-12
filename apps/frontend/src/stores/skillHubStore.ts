import { create } from 'zustand'
export interface Skill {
  id: string
  name: string
  description: string
  level: string
  code: string
  tags: string[]
  version: string
  status: string
  created_at: string
  updated_at: string
}

export interface AgentBinding {
  id: string
  agent_id: string
  skill_id: string
  priority: number
  config: Record<string, unknown>
}

interface SkillHubState {
  skills: Skill[]
  bindings: AgentBinding[]
  isLoading: boolean
  error: string | null
  activeLevel: string | null
  activeTab: 'skills' | 'bindings'
  fetchSkills: (level?: string) => Promise<void>
  createSkill: (payload: Partial<Skill>) => Promise<Skill | null>
  bindSkill: (agentId: string, skillId: string, priority: number) => Promise<AgentBinding | null>
  executeSkill: (skillId: string, context: Record<string, unknown>) => Promise<{ success: boolean; result?: unknown; error?: string }>
  setActiveLevel: (level: string | null) => void
  setActiveTab: (tab: 'skills' | 'bindings') => void
  clearError: () => void
}

import { authHeaders } from '../lib/api'

export const useSkillHubStore = create<SkillHubState>((set) => ({
  skills: [],
  bindings: [],
  isLoading: false,
  error: null,
  activeLevel: null,
  activeTab: 'skills',

  fetchSkills: async (level) => {
    set({ isLoading: true, error: null })
    try {
      const url = level ? `/api/skills?level=${level}` : '/api/skills'
      const res = await fetch(url, { headers: authHeaders() })
      if (!res.ok) throw new Error(`Skills: ${res.status}`)
      const data = await res.json()
      set({ skills: data.skills || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载技能失败' })
    }
  },

  createSkill: async (payload) => {
    try {
      const res = await fetch('/api/skills', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`Create: ${res.status}`)
      const skill = await res.json()
      set((s) => ({ skills: [skill, ...s.skills] }))
      return skill
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建技能失败' })
      return null
    }
  },

  bindSkill: async (agentId, skillId, priority) => {
    try {
      const res = await fetch('/api/agent-skills', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ agent_id: agentId, skill_id: skillId, priority }),
      })
      if (!res.ok) throw new Error(`Bind: ${res.status}`)
      const binding = await res.json()
      set((s) => ({ bindings: [binding, ...s.bindings] }))
      return binding
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '绑定失败' })
      return null
    }
  },

  executeSkill: async (skillId, context) => {
    try {
      const res = await fetch(`/api/skills/${skillId}/execute`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ context }),
      })
      if (!res.ok) throw new Error(`Execute: ${res.status}`)
      return await res.json()
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : '执行失败' }
    }
  },

  setActiveLevel: (level) => set({ activeLevel: level }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  clearError: () => set({ error: null }),
}))
