import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface PublishTask {
  id: string
  draft_id: string
  account_id: string
  platform: string
  status: string
  scheduled_at?: string
  published_at?: string
  published_url?: string
  error_reason?: string
  retry_count: number
  created_at: string
  draft_title?: string
  account_name?: string
  body?: string
  cover_image_url?: string
  tags?: string[]
}

export interface DraftOption {
  id: string
  title: string
  body?: string
  cover_image_url?: string
  tags?: string[]
}

export interface AccountOption {
  id: string
  username: string
  platform: string
}

export interface PublishStats {
  todayPublished: number
  pendingCount: number
  successRate7d: number
  failedRetryCount: number
}

interface PublisherState {
  tasks: PublishTask[]
  drafts: DraftOption[]
  accounts: AccountOption[]
  stats: PublishStats
  isLoading: boolean
  isFormLoading: boolean
  error: string | null
  fetchTasks: () => Promise<void>
  fetchDrafts: () => Promise<void>
  fetchAccounts: () => Promise<void>
  computeStats: () => void
  createTask: (data: Partial<PublishTask>) => Promise<boolean>
  executeTask: (id: string) => Promise<boolean>
  retryTask: (id: string) => Promise<boolean>
  deleteTask: (id: string) => Promise<boolean>
}

function formatDateKey(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export const usePublisherStore = create<PublisherState>((set, get) => ({
  tasks: [],
  drafts: [],
  accounts: [],
  stats: { todayPublished: 0, pendingCount: 0, successRate7d: 0, failedRetryCount: 0 },
  isLoading: false,
  isFormLoading: false,
  error: null,

  fetchTasks: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/publish-tasks', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取发布任务失败: ${res.status}`)
      const data = await res.json()
      const tasks = data.tasks || []
      set({ tasks, isLoading: false })
      get().computeStats()
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  fetchDrafts: async () => {
    try {
      const res = await fetch('/api/content-drafts?status=approved', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取草稿列表失败: ${res.status}`)
      const data = await res.json()
      set({ drafts: data.drafts || [] })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取草稿列表失败' })
    }
  },

  fetchAccounts: async () => {
    try {
      const res = await fetch('/api/account-pool', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取账号列表失败: ${res.status}`)
      const data = await res.json()
      set({ accounts: data.accounts || [] })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取账号列表失败' })
    }
  },

  computeStats: () => {
    const tasks = get().tasks
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const todayKey = formatDateKey(today)

    const todayPublished = tasks.filter((t) => {
      if (!t.published_at) return false
      return formatDateKey(new Date(t.published_at)) === todayKey
    }).length

    const pendingCount = tasks.filter((t) => ['pending', 'scheduled'].includes(t.status)).length

    const sevenDaysAgo = new Date(today)
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 6)
    const sevenDaysAgoKey = formatDateKey(sevenDaysAgo)

    const recentFinished = tasks.filter((t) => {
      if (t.status !== 'published' && t.status !== 'failed') return false
      const dateStr = t.published_at || t.created_at
      if (!dateStr) return false
      const key = formatDateKey(new Date(dateStr))
      return key >= sevenDaysAgoKey && key <= todayKey
    })

    const publishedRecent = recentFinished.filter((t) => t.status === 'published').length
    const totalRecent = recentFinished.length
    const successRate7d = totalRecent > 0 ? Math.round((publishedRecent / totalRecent) * 100) : 0

    const failedRetryCount = tasks.filter((t) => t.status === 'failed').length

    set({ stats: { todayPublished, pendingCount, successRate7d, failedRetryCount } })
  },

  createTask: async (data) => {
    set({ isFormLoading: true, error: null })
    try {
      const res = await fetch('/api/publish-tasks', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('创建发布任务失败')
      await get().fetchTasks()
      set({ isFormLoading: false })
      return true
    } catch (err) {
      set({ isFormLoading: false, error: err instanceof Error ? err.message : '创建失败' })
      return false
    }
  },

  executeTask: async (id) => {
    try {
      const res = await fetch(`/api/publish-tasks/${id}/execute`, {
        method: 'POST',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('执行发布失败')
      await get().fetchTasks()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '执行失败' })
      return false
    }
  },

  retryTask: async (id) => {
    try {
      const res = await fetch(`/api/publish-tasks/${id}/retry`, {
        method: 'POST',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('重试发布失败')
      await get().fetchTasks()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '重试失败' })
      return false
    }
  },

  deleteTask: async (id) => {
    try {
      const res = await fetch(`/api/publish-tasks/${id}`, {
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
}))
