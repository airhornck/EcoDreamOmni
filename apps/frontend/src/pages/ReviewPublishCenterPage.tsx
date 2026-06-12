import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAICopilotStore } from '../stores/aiCopilotStore'
import { useReviewPublishStore } from '../stores/reviewPublishStore'
import {
  ClipboardList,
  Shield,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Clock,
  AlertTriangle,
  Sparkles,
  ChevronRight,
} from 'lucide-react'

const tabs = [
  { key: 'all' as const, label: '全部', icon: ClipboardList },
  { key: 'pending' as const, label: '审核中', icon: Shield },
  { key: 'approved' as const, label: '已通过', icon: CheckCircle2 },
  { key: 'rejected' as const, label: '已驳回', icon: XCircle },
  { key: 'revised' as const, label: '已打回', icon: RefreshCw },
] as const

const platformLabels: Record<string, string> = {
  xhs: '小红书',
  douyin: '抖音',
  wechat_channels: '视频号',
}

export function ReviewPublishCenterPage() {
  const navigate = useNavigate()
  const {
    conclusions,
    isLoading,
    error,
    activeTab,
    copilotSummary,
    fetchConclusions,
    setActiveTab,
    clearError,
    fetchActionCards,
  } = useReviewPublishStore()

  const { setPageActionCards, setPageActionHandler } = useAICopilotStore()

  // ─── Data Fetching ───
  useEffect(() => {
    fetchConclusions(activeTab === 'all' ? undefined : activeTab)
  }, [activeTab])

  // ─── Copilot Action Handler ───
  // 审核列表页面需要自定义 handler 处理"批量审核""AI 分析"等操作
  // fallback handler 只支持页面跳转，批量操作需调用后端 API
  const handleCopilotAction = useCallback(
    async (cardId: string, actionId: string, payload?: Record<string, unknown>) => {
      if (cardId === 'batch-review-list') {
        if (actionId === 'batch_approve') {
          // 批量通过当前可见列表中的 pending 项
          const pendingIds = conclusions
            .filter((c) => c.status === 'human_wait')
            .map((c) => c.task_id)
          if (pendingIds.length === 0) return
          // Phase 1：逐个 approve（Phase 2 迁移到 MetaOrchestrator 批量操作）
          const { useReviewPublishStore } = await import('../stores/reviewPublishStore')
          const store = useReviewPublishStore.getState()
          for (const taskId of pendingIds.slice(0, 5)) {
            await store.decideTask(taskId, 'approve')
          }
          await fetchConclusions(activeTab === 'all' ? undefined : activeTab)
          return
        }
        if (actionId === 'batch_revise') {
          const pendingIds = conclusions
            .filter((c) => c.status === 'human_wait')
            .map((c) => c.task_id)
          if (pendingIds.length === 0) return
          const { useReviewPublishStore } = await import('../stores/reviewPublishStore')
          const store = useReviewPublishStore.getState()
          for (const taskId of pendingIds.slice(0, 5)) {
            await store.decideTask(taskId, 'revise', payload?.reason as string)
          }
          await fetchConclusions(activeTab === 'all' ? undefined : activeTab)
          return
        }
      }
      if (cardId === 'ai-analysis-list') {
        // AI 分析：导航到数据报表页面
        navigate('/analytics')
        return
      }
    },
    [conclusions, activeTab, navigate, fetchConclusions],
  )

  useEffect(() => {
    // Fetch and set action cards from backend
    fetchActionCards('/review').then((res) => {
      const cards = (res.cards || []).map((c) => {
        const card = c as Record<string, unknown>
        return {
          id: String(card.id),
          type: String(card.type) as 'decision' | 'generation' | 'suggestion' | 'info',
          title: String(card.title),
          description: String(card.description),
          priority: Number(card.priority || 1),
          inputs: Array.isArray(card.inputs) ? card.inputs : [],
          actions: Array.isArray(card.actions) ? card.actions : [],
        }
      })
      setPageActionCards(cards)
    })

    // Register custom handler（覆盖 useCopilotPageSync 的 fallback handler）
    setPageActionHandler(handleCopilotAction)

    // Cleanup on unmount
    return () => {
      setPageActionCards([])
      setPageActionHandler(null)
    }
  }, [activeTab, handleCopilotAction, fetchActionCards, setPageActionCards, setPageActionHandler])

  // ─── Helpers ───
  const getStatusBadge = (c: (typeof conclusions)[0]) => {
    if (c.review_decision === 'APPROVE') return { label: '已通过', color: 'bg-success/10 text-success' }
    if (c.review_decision === 'REJECT') return { label: '已驳回', color: 'bg-destructive/10 text-destructive' }
    if (c.review_decision === 'REVISE') return { label: '已打回', color: 'bg-warning/10 text-warning' }
    return { label: '审核中', color: 'bg-primary/10 text-primary' }
  }

  const getComplianceColor = (score?: number) => {
    if (!score) return 'text-muted-foreground'
    if (score >= 85) return 'text-success'
    if (score >= 70) return 'text-warning'
    return 'text-destructive'
  }

  return (
    <div className="h-full flex flex-col page-transition">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-lg font-semibold text-foreground">审核发布</h1>
          {copilotSummary && (
            <p className="text-xs text-muted-foreground mt-0.5">
              {copilotSummary.total_pending > 0
                ? `${copilotSummary.total_pending} 条待审 — ${copilotSummary.batch_suggestion}`
                : '暂无待审内容'}
            </p>
          )}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 flex items-center gap-2 text-sm text-destructive">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={clearError} className="text-xs underline hover:no-underline">关闭</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-4 p-1 bg-muted/50 rounded-lg w-fit">
        {tabs.map((t) => {
          const Icon = t.icon
          const isActive = activeTab === t.key
          return (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all
                ${isActive ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}
              `}
            >
              <Icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          )
        })}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="space-y-3 text-center">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm text-muted-foreground">加载中...</p>
          </div>
        </div>
      ) : conclusions.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center space-y-3 py-16">
          <ClipboardList className="w-10 h-10 text-muted-foreground/40" />
          <div>
            <p className="text-sm font-medium text-foreground">暂无内容</p>
            <p className="text-xs text-muted-foreground mt-1">
              {activeTab === 'all' ? '当前没有需要审核的内容' : `暂无「${tabs.find((t) => t.key === activeTab)?.label}」内容`}
            </p>
          </div>
          <p className="text-xs text-primary/70 flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            有新内容生成后会自动出现在这里
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {conclusions.map((c) => {
            const badge = getStatusBadge(c)
            const complianceColor = getComplianceColor(c.compliance_score)
            return (
              <div
                key={c.task_id}
                onClick={() => navigate(`/review/${c.task_id}`)}
                className="group p-4 rounded-xl bg-card border border-border hover:border-primary/30 hover:shadow-sm cursor-pointer transition-all card-hover"
              >
                <div className="flex items-start gap-3">
                  {/* Cover */}
                  <div className="shrink-0 w-16 h-16 rounded-lg bg-muted overflow-hidden">
                    {c.cover_image_url ? (
                      <img src={c.cover_image_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <ClipboardList className="w-5 h-5 text-muted-foreground/30" />
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-medium text-foreground truncate">
                        {c.content_title || c.task_name}
                      </h3>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${badge.color}`}>
                        {badge.label}
                      </span>
                    </div>

                    <p className="text-xs text-muted-foreground line-clamp-1 mb-2">
                      {c.content_preview}
                    </p>

                    <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                      <span className="flex items-center gap-1">
                        {platformLabels[c.platform] || c.platform}
                      </span>
                      <span>{c.account_name}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatRelativeTime(c.waiting_since)}
                      </span>
                      {typeof c.compliance_score === 'number' && (
                        <span className={`flex items-center gap-1 font-medium ${complianceColor}`}>
                          <Shield className="w-3 h-3" />
                          {c.compliance_score}分
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Arrow */}
                  <ChevronRight className="w-4 h-4 text-muted-foreground/30 group-hover:text-primary/60 transition-colors shrink-0 mt-5" />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  return `${days}天前`
}
