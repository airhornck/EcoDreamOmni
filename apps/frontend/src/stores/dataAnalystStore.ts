import { create } from 'zustand'
import { authHeaders } from '../lib/api'

const PLATFORM_COLORS: Record<string, string> = {
  xiaohongshu: '#ff2442',
  xhs: '#ff2442',
  douyin: '#1c1c1c',
  wechat_channels: '#07c160',
  videoChannel: '#07c160',
}

const PLATFORM_LABELS: Record<string, string> = {
  xiaohongshu: '小红书',
  xhs: '小红书',
  douyin: '抖音',
  wechat_channels: '视频号',
  videoChannel: '视频号',
}

export interface DataReport {
  id: string
  account_id: string
  content_id: string
  period: string
  actual_metrics: Record<string, number>
  prediction_comparison: Record<string, unknown>
  attribution: Record<string, unknown>
  model_calibration: Record<string, unknown>
}

export interface DashboardData {
  totalPublished: number
  totalPublishedChange: number
  avgCoverage: number
  avgMape: number
  avgLikes: number
  avgLikesChange: number
}

export interface PublishTrendPoint {
  date: string
  total: number
  xiaohongshu: number
  douyin: number
  videoChannel: number
}

export interface PlatformDistributionItem {
  name: string
  value: number
  color: string
}

export interface EngagementDistributionItem {
  type: string
  likes: number
  comments: number
  saves: number
}

export interface MapeTrendPoint {
  date: string
  mape: number
}

export interface ContentRankingItem {
  id: string
  rank: number
  title: string
  platform: string
  likes: number
  comments: number
  saves: number
  coverage: number
  mape: number
}

export interface AccountComparisonItem {
  id: string
  name: string
  platform: string
  publishCount: number
  avgLikes: number
  healthScore: number
}

export interface ReportItem {
  id: string
  name: string
  createdAt: string
  period: string
}

export interface CalibrationStatus {
  lastCalibratedAt: string | null
  status: 'idle' | 'running' | 'success' | 'failed'
  message: string
}

export interface ImportHistoryItem {
  id: string
  filename: string
  importedAt: string
  rows: number
  status: 'success' | 'partial' | 'failed'
}

interface DataAnalystState {
  reports: DataReport[]
  dashboard: DashboardData | null
  publishTrend: PublishTrendPoint[]
  platformDistribution: PlatformDistributionItem[]
  engagementDistribution: EngagementDistributionItem[]
  mapeTrend: MapeTrendPoint[]
  contentRanking: ContentRankingItem[]
  accountComparison: AccountComparisonItem[]
  reportList: ReportItem[]
  calibrationStatus: CalibrationStatus | null
  importHistory: ImportHistoryItem[]
  isLoading: boolean
  error: string | null
  fetchReports: () => Promise<void>
  fetchDashboard: () => Promise<void>
  fetchPublishTrend: (days?: number) => Promise<void>
  fetchPlatformDistribution: () => Promise<void>
  fetchEngagementDistribution: () => Promise<void>
  fetchMapeTrend: () => Promise<void>
  fetchContentRanking: (limit?: number) => Promise<void>
  fetchAccountComparison: () => Promise<void>
  fetchReportList: () => Promise<void>
  fetchCalibrationStatus: () => Promise<void>
  fetchImportHistory: () => Promise<void>
  createReport: (contentId: string, csvData?: FormData) => Promise<boolean>
  getAttribution: (contentId: string) => Promise<Record<string, unknown> | null>
  triggerCalibrate: () => Promise<boolean>
  clearError: () => void
}

export const useDataAnalystStore = create<DataAnalystState>((set, get) => ({
  reports: [],
  dashboard: null,
  publishTrend: [],
  platformDistribution: [],
  engagementDistribution: [],
  mapeTrend: [],
  contentRanking: [],
  accountComparison: [],
  reportList: [],
  calibrationStatus: null,
  importHistory: [],
  isLoading: false,
  error: null,

  clearError: () => set({ error: null }),

  fetchReports: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/data-analyst/reports', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取报告列表失败: ${res.status}`)
      const data = await res.json()
      set({ reports: data, isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  fetchDashboard: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await fetch('/api/data-analyst/dashboard', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取仪表盘失败: ${res.status}`)
      const data = await res.json()
      set({ dashboard: data, isLoading: false })
    } catch (err) {
      set({ isLoading: false, error: err instanceof Error ? err.message : '未知错误' })
    }
  },

  fetchPublishTrend: async (days = 30) => {
    try {
      const res = await fetch(`/api/data-analyst/publish-trend?days=${days}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取发布趋势失败: ${res.status}`)
      const data = await res.json()
      const trend = Array.isArray(data) ? data : (data.trend || [])
      set({
        publishTrend: trend.map((d: { date: string; count?: number; total?: number }) => ({
          date: d.date,
          total: d.total ?? d.count ?? 0,
          xiaohongshu: d.count ?? d.total ?? 0,
          douyin: d.count ?? d.total ?? 0,
          videoChannel: d.count ?? d.total ?? 0,
        })),
      })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取发布趋势失败' })
    }
  },

  fetchPlatformDistribution: async () => {
    try {
      const res = await fetch('/api/data-analyst/platform-distribution', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取平台分布失败: ${res.status}`)
      const data = await res.json()
      const distribution = Array.isArray(data) ? data : (data.distribution || [])
      set({
        platformDistribution: distribution.map((d: { platform: string; count: number; percentage?: number }) => ({
          name: PLATFORM_LABELS[d.platform] || d.platform,
          value: d.count,
          color: PLATFORM_COLORS[d.platform] || '#888888',
        })),
      })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取平台分布失败' })
    }
  },

  fetchEngagementDistribution: async () => {
    try {
      const res = await fetch('/api/data-analyst/engagement-distribution', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取互动量分布失败: ${res.status}`)
      const data = await res.json()
      set({
        engagementDistribution: data
          ? [
              {
                type: '平均互动',
                likes: data.likes_avg || 0,
                comments: data.comments_avg || 0,
                saves: data.collections_avg || 0,
              },
            ]
          : [],
      })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取互动量分布失败' })
    }
  },

  fetchMapeTrend: async () => {
    try {
      const res = await fetch('/api/data-analyst/mape-trend', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取MAPE趋势失败: ${res.status}`)
      const data = await res.json()
      set({ mapeTrend: Array.isArray(data) ? data : (data.trend || []) })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取MAPE趋势失败' })
    }
  },

  fetchContentRanking: async (limit = 10) => {
    try {
      const res = await fetch(`/api/data-analyst/content-ranking?limit=${limit}`, { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取内容排行榜失败: ${res.status}`)
      const data = await res.json()
      const ranking = Array.isArray(data) ? data : (data.ranking || [])
      set({
        contentRanking: ranking.map((item: { rank: number; title: string; platform: string; likes: number; comments: number; collections?: number; saves?: number; coverage: number; mape: number }) => ({
          id: `${item.rank}-${item.title}`,
          rank: item.rank,
          title: item.title,
          platform: item.platform,
          likes: item.likes,
          comments: item.comments,
          saves: item.saves ?? item.collections ?? 0,
          coverage: item.coverage,
          mape: item.mape,
        })),
      })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取内容排行榜失败' })
    }
  },

  fetchAccountComparison: async () => {
    try {
      const res = await fetch('/api/data-analyst/account-comparison', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取账号对比失败: ${res.status}`)
      const data = await res.json()
      const accounts = Array.isArray(data) ? data : (data.accounts || [])
      set({
        accountComparison: accounts.map((a: { account_id: string; account_name: string; platform: string; avg_engagement: number; health_score: number }) => ({
          id: a.account_id,
          name: a.account_name,
          platform: a.platform,
          publishCount: 0,
          avgLikes: a.avg_engagement,
          healthScore: a.health_score,
        })),
      })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取账号对比失败' })
    }
  },

  fetchReportList: async () => {
    try {
      const res = await fetch('/api/data-analyst/reports', { headers: authHeaders() })
      if (!res.ok) {
        // 后端暂无列表接口，返回空数组避免页面白屏
        if (res.status === 404) {
          set({ reportList: [] })
          return
        }
        throw new Error(`获取报表列表失败: ${res.status}`)
      }
      const data = await res.json()
      const items = Array.isArray(data) ? data : (data.items || data.reports || [])
      set({
        reportList: items.map((r: { id?: string; name?: string; created_at?: string; createdAt?: string; period?: string }) => ({
          id: r.id || '',
          name: r.name || '',
          createdAt: r.created_at || r.createdAt || '',
          period: r.period || '',
        })),
      })
    } catch (err) {
      set({ reportList: [] })
      set({ error: err instanceof Error ? err.message : '获取报表列表失败' })
    }
  },

  fetchCalibrationStatus: async () => {
    try {
      const res = await fetch('/api/data-analyst/calibration-status', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取校准状态失败: ${res.status}`)
      const data = await res.json()
      const statusMap: Record<string, CalibrationStatus['status']> = {
        ok: 'success',
        success: 'success',
        running: 'running',
        failed: 'failed',
        idle: 'idle',
      }
      set({
        calibrationStatus: {
          lastCalibratedAt: data.last_calibrated_at || null,
          status: statusMap[data.status] || 'idle',
          message: data.message || '',
        },
      })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取校准状态失败' })
    }
  },

  fetchImportHistory: async () => {
    try {
      const res = await fetch('/api/data-analyst/import-history', { headers: authHeaders() })
      if (!res.ok) throw new Error(`获取导入历史失败: ${res.status}`)
      const data = await res.json()
      const history = Array.isArray(data) ? data : (data.history || [])
      set({
        importHistory: history.map((h: { id: string; file_name?: string; filename?: string; imported_at?: string; importedAt?: string; record_count?: number; rows?: number; status?: 'success' | 'partial' | 'failed' }) => ({
          id: h.id,
          filename: h.file_name || h.filename || '',
          importedAt: h.imported_at || h.importedAt || '',
          rows: h.record_count ?? h.rows ?? 0,
          status: h.status || 'success',
        })),
      })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取导入历史失败' })
    }
  },

  createReport: async (contentId, csvData) => {
    try {
      let res: Response
      if (csvData) {
        res = await fetch('/api/data-analyst/reports', {
          method: 'POST',
          headers: authHeaders(false),
          body: csvData,
        })
      } else {
        res = await fetch('/api/data-analyst/reports', {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ content_id: contentId, period: '24h' }),
        })
      }
      if (!res.ok) throw new Error('创建报告失败')
      await get().fetchReports()
      await get().fetchImportHistory()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建失败' })
      return false
    }
  },

  getAttribution: async (contentId) => {
    try {
      const res = await fetch(`/api/data-analyst/attribution/${contentId}`, { headers: authHeaders() })
      if (!res.ok) throw new Error('获取归因失败')
      return await res.json()
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取失败' })
      return null
    }
  },

  triggerCalibrate: async () => {
    try {
      const res = await fetch('/api/data-analyst/calibrate', {
        method: 'POST',
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error('触发校准失败')
      await get().fetchCalibrationStatus()
      return true
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '触发失败' })
      return false
    }
  },
}))
