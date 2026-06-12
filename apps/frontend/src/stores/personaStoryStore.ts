import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface StoryNode {
  id: string
  story_id: string
  sequence_index: number
  theme: string
  emotion_tone: 'low' | 'medium' | 'high' | 'burst'
  key_event: string
  prev_recap?: string | null
  next_teaser?: string | null
  content_draft_id?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface PersonaStory {
  id: string
  persona_id: string
  name: string
  description?: string | null
  emotion_curve_template: string
  status: 'draft' | 'active' | 'completed' | 'archived'
  nodes_count?: number
  created_at?: string | null
  updated_at?: string | null
}

export interface StoryContext {
  current_node?: StoryNode | null
  prev_node_summary: string
  next_node_teaser: string
  series_theme: string
  emotional_arc: string
}

interface PersonaStoryState {
  stories: PersonaStory[]
  nodes: StoryNode[]
  currentStory: PersonaStory | null
  storyContext: StoryContext | null
  isLoading: boolean
  error: string | null
  fetchStories: (persona_id?: string, status?: string) => Promise<void>
  fetchStory: (storyId: string) => Promise<PersonaStory | null>
  createStory: (data: Partial<PersonaStory>) => Promise<PersonaStory | null>
  updateStory: (id: string, data: Partial<PersonaStory>) => Promise<boolean>
  deleteStory: (id: string) => Promise<boolean>
  cloneStory: (id: string, newName: string) => Promise<PersonaStory | null>
  updateStoryStatus: (id: string, status: PersonaStory['status']) => Promise<boolean>
  fetchNodes: (storyId: string) => Promise<void>
  createNode: (storyId: string, data: Partial<StoryNode>) => Promise<StoryNode | null>
  updateNode: (nodeId: string, data: Partial<StoryNode>) => Promise<boolean>
  deleteNode: (nodeId: string) => Promise<boolean>
  reorderNodes: (storyId: string, nodeOrder: string[]) => Promise<boolean>
  fetchStoryContext: (storyId: string, currentNodeIndex?: number) => Promise<StoryContext | null>
  bindContentToNode: (nodeId: string, contentDraftId: string) => Promise<boolean>
  clearError: () => void
}

export const usePersonaStoryStore = create<PersonaStoryState>((set) => ({
  stories: [],
  nodes: [],
  currentStory: null,
  storyContext: null,
  isLoading: false,
  error: null,

  fetchStories: async (persona_id, status) => {
    set({ isLoading: true, error: null })
    try {
      const params = new URLSearchParams()
      if (persona_id) params.append('persona_id', persona_id)
      if (status) params.append('status', status)
      const url = `/api/persona-stories${params.toString() ? '?' + params.toString() : ''}`
      const res = await fetch(url, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取剧本列表失败: ${res.status}`)
      const data = await res.json()
      set({ stories: data.items || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载失败' })
    }
  },

  fetchStory: async (storyId) => {
    try {
      const res = await fetch(`/api/persona-stories/${storyId}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取剧本详情失败: ${res.status}`)
      const story = await res.json()
      set({ currentStory: story })
      return story
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '加载失败' })
      return null
    }
  },

  createStory: async (payload) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/persona-stories', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`创建剧本失败: ${res.status}`)
      const story = await res.json()
      set((s) => ({ stories: [story, ...s.stories], isLoading: false }))
      return story
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '创建失败' })
      return null
    }
  },

  updateStory: async (id, payload) => {
    try {
      const res = await fetch(`/api/persona-stories/${id}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`更新剧本失败: ${res.status}`)
      const updated = await res.json()
      set((s) => ({
        stories: s.stories.map((st) => (st.id === id ? updated : st)),
        currentStory: s.currentStory?.id === id ? updated : s.currentStory,
      }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新失败' })
      return false
    }
  },

  deleteStory: async (id) => {
    try {
      const res = await fetch(`/api/persona-stories/${id}`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`删除剧本失败: ${res.status}`)
      set((s) => ({
        stories: s.stories.filter((st) => st.id !== id),
        currentStory: s.currentStory?.id === id ? null : s.currentStory,
      }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },

  cloneStory: async (id, newName) => {
    try {
      const res = await fetch(`/api/persona-stories/${id}/clone`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ new_name: newName }),
      })
      if (!res.ok) throw new Error(`克隆剧本失败: ${res.status}`)
      const story = await res.json()
      set((s) => ({ stories: [story, ...s.stories] }))
      return story
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '克隆失败' })
      return null
    }
  },

  updateStoryStatus: async (id, status) => {
    try {
      const res = await fetch(`/api/persona-stories/${id}/status`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify({ status }),
      })
      if (!res.ok) throw new Error(`更新状态失败: ${res.status}`)
      const updated = await res.json()
      set((s) => ({
        stories: s.stories.map((st) => (st.id === id ? updated : st)),
        currentStory: s.currentStory?.id === id ? updated : s.currentStory,
      }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新状态失败' })
      return false
    }
  },

  fetchNodes: async (storyId) => {
    try {
      const res = await fetch(`/api/persona-stories/${storyId}/nodes`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取节点列表失败: ${res.status}`)
      const data = await res.json()
      set({ nodes: data || [] })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '加载节点失败' })
    }
  },

  createNode: async (storyId, payload) => {
    try {
      const res = await fetch(`/api/persona-stories/${storyId}/nodes`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`创建节点失败: ${res.status}`)
      const node = await res.json()
      set((s) => ({ nodes: [...s.nodes, node] }))
      return node
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建节点失败' })
      return null
    }
  },

  updateNode: async (nodeId, payload) => {
    try {
      const res = await fetch(`/api/persona-stories/story-nodes/${nodeId}`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`更新节点失败: ${res.status}`)
      const updated = await res.json()
      set((s) => ({
        nodes: s.nodes.map((n) => (n.id === nodeId ? updated : n)),
      }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新节点失败' })
      return false
    }
  },

  deleteNode: async (nodeId) => {
    try {
      const res = await fetch(`/api/persona-stories/story-nodes/${nodeId}`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`删除节点失败: ${res.status}`)
      set((s) => ({ nodes: s.nodes.filter((n) => n.id !== nodeId) }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除节点失败' })
      return false
    }
  },

  reorderNodes: async (storyId, nodeOrder) => {
    try {
      const res = await fetch(`/api/persona-stories/${storyId}/nodes/reorder`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ node_order: nodeOrder }),
      })
      if (!res.ok) throw new Error(`重排节点失败: ${res.status}`)
      const data = await res.json()
      set({ nodes: data || [] })
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '重排节点失败' })
      return false
    }
  },

  fetchStoryContext: async (storyId, currentNodeIndex) => {
    try {
      const params = currentNodeIndex !== undefined ? `?current_node_index=${currentNodeIndex}` : ''
      const res = await fetch(`/api/persona-stories/${storyId}/context${params}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取剧本上下文失败: ${res.status}`)
      const context = await res.json()
      set({ storyContext: context })
      return context
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '加载上下文失败' })
      return null
    }
  },

  bindContentToNode: async (nodeId, contentDraftId) => {
    try {
      const res = await fetch(`/api/story-nodes/${nodeId}/bind-content`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ content_draft_id: contentDraftId }),
      })
      if (!res.ok) throw new Error(`绑定内容失败: ${res.status}`)
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '绑定内容失败' })
      return false
    }
  },

  clearError: () => set({ error: null }),
}))
