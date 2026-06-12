import { create } from 'zustand'
import { authHeaders } from '../lib/api'

export interface TodayOverview {
  tasksPending: number
  briefsPending: number
  contentsPendingReview: number
  contentsPublished: number
  engagementDelta: number
  avgHealthScore: number
}

export interface QuickAction {
  id: string
  label: string
  icon: string
  href: string
  badge?: number
}

export interface Alert {
  id: string
  level: 'emergency' | 'warning' | 'info' | 'success'
  title: string
  message: string
  timestamp: string
}

export interface ActivityEntry {
  id: string
  actor: string
  action: string
  target: string
  timestamp: string
}

export interface CoreMetrics {
  pendingReview: number
  publishedToday: number
  queuedTasks: number
  failedDlq: number
  tokenCostToday: number
}

export interface SmartTopic {
  id: string
  title: string
  estimatedEngagement: number
  tags: string[]
}

export interface AgentStatus {
  activeAgents: number
  pendingMessages: number
  successRate1h: number
  lastExecutionStatus: 'success' | 'failure' | 'idle'
}

export interface StoryProgress {
  id: string
  name: string
  currentNode: string
  currentNodeIndex: number
  totalNodes: number
  nextNodeTopic: string
  estimatedCompletionAt: string
}

export interface EngagementTrend {
  date: string
  likes: number
  comments: number
  collections: number
}

export interface HitRate {
  label: string
  value: number
  color: string
}

export interface PublishTask {
  id: string
  draft_id: string
  platform: string
  status: string
  scheduled_at?: string
  published_url?: string
  error_reason?: string
}

export interface ContentDraft {
  id: string
  title: string
  body: string
  status: string
  platform: string
  content_type: string
}

export interface AccountPoolItem {
  id: string
  nickname: string
  lifecycle_phase: string
  status: string
  health_score: number
}

interface DashboardState {
  overview: TodayOverview | null
  quickActions: QuickAction[]
  alerts: Alert[]
  activityLog: ActivityEntry[]
  activityLogTotal: number
  publishTasks: PublishTask[]
  contentDrafts: ContentDraft[]
  accountPool: AccountPoolItem[]
  coreMetrics: CoreMetrics | null
  smartTopics: SmartTopic[]
  agentStatus: AgentStatus | null
  storyProgress: StoryProgress[]
  engagementTrend: EngagementTrend[]
  hitRate: HitRate[]
  isLoading: boolean
  error: string | null
  fetchDashboard: () => Promise<void>
  fetchPublishTasks: () => Promise<void>
  fetchContentDrafts: () => Promise<void>
  fetchAccountPool: () => Promise<void>
  fetchCoreMetrics: () => Promise<void>
  fetchSmartTopics: () => Promise<void>
  fetchAgentStatus: () => Promise<void>
  fetchStoryProgress: () => Promise<void>
  fetchEngagementTrend: (days?: number) => Promise<void>
  fetchHitRate: () => Promise<void>
  clearError: () => void
}

export const useDashboardStore = create<DashboardState>((set) => ({
  overview: null,
  quickActions: [],
  alerts: [],
  activityLog: [],
  activityLogTotal: 0,
  publishTasks: [],
  contentDrafts: [],
  accountPool: [],
  coreMetrics: null,
  smartTopics: [],
  agentStatus: null,
  storyProgress: [],
  engagementTrend: [],
  hitRate: [],
  isLoading: false,
  error: null,

  fetchDashboard: async () => {
    set({ isLoading: true, error: null })
    try {
      const headers = authHeaders()

      const [overviewRes, actionsRes, alertsRes, logRes] = await Promise.all([
        fetch('/api/dashboard/overview', { headers }),
        fetch('/api/dashboard/quick-actions', { headers }),
        fetch('/api/dashboard/alerts', { headers }),
        fetch('/api/dashboard/activity-log', { headers }),
      ])

      if (!overviewRes.ok) throw new Error(`Overview: ${overviewRes.status}`)
      if (!actionsRes.ok) throw new Error(`QuickActions: ${actionsRes.status}`)
      if (!alertsRes.ok) throw new Error(`Alerts: ${alertsRes.status}`)
      if (!logRes.ok) throw new Error(`ActivityLog: ${logRes.status}`)

      const [overviewData, actionsData, alertsData, logData] = await Promise.all([
        overviewRes.json(),
        actionsRes.json(),
        alertsRes.json(),
        logRes.json(),
      ])

      set({
        overview: overviewData.today,
        quickActions: actionsData.actions,
        alerts: alertsData.alerts,
        activityLog: logData.entries,
        activityLogTotal: logData.total,
        isLoading: false,
      })
    } catch (err) {
      set({
        isLoading: false,
        error: err instanceof Error ? err.message : '加载仪表盘数据失败',
      })
    }
  },

  fetchPublishTasks: async () => {
    try {
      const res = await fetch('/api/publish-tasks', { headers: authHeaders(false) })
      if (res.ok) {
        const data = await res.json()
        set({ publishTasks: data.tasks })
      }
    } catch {
      // silent fail for MVP
    }
  },

  fetchContentDrafts: async () => {
    try {
      const res = await fetch('/api/content-drafts', { headers: authHeaders(false) })
      if (res.ok) {
        const data = await res.json()
        set({ contentDrafts: data.drafts })
      }
    } catch {
      // silent fail for MVP
    }
  },

  fetchAccountPool: async () => {
    try {
      const res = await fetch('/api/account-pool', { headers: authHeaders(false) })
      if (res.ok) {
        const data = await res.json()
        set({ accountPool: data.accounts })
      }
    } catch {
      // silent fail for MVP
    }
  },

  fetchCoreMetrics: async () => {
    try {
      const res = await fetch('/api/dashboard/core-metrics', { headers: authHeaders() })
      if (res.ok) {
        const data = await res.json()
        set({ coreMetrics: data.metrics })
      }
    } catch {
      // silent fail
    }
  },

  fetchSmartTopics: async () => {
    try {
      const res = await fetch('/api/trend-scout/topics?limit=5', { headers: authHeaders() })
      if (res.ok) {
        const data = await res.json()
        set({
          smartTopics: (data.topics || []).map((t: { id: string; title: string; estimated_engagement?: number; estimatedEngagement?: number; tags?: string[] }) => ({
            id: t.id,
            title: t.title,
            estimatedEngagement: t.estimated_engagement ?? t.estimatedEngagement ?? 0,
            tags: t.tags || [],
          })),
        })
      }
    } catch {
      // silent fail
    }
  },

  fetchAgentStatus: async () => {
    try {
      const res = await fetch('/api/agents', { headers: authHeaders() })
      if (res.ok) {
        const data = await res.json()
        set({ agentStatus: data.status || null })
      }
    } catch {
      // silent fail
    }
  },

  fetchStoryProgress: async () => {
    try {
      const res = await fetch('/api/persona-stories?status=active', { headers: authHeaders() })
      if (res.ok) {
        const data = await res.json()
        const items = data.items || data.stories || []
        const progressItems = items.filter(
          (item: { currentNodeIndex?: number; totalNodes?: number }) => item.currentNodeIndex !== undefined || item.totalNodes !== undefined
        )
        set({ storyProgress: progressItems })
      }
    } catch {
      // silent fail
    }
  },

  fetchEngagementTrend: async (days = 7) => {
    try {
      const res = await fetch(`/api/data-analyst/engagement-trend?days=${days}`, { headers: authHeaders() })
      if (res.ok) {
        const data = await res.json()
        set({ engagementTrend: data.trend || [] })
      }
    } catch {
      // silent fail
    }
  },

  fetchHitRate: async () => {
    try {
      const res = await fetch('/api/predictions/hit-rate', { headers: authHeaders() })
      if (res.ok) {
        const data = await res.json()
        set({ hitRate: data.rates || [] })
      }
    } catch {
      // silent fail
    }
  },

  clearError: () => set({ error: null }),
}))
