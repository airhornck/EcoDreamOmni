import { create } from 'zustand'
import { authHeaders } from '../lib/api'

/* ── Types ── */

export interface ContentDraft {
  id: string
  title: string
  content_type: string
  platform: string
  account_id: string
  body: string
  tags: string[]
  status: string
  cover_image_url?: string
  created_at: string
  updated_at: string
}

export interface Persona {
  id: string
  nickname: string
  pet_type: string
  avatar_url?: string
}

export interface PersonaStory {
  id: string
  title: string
  status: string
}

export interface StoryNode {
  id: string
  title: string
  theme: string
  mood: string
}

export interface ContentSeries {
  id: string
  name: string
}

export interface LLMModel {
  id: string
  name: string
  provider: string
}

export interface GenerateRequest {
  topic: string
  platform: string
  tone?: string
  length?: string
  persona_id?: string
  story_id?: string
  node_id?: string
  series_id?: string
  model_id?: string
  temperature?: number
}

export interface ScoreBreakdown {
  title_attractiveness: number
  body_completeness: number
  tag_relevance: number
  cover_quality: number
  overall: number
}

export interface TokenUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  estimated_cost_cny: number
}

export interface InjectionContext {
  brand_knowledge?: { title: string; source: string }[]
  persona_story?: {
    current_node_theme: string
    previous_recap: string
    mood: string
    next_preview: string
  }
  platform_rules?: string[]
}

export interface GeneratedContent {
  title: string
  body: string
  tags: string[]
  platform: string
  cover_image_url?: string
  scores?: ScoreBreakdown
  tokens?: TokenUsage
  duration_ms?: number
  injection_context?: InjectionContext
}

/* ── State ── */

interface ContentForgeState {
  drafts: ContentDraft[]
  generated: GeneratedContent | null
  isLoading: boolean
  isGenerating: boolean
  error: string | null

  personas: Persona[]
  stories: PersonaStory[]
  storyNodes: StoryNode[]
  contentSeries: ContentSeries[]
  llmModels: LLMModel[]

  fetchDrafts: () => Promise<void>
  createDraft: (data: Partial<ContentDraft>) => Promise<ContentDraft | null>
  updateDraft: (id: string, data: Partial<ContentDraft>) => Promise<boolean>
  deleteDraft: (id: string) => Promise<boolean>
  submitForReview: (id: string, personaId?: string, workflowTemplateId?: string) => Promise<boolean>

  fetchPersonas: () => Promise<void>
  fetchStories: () => Promise<void>
  fetchStoryNodes: (storyId: string) => Promise<void>
  fetchContentSeries: () => Promise<void>
  fetchLLMModels: () => Promise<void>

  generateContent: (params: GenerateRequest) => Promise<GeneratedContent | null>
  clearGenerated: () => void
  clearError: () => void
}

/* ── Backend types ── */

interface BackendPersona {
  id: string
  nickname?: string
  name?: string
  pet_type?: string
  pet_profile?: { pet_type?: string }
  avatar_url?: string
}

interface BackendStory {
  id: string
  title?: string
  name?: string
  status: string
}

interface BackendNode {
  id: string
  title?: string
  theme?: string
  mood?: string
  emotion_tone?: string
}

interface BackendSeries {
  id: string
  name?: string
}

interface BackendModel {
  id: string
  name?: string
  model_name?: string
  provider?: string
}

/* ── Store ── */

export const useContentForgeStore = create<ContentForgeState>((set, get) => ({
  drafts: [],
  generated: null,
  isLoading: false,
  isGenerating: false,
  error: null,

  personas: [],
  stories: [],
  storyNodes: [],
  contentSeries: [],
  llmModels: [],

  fetchDrafts: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/content-drafts', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取草稿列表失败: ${res.status}`)
      const data = await res.json()
      set({ drafts: data.drafts || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  createDraft: async (data) => {
    try {
      const res = await fetch('/api/content-drafts', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('创建草稿失败')
      const draft = await res.json()
      await get().fetchDrafts()
      return draft
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败' })
      return null
    }
  },

  updateDraft: async (id, data) => {
    try {
      const res = await fetch(`/api/content-drafts/${id}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('更新草稿失败')
      await get().fetchDrafts()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新失败' })
      return false
    }
  },

  deleteDraft: async (id) => {
    try {
      const res = await fetch(`/api/content-drafts/${id}`, {
        method: 'DELETE',
        headers: authHeaders(false),
      })
      if (!res.ok) throw new Error('删除草稿失败')
      await get().fetchDrafts()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除失败' })
      return false
    }
  },

  submitForReview: async (id, personaId?: string, workflowTemplateId?: string) => {
    try {
      const params = new URLSearchParams()
      if (personaId) params.append('persona_id', personaId)
      if (workflowTemplateId) params.append('workflow_template_id', workflowTemplateId)
      const query = params.toString() ? `?${params.toString()}` : ''
      const res = await fetch(`/api/content-drafts/${id}/submit-for-review${query}`, {
        method: 'POST',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('提交审核失败')
      await get().fetchDrafts()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '提交审核失败' })
      return false
    }
  },

  fetchPersonas: async () => {
    try {
      const res = await fetch('/api/personas', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取人设列表失败')
      const data = await res.json()
      const items = data.items || data.personas || []
      // 后端可能返回 name，前端需要 nickname；后端 pet_profile.pet_type 映射为 pet_type
      set({ personas: items.map((p: BackendPersona) => ({
        id: p.id,
        nickname: p.nickname || p.name || '未命名',
        pet_type: p.pet_type || p.pet_profile?.pet_type || '',
        avatar_url: p.avatar_url,
      })) })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取人设列表失败' })
    }
  },

  fetchStories: async () => {
    try {
      const res = await fetch('/api/persona-stories?status=active', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取剧本列表失败')
      const data = await res.json()
      const items = data.items || data.stories || []
      // 后端返回 name，前端需要 title
      set({ stories: items.map((s: BackendStory) => ({
        id: s.id,
        title: s.title || s.name || '未命名',
        status: s.status,
      })) })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取剧本列表失败' })
    }
  },

  fetchStoryNodes: async (storyId: string) => {
    try {
      const res = await fetch(`/api/persona-stories/${storyId}/nodes`, { headers: authHeaders() })
      if (!res.ok) throw new Error('获取节点列表失败')
      const data = await res.json()
      // 后端可能直接返回数组
      const items = Array.isArray(data) ? data : (data.items || data.nodes || [])
      // 后端返回 theme/emotion_tone，前端需要 title/mood
      set({ storyNodes: items.map((n: BackendNode) => ({
        id: n.id,
        title: n.title || n.theme || '未命名',
        theme: n.theme || '',
        mood: n.mood || n.emotion_tone || '',
      })) })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取节点列表失败' })
    }
  },

  fetchContentSeries: async () => {
    try {
      const res = await fetch('/api/content-series', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取系列列表失败')
      const data = await res.json()
      const items = data.items || data.series || []
      set({ contentSeries: items.map((s: BackendSeries) => ({
        id: s.id,
        name: s.name || '未命名',
      })) })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取系列列表失败' })
    }
  },

  fetchLLMModels: async () => {
    try {
      const res = await fetch('/api/llm-hub/models?status=active', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取模型列表失败')
      const data = await res.json()
      // 后端可能直接返回数组或 {items: [...]}
      const items = Array.isArray(data) ? data : (data.items || data.models || [])
      // 后端返回 model_name，前端需要 name
      set({ llmModels: items.map((m: BackendModel) => ({
        id: m.id,
        name: m.name || m.model_name || '未命名',
        provider: m.provider || 'unknown',
      })) })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取模型列表失败' })
    }
  },

  generateContent: async (params) => {
    set({ isGenerating: true, error: null })
    const start = Date.now()
    try {
      const res = await fetch('/api/content-generate', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(params),
      })
      if (!res.ok) throw new Error('生成内容失败')
      const data: GeneratedContent = await res.json()
      const duration = Date.now() - start
      set({ generated: { ...data, duration_ms: data.duration_ms ?? duration }, isGenerating: false })
      return data
    } catch (err) {
      set({ isGenerating: false, error: err instanceof Error ? err.message : '生成失败' })
      return null
    }
  },

  clearGenerated: () => set({ generated: null }),
  clearError: () => set({ error: null }),
}))
