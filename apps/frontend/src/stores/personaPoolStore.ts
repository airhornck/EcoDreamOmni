import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface Persona {
  id: string
  name: string
  voice_style: string
  target_platforms: string[]
  created_at: string
}

interface PersonaPoolState {
  personas: Persona[]
  isLoading: boolean
  error: string | null
  fetchPersonas: () => Promise<void>
  createPersona: (data: Partial<Persona>) => Promise<boolean>
  deletePersona: (id: string) => Promise<boolean>
}

export const usePersonaPoolStore = create<PersonaPoolState>((set, get) => ({
  personas: [],
  isLoading: false,
  error: null,

  fetchPersonas: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/personas', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取人设列表失败: ${res.status}`)
      const data = await res.json()
      set({ personas: data.personas || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  createPersona: async (data) => {
    try {
      const res = await fetch('/api/personas', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('创建失败')
      await get().fetchPersonas()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败' })
      return false
    }
  },

  deletePersona: async (id) => {
    try {
      const res = await fetch(`/api/personas/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('删除失败')
      await get().fetchPersonas()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },
}))
