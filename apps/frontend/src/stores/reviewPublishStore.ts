import { create } from 'zustand'
import { apiClient } from '../lib/api'
import {
  mockFetchConclusions,
  mockFetchDetail,
  mockDecideTask,
  mockUpdateContent,
  mockConfirmPublish,
  mockRegenerate,
} from '../lib/mockReview'
import {
  mockGenerateCover,
  mockGetCoverStatus,
  mockCopilotContext,
  mockGetActionCards,
  mockExecuteAction,
} from '../lib/mockCopilot'

// ───────────────────────────────────────────────
// Feature Flag: use mock APIs during backend Sprint 1/2
// ───────────────────────────────────────────────
const USE_MOCK = false // Backend is ready — using real API

// ───────────────────────────────────────────────
// Types
// ───────────────────────────────────────────────

export interface ReviewConclusion {
  task_id: string
  task_name: string
  content_title: string | null
  platform: string
  account_name: string
  status: string
  review_decision: string | null
  reviewed_at: string | null
  reviewer: string | null
  review_reason: string | null
  content_preview: string
  waiting_since: string
  priority: number
  risk_level: string
  can_publish_now: boolean
  has_cron_job: boolean
  compliance_score?: number
  quality_score?: number
  cover_image_url?: string | null
}

export interface GeneratedContent {
  title: string
  body: string
  tags: string[]
  platform: string
  content_type: string
  content_format?: string
  cover_image_url?: string
  cover_image_ratio?: string
  images?: string[]
}

export interface TopicReport {
  report_id: string
  selected_topic: string
  topics: Array<{
    id: string
    title: string
    source_report: string
    estimated_engagement: number
    tags: string[]
    status: string
  }>
  '5a_stage': string
  audience_fit_score: number
}

export interface CopilotContext {
  recommended_action: string
  confidence: number
  reasoning: string
  risk_factors: string[]
  suggested_improvements: string[]
}

export interface ReviewDetail {
  task_id: string
  task_name: string
  platform: string
  status: string
  content_preview: string
  generated_content: GeneratedContent | null
  agent_summary: string
  compliance_result: Record<string, unknown>
  prediction_result: Record<string, unknown>
  quality_score: Record<string, unknown>
  injection_context: Record<string, unknown>
  topic_report: TopicReport | null
  cover_image_url: string | null
  review_history: Array<{
    reviewer: string
    decision: string
    reason: string | null
    publish_mode: string | null
    scheduled_at: string | null
    created_at: string
  }>
  risk_level: string
  can_publish: boolean
  has_primary_approval?: boolean
  account_id: string
  account_name: string
  draft_id: string | null
  cron_schedule?: string | null
  copilot_context?: CopilotContext
  available_copilot_cards?: string[]
}

export interface CoverGenerationResult {
  url: string
  thumbnail_url: string
  ratio: string
  prompt_used: string
  seed: number
}

// ───────────────────────────────────────────────
// Store State
// ───────────────────────────────────────────────

interface ReviewPublishState {
  // Data
  conclusions: ReviewConclusion[]
  currentDetail: ReviewDetail | null
  selectedTaskId: string | null
  copilotSummary: {
    total_pending: number
    recommended_priority: string[]
    batch_suggestion: string
  } | null

  // UI State
  isLoading: boolean
  isDeciding: boolean
  isGeneratingCover: boolean
  error: string | null
  activeTab: 'all' | 'pending' | 'approved' | 'rejected' | 'revised'

  // Actions
  clearError: () => void
  setActiveTab: (tab: ReviewPublishState['activeTab']) => void
  selectTask: (taskId: string | null) => void

  // API Actions
  fetchConclusions: (status_filter?: string) => Promise<void>
  fetchDetail: (taskId: string) => Promise<void>
  decideTask: (
    taskId: string,
    decision: 'approve' | 'reject' | 'revise',
    reason?: string,
  ) => Promise<{ success: boolean; status?: string; copilot_followup?: unknown }>
  updateContent: (
    taskId: string,
    patch: { title?: string; body?: string; tags?: string[]; cover_image_url?: string },
  ) => Promise<{ success: boolean; updated_at?: string }>
  confirmPublish: (
    taskId: string,
    config: {
      operator?: string
      publish_mode: string
      scheduled_at?: string
      cron_schedule?: string
    },
  ) => Promise<{ success: boolean; cron_job_id?: string; publish_task_id?: string }>
  regenerateContent: (taskId: string) => Promise<{ success: boolean; status?: string; message?: string }>

  // Copilot Actions
  generateCover: (payload: {
    task_id: string
    prompt?: string
    auto_prompt?: boolean
    style_preset?: string
    count?: number
    ratio?: string
  }) => Promise<{ job_id: string; status: string; estimated_seconds: number }>
  getCoverStatus: (jobId: string) => Promise<{
    job_id: string
    status: string
    results?: CoverGenerationResult[]
    completed_at?: string
    error_message?: string
  }>
  reportCopilotContext: (payload: {
    session_id: string
    page: string
    selected_items: string[]
    selected_content?: Record<string, unknown>
    workspace_state?: Record<string, unknown>
  }) => Promise<unknown>
  fetchActionCards: (page: string, taskId?: string) => Promise<{ cards: unknown[] }>
  executeCopilotAction: (payload: {
    card_id: string
    action_id: string
    inputs?: Record<string, unknown>
    payload?: Record<string, unknown>
  }) => Promise<unknown>
}

// ───────────────────────────────────────────────
// Store Implementation
// ───────────────────────────────────────────────

export const useReviewPublishStore = create<ReviewPublishState>((set) => ({
  conclusions: [],
  currentDetail: null,
  selectedTaskId: null,
  copilotSummary: null,
  isLoading: false,
  isDeciding: false,
  isGeneratingCover: false,
  error: null,
  activeTab: 'all',

  clearError: () => set({ error: null }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  selectTask: (taskId) => set({ selectedTaskId: taskId }),

  // ─── Fetch Conclusions ───
  fetchConclusions: async (status_filter) => {
    set({ isLoading: true, error: null })
    try {
      let data: { items: ReviewConclusion[]; copilot_summary?: ReviewPublishState['copilotSummary'] }

      if (USE_MOCK) {
        data = await mockFetchConclusions(status_filter)
      } else {
        const url = status_filter
          ? `/api/review-publish-center/conclusions?status_filter=${status_filter}`
          : '/api/review-publish-center/conclusions'
        data = await apiClient<{ items: ReviewConclusion[]; copilot_summary?: ReviewPublishState['copilotSummary'] }>(url)
      }

      set({
        conclusions: data.items || [],
        copilotSummary: data.copilot_summary || null,
        isLoading: false,
      })
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : '加载失败',
      })
    }
  },

  // ─── Fetch Detail ───
  fetchDetail: async (taskId) => {
    set({ isLoading: true, error: null })
    try {
      const data = USE_MOCK
        ? await mockFetchDetail(taskId)
        : await apiClient<ReviewDetail>(`/api/review-publish-center/conclusions/${taskId}`)
      set({ currentDetail: data, isLoading: false })
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : '加载详情失败',
      })
    }
  },

  // ─── Decide Task ───
  decideTask: async (taskId, decision, reason) => {
    set({ isDeciding: true, error: null })
    try {
      const result = USE_MOCK
        ? await mockDecideTask(taskId, decision, reason)
        : await apiClient<{ success: boolean; status?: string; copilot_followup?: unknown }>(`/api/human-in-the-loop/tasks/${taskId}/${decision}`, {
            method: 'POST',
            body: JSON.stringify({ reason, copilot_suggested: true }),
          })

      // Update local state if successful
      if (result.success) {
        set((state) => ({
          currentDetail: state.currentDetail
            ? { ...state.currentDetail, status: result.status || state.currentDetail.status }
            : null,
          conclusions: state.conclusions.map((c) =>
            c.task_id === taskId ? { ...c, status: result.status || c.status, review_decision: decision.toUpperCase() } : c,
          ),
        }))
      }

      set({ isDeciding: false })
      return result
    } catch (err) {
      set({ isDeciding: false, error: err instanceof Error ? err.message : '审核操作失败' })
      return { success: false }
    }
  },

  // ─── Update Content ───
  updateContent: async (taskId, patch) => {
    try {
      const result = USE_MOCK
        ? await mockUpdateContent(taskId, patch)
        : await apiClient<{ success: boolean; updated_at?: string }>(`/api/review-publish-center/conclusions/${taskId}/content`, {
            method: 'PUT',
            body: JSON.stringify(patch),
          })
      return result
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '更新内容失败' })
      return { success: false }
    }
  },

  // ─── Confirm Publish ───
  confirmPublish: async (taskId, config) => {
    try {
      const result = USE_MOCK
        ? await mockConfirmPublish(taskId, config)
        : await apiClient<{ success: boolean; cron_job_id?: string; publish_task_id?: string }>(`/api/review-publish-center/conclusions/${taskId}/confirm-publish`, {
            method: 'POST',
            body: JSON.stringify(config),
          })
      return result
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '确认发布失败' })
      return { success: false }
    }
  },

  // ─── Regenerate Content ───
  regenerateContent: async (taskId) => {
    try {
      const result = USE_MOCK
        ? await mockRegenerate(taskId)
        : await apiClient<{ success: boolean; status?: string; message?: string }>(`/api/review-publish-center/conclusions/${taskId}/regenerate`, {
            method: 'POST',
          })
      return result
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '重新生成失败' })
      return { success: false }
    }
  },

  // ─── Generate Cover ───
  generateCover: async (payload) => {
    set({ isGeneratingCover: true, error: null })
    try {
      const result = USE_MOCK
        ? await mockGenerateCover(payload)
        : await apiClient<{ job_id: string; status: string; estimated_seconds: number }>('/api/ai/generate-cover', {
            method: 'POST',
            body: JSON.stringify(payload),
          })
      set({ isGeneratingCover: false })
      return result
    } catch (err) {
      set({ isGeneratingCover: false, error: err instanceof Error ? err.message : '封面生成失败' })
      throw err
    }
  },

  // ─── Get Cover Status ───
  getCoverStatus: async (jobId) => {
    try {
      return USE_MOCK
        ? await mockGetCoverStatus(jobId)
        : await apiClient<{ job_id: string; status: string; progress: number; result?: { urls: string[] } }>(`/api/ai/generate-cover/${jobId}`)
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '查询封面状态失败' })
      throw err
    }
  },

  // ─── Copilot Context ───
  reportCopilotContext: async (payload) => {
    try {
      return USE_MOCK
        ? await mockCopilotContext(payload)
        : await apiClient<{ context_id: string; suggested_cards?: unknown[] }>('/api/ai/copilot/context', {
            method: 'POST',
            body: JSON.stringify(payload),
          })
    } catch (err) {
      // Silently fail — Copilot context is best-effort
      console.warn('Copilot context update failed:', err)
      return null
    }
  },

  // ─── Fetch Action Cards ───
  fetchActionCards: async (page, taskId) => {
    try {
      return USE_MOCK
        ? await mockGetActionCards(page, taskId)
        : await apiClient<{ cards: unknown[] }>(`/api/ai/copilot/action-cards?page=${page}${taskId ? `&task_id=${taskId}` : ''}`)
    } catch (err) {
      console.warn('Action cards fetch failed:', err)
      return { cards: [] }
    }
  },

  // ─── Execute Copilot Action ───
  executeCopilotAction: async (payload) => {
    try {
      return USE_MOCK
        ? await mockExecuteAction(payload)
        : await apiClient<unknown>('/api/ai/copilot/agent', {
            method: 'POST',
            body: JSON.stringify({ ...payload, context: {} }),
          })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '执行失败' })
      throw err
    }
  },
}))
