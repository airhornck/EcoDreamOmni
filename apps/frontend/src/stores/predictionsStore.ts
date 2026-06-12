import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface Prediction {
  id: string
  likes: { lower: number; median: number; upper: number }
  comments: { lower: number; median: number; upper: number }
  saves: { lower: number; median: number; upper: number }
  interval_mode: string
  confidence: number
  content_id?: string
  created_at: string
  content_summary?: string
  account_id?: string
}

export interface PredictionStats {
  total: number
  today: number
  avgConfidence: number
  weekAccuracy: number
}

export interface AccuracyData {
  daily: { date: string; accuracy: number }[]
  byPlatform: { platform: string; accuracy: number }[]
  byContentType: { type: string; accuracy: number }[]
}

export interface BatchPredictionResult {
  id: string
  content_summary: string
  likes: { lower: number; upper: number }
  confidence: number
}

export interface AccountOption {
  id: string
  name: string
  platform: string
}

interface PredictionsState {
  predictions: Prediction[]
  current: Prediction | null
  batchResults: BatchPredictionResult[]
  stats: PredictionStats | null
  accuracyData: AccuracyData | null
  accounts: AccountOption[]
  isLoading: boolean
  error: string | null
  createPrediction: (contentText: string, tags?: string[], accountId?: string) => Promise<Prediction | null>
  createBatchPredictions: (items: string[], tags?: string[], accountId?: string) => Promise<BatchPredictionResult[] | null>
  fetchPredictions: () => Promise<void>
  fetchPrediction: (id: string) => Promise<Prediction | null>
  fetchStats: () => Promise<void>
  fetchAccuracy: () => Promise<void>
  fetchAccounts: () => Promise<void>
}

export const usePredictionsStore = create<PredictionsState>((set) => ({
  predictions: [],
  current: null,
  batchResults: [],
  stats: null,
  accuracyData: null,
  accounts: [],
  isLoading: false,
  error: null,

  createPrediction: async (contentText, tags, accountId) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/predictions', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ content_text: contentText, tags, account_id: accountId }),
      })
      if (!res.ok) throw new Error('预测失败')
      const data = await res.json()
      set((state) => ({ predictions: [data, ...state.predictions], current: data, isLoading: false }))
      return data
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '预测失败' })
      return null
    }
  },

  createBatchPredictions: async (items, tags, accountId) => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/predictions/batch', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ items, tags, account_id: accountId }),
      })
      if (!res.ok) throw new Error('批量预测失败')
      const data = await res.json()
      set({ batchResults: data.results || data || [], isLoading: false })
      return data.results || data || []
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '批量预测失败' })
      return null
    }
  },

  fetchPredictions: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/predictions', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取预测历史失败')
      const data = await res.json()
      set({ predictions: data.predictions || data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '获取失败' })
    }
  },

  fetchPrediction: async (id) => {
    try {
      const res = await fetch(`/api/predictions/${id}`, { headers: authHeaders() })
      if (!res.ok) throw new Error('获取预测失败')
      const data = await res.json()
      set({ current: data })
      return data
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取失败' })
      return null
    }
  },

  fetchStats: async () => {
    try {
      const res = await fetch('/api/predictions/stats', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取统计失败')
      const data = await res.json()
      set({ stats: data })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取统计失败' })
    }
  },

  fetchAccuracy: async () => {
    try {
      const res = await fetch('/api/predictions/accuracy', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取命中率失败')
      const data = await res.json()
      set({ accuracyData: data })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取命中率失败' })
    }
  },

  fetchAccounts: async () => {
    try {
      const res = await fetch('/api/account-pool?status=active', { headers: authHeaders() })
      if (!res.ok) throw new Error('获取账号失败')
      const data = await res.json()
      set({ accounts: data.accounts || data || [] })
    } catch {
      set({ accounts: [] })
    }
  },
}))
