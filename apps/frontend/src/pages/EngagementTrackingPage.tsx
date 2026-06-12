import { useEffect, useState } from 'react'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { Button } from '../components/ui/Button'
import { authHeaders } from '../lib/api'
import {
  Eye,
  ThumbsUp,
  MessageCircle,
  Bookmark,
  Share2,
  BarChart3,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react'

interface EngagementItem {
  id: string
  publish_task_id: string
  account_id: string
  platform_post_id: string
  likes: number | null
  comments: number | null
  saves: number | null
  shares: number | null
  views: number | null
  fetch_status: string
  fetch_error: string | null
  fetched_at: string | null
  created_at: string
  task_name: string | null
  content_title: string | null
  published_url: string | null
}

interface EngagementListResponse {
  total: number
  items: EngagementItem[]
}

const STATUS_LABELS: Record<string, { label: string; variant: 'success' | 'warning' | 'danger' | 'default' }> = {
  success: { label: '抓取成功', variant: 'success' },
  failed: { label: '抓取失败', variant: 'danger' },
  pending: { label: '等待中', variant: 'default' },
  manual: { label: '手动导入', variant: 'warning' },
}

function StatusBadge({ status, error }: { status: string; error?: string | null }) {
  const cfg = STATUS_LABELS[status] || STATUS_LABELS.pending
  const iconMap: Record<string, React.ReactNode> = {
    success: <CheckCircle2 className="w-3.5 h-3.5" />,
    failed: <XCircle className="w-3.5 h-3.5" />,
    pending: <Clock className="w-3.5 h-3.5" />,
    manual: <AlertCircle className="w-3.5 h-3.5" />,
  }
  return (
    <div>
      <Badge variant={cfg.variant} className="gap-1">
        {iconMap[status] || iconMap.pending}
        {cfg.label}
      </Badge>
      {error && (
        <p className="text-xs text-destructive mt-1 max-w-[140px] truncate" title={error}>
          {error}
        </p>
      )}
    </div>
  )
}

function formatNumber(n: number | null): string {
  if (n === null || n === undefined) return '-'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

function formatDate(iso: string | null): string {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export function EngagementTrackingPage() {
  const [data, setData] = useState<EngagementListResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [page, setPage] = useState(0)
  const limit = 10

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams()
      params.set('limit', String(limit))
      params.set('offset', String(page * limit))
      if (statusFilter) params.set('status', statusFilter)
      const res = await fetch(`/api/data-analyst/engagements?${params.toString()}`, {
        headers: authHeaders(false),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      const json: EngagementListResponse = await res.json()
      setData(json)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      setLoading(true)
      setError('')
      try {
        const params = new URLSearchParams()
        params.set('limit', String(limit))
        params.set('offset', String(page * limit))
        if (statusFilter) params.set('status', statusFilter)
        const res = await fetch(`/api/data-analyst/engagements?${params.toString()}`, {
          headers: authHeaders(false),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || `HTTP ${res.status}`)
        }
        const json: EngagementListResponse = await res.json()
        if (!cancelled) setData(json)
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : '加载失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [page, statusFilter])

  const totalPages = data ? Math.ceil(data.total / limit) : 0

  return (
    <div className="space-y-6">
      <PageHeader
        title="互动数据跟踪"
        subtitle="24h 发布后自动抓取笔记互动指标（点赞 / 评论 / 收藏 / 分享 / 阅读）"
      />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">状态筛选:</span>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(0) }}
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">全部</option>
            <option value="success">抓取成功</option>
            <option value="failed">抓取失败</option>
            <option value="pending">等待中</option>
            <option value="manual">手动导入</option>
          </select>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Table */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              互动数据列表
              {data !== null && (
                <Badge variant="default">共 {data.total} 条</Badge>
              )}
            </h3>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading && !data ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
              <span className="ml-2 text-sm text-muted-foreground">加载中...</span>
            </div>
          ) : data && data.items.length === 0 ? (
            <EmptyState
              icon={Eye}
              title="暂无互动数据"
              description="发布笔记并等待 24h 后，系统将自动抓取互动数据。也可通过 CSV 导入方式补充数据。"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">内容标题</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">平台帖子ID</th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">
                      <span className="inline-flex items-center gap-1"><ThumbsUp className="w-3.5 h-3.5" /> 点赞</span>
                    </th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">
                      <span className="inline-flex items-center gap-1"><MessageCircle className="w-3.5 h-3.5" /> 评论</span>
                    </th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">
                      <span className="inline-flex items-center gap-1"><Bookmark className="w-3.5 h-3.5" /> 收藏</span>
                    </th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">
                      <span className="inline-flex items-center gap-1"><Share2 className="w-3.5 h-3.5" /> 分享</span>
                    </th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">阅读量</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">状态</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">抓取时间</th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((item) => (
                    <tr key={item.id} className="border-b last:border-0 hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3">
                        <div className="max-w-[200px]">
                          <p className="font-medium truncate" title={item.content_title || item.task_name || '-'}>
                            {item.content_title || item.task_name || '-'}
                          </p>
                          <p className="text-xs text-muted-foreground mt-0.5 truncate" title={item.account_id}>
                            账号: {item.account_id}
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{item.platform_post_id.slice(0, 12)}...</code>
                      </td>
                      <td className="px-4 py-3 text-center font-semibold">{formatNumber(item.likes)}</td>
                      <td className="px-4 py-3 text-center font-semibold">{formatNumber(item.comments)}</td>
                      <td className="px-4 py-3 text-center font-semibold">{formatNumber(item.saves)}</td>
                      <td className="px-4 py-3 text-center font-semibold">{formatNumber(item.shares)}</td>
                      <td className="px-4 py-3 text-center font-semibold">{formatNumber(item.views)}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={item.fetch_status} error={item.fetch_error} />
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{formatDate(item.fetched_at)}</td>
                      <td className="px-4 py-3 text-right">
                        {item.published_url && (
                          <a
                            href={item.published_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-primary hover:underline text-xs"
                          >
                            查看笔记 <ExternalLink className="w-3 h-3 ml-0.5" />
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {data && data.total > 0 && (
            <div className="flex items-center justify-between px-4 py-3 border-t">
              <span className="text-sm text-muted-foreground">
                第 {page * limit + 1} - {Math.min((page + 1) * limit, data.total)} 条，共 {data.total} 条
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0 || loading}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-sm text-muted-foreground">
                  {page + 1} / {Math.max(1, totalPages)}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1 || loading}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
