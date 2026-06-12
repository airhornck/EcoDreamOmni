import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface CronJob {
  id: string
  name: string
  description: string
  schedule: string
  target_type: string
  target_id: string
  status: string
  concurrency_policy: string
  owner: string
}

export interface JobExecution {
  id: string
  job_id: string
  execution_type: string
  status: string
  scheduled_at: string
  started_at: string | null
  ended_at: string | null
  duration_ms: number | null
  output_summary: string | null
  error_message: string | null
}

export interface DLQEntry {
  id: string
  job_id: string
  execution_id: string
  failed_at: string
  error_message: string
  error_type: string
  retry_exhausted: boolean
  status: string
}

interface CronCockpitState {
  jobs: CronJob[]
  executions: JobExecution[]
  dlq: DLQEntry[]
  isLoading: boolean
  error: string | null
  activeTab: 'jobs' | 'executions' | 'dlq'
  fetchJobs: () => Promise<void>
  fetchExecutions: () => Promise<void>
  fetchDLQ: () => Promise<void>
  createJob: (payload: Partial<CronJob>) => Promise<CronJob | null>
  deleteJob: (id: string) => Promise<boolean>
  executeJob: (id: string) => Promise<boolean>
  retryExecution: (id: string) => Promise<boolean>
  reviewDLQ: (id: string, decision: string, reviewer: string) => Promise<boolean>
  setActiveTab: (tab: 'jobs' | 'executions' | 'dlq') => void
  clearError: () => void
}

export const useCronCockpitStore = create<CronCockpitState>((set) => ({
  jobs: [],
  executions: [],
  dlq: [],
  isLoading: false,
  error: null,
  activeTab: 'jobs',

  fetchJobs: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/cron-hub/jobs', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Jobs: ${res.status}`)
      const data = await res.json()
      set({ jobs: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载任务失败' })
    }
  },

  fetchExecutions: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/cron-hub/executions?limit=100', { headers: authHeaders() })
      if (!res.ok) throw new Error(`Executions: ${res.status}`)
      const data = await res.json()
      set({ executions: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载执行历史失败' })
    }
  },

  fetchDLQ: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/cron-hub/dlq?limit=100', { headers: authHeaders() })
      if (!res.ok) throw new Error(`DLQ: ${res.status}`)
      const data = await res.json()
      set({ dlq: data || [], isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '加载死信队列失败' })
    }
  },

  createJob: async (payload) => {
    try {
      const res = await fetch('/api/cron-hub/jobs', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`Create: ${res.status}`)
      const job = await res.json()
      set((s) => ({ jobs: [job, ...s.jobs] }))
      return job
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建任务失败' })
      return null
    }
  },

  deleteJob: async (id) => {
    try {
      const res = await fetch(`/api/cron-hub/jobs/${id}`, { method: 'DELETE', headers: authHeaders() })
      if (!res.ok) throw new Error(`Delete: ${res.status}`)
      set((s) => ({ jobs: s.jobs.filter((j) => j.id !== id) }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除任务失败' })
      return false
    }
  },

  executeJob: async (id) => {
    try {
      const res = await fetch(`/api/cron-hub/jobs/${id}/execute`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ execution_type: 'MANUAL' }),
      })
      if (!res.ok) throw new Error(`Execute: ${res.status}`)
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '执行失败' })
      return false
    }
  },

  retryExecution: async (id) => {
    try {
      const res = await fetch(`/api/cron-hub/executions/${id}/retry`, {
        method: 'POST',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`Retry: ${res.status}`)
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '重试失败' })
      return false
    }
  },

  reviewDLQ: async (id, decision, reviewer) => {
    try {
      const res = await fetch(`/api/cron-hub/dlq/${id}/review`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ decision, reviewed_by: reviewer }),
      })
      if (!res.ok) throw new Error(`Review: ${res.status}`)
      set((s) => ({ dlq: s.dlq.filter((d) => d.id !== id) }))
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '审核失败' })
      return false
    }
  },

  setActiveTab: (tab) => set({ activeTab: tab }),
  clearError: () => set({ error: null }),
}))
