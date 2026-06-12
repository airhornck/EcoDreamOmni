import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useReviewPublishStore } from '../stores/reviewPublishStore'
import { useAICopilotStore } from '../stores/aiCopilotStore'
import { NoteEditorPanel } from '../components/review/NoteEditorPanel'
import { NotePreviewPanel } from '../components/review/NotePreviewPanel'
import { AgentSummaryPanel } from '../components/review/AgentSummaryPanel'
import { TopicReportPanel } from '../components/review/TopicReportPanel'
import { CoverPickerModal } from '../components/review/CoverPickerModal'
import {
  ArrowLeft,
  AlertTriangle,
  Loader2,
  ImagePlus,
  Sparkles,
} from 'lucide-react'

export function ReviewPublishDetailPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [coverModalOpen, setCoverModalOpen] = useState(false)
  const [coverGenerating, setCoverGenerating] = useState(false)

  const {
    currentDetail,
    isLoading,
    error,
    fetchDetail,
    updateContent,
    getCoverStatus,
    clearError,
    fetchActionCards,
    reportCopilotContext,
    executeCopilotAction,
  } = useReviewPublishStore()

  const { setPageActionCards, setPageActionHandler } = useAICopilotStore()

  // ─── Data Fetching ───
  useEffect(() => {
    if (taskId) fetchDetail(taskId)
  }, [taskId])

  // ─── Copilot Action Handler — 透传后端统一网关，仅保留 UI 副作用 ───
  const handleCopilotAction = useCallback(
    async (cardId: string, actionId: string, payload?: Record<string, unknown>) => {
      if (!taskId) return

      // 封面生成：走 execute 网关后异步轮询并自动应用
      if (cardId.startsWith('cover-gen') && actionId === 'generate') {
        const result = await executeCopilotAction({
          card_id: cardId,
          action_id: actionId,
          inputs: payload,
          payload: { task_id: taskId, style_preset: 'cute', count: 2, ratio: '3:4' },
        }) as Record<string, unknown>

        const coverJob = result?.cover_job as Record<string, unknown> | undefined
        if (coverJob?.job_id) {
          setCoverGenerating(true)
          try {
            for (let i = 0; i < 30; i++) {
              const status = await getCoverStatus(String(coverJob.job_id))
              if (status.status === 'completed' && status.results && status.results.length > 0) {
                await updateContent(taskId, { cover_image_url: status.results[0].url })
                await fetchDetail(taskId)
                break
              } else if (status.status === 'failed') {
                throw new Error(status.error_message || '封面生成失败')
              }
              await new Promise((r) => setTimeout(r, 1000))
            }
          } finally {
            setCoverGenerating(false)
          }
        }
        return
      }

      // 其他所有 Action 统一透传到后端 execute 网关
      const result = await executeCopilotAction({
        card_id: cardId,
        action_id: actionId,
        inputs: payload,
        payload: { task_id: taskId, publish_mode: actionId === 'publish_now' ? 'immediate' : actionId === 'schedule' ? 'scheduled' : undefined },
      }) as Record<string, unknown>

      // 处理后端返回的 copilot_followup（如审核通过后的发布确认 Cards）
      const followup = result?.copilot_followup as Record<string, unknown> | undefined
      if (followup?.suggested_cards) {
        const suggestedCards = followup.suggested_cards as Array<Record<string, unknown>>
        const newCards = suggestedCards.map((sc) => ({
          id: `publish-confirm-${taskId}`,
          type: 'decision' as const,
          title: String(sc.title),
          description: String(followup.message || ''),
          actions: ((sc.actions as Array<{ id: string; label: string }>) || []).map((a) => ({
            id: a.id,
            label: a.label,
            variant: (a.id === 'publish_now' ? 'primary' : 'secondary') as 'primary' | 'secondary' | 'ghost',
          })),
        }))
        setPageActionCards(newCards)
      }

      // 打回 / 驳回 / 发布后导航回列表
      if (
        (cardId.startsWith('review-decision') && (actionId === 'revise' || actionId === 'reject')) ||
        cardId.startsWith('publish-confirm')
      ) {
        navigate('/review')
      }
    },
    [taskId],
  )

  // ─── Copilot Action Cards — 上下文由 useCopilotPageSync 统一注入 ───
  useEffect(() => {
    if (!taskId || !currentDetail) return

    // 向后端上报详细的选中内容上下文（补充 useCopilotPageSync 的基础上下文）
    reportCopilotContext({
      session_id: `sess_${Date.now()}`,
      page: '/review',
      selected_items: [taskId],
      selected_content: {
        task_id: taskId,
        title: currentDetail.generated_content?.title || '',
        compliance_score: currentDetail.compliance_result?.overall || 80,
        quality_score: currentDetail.quality_score?.overall || 80,
        status: currentDetail.status,
        platform: currentDetail.platform,
        account_name: currentDetail.account_name,
      },
    })

    // 获取页面级 Action Cards（后端驱动，逐步迁移中）
    fetchActionCards('/review', taskId).then((res) => {
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

    // 注册自定义 Action Handler（审核决策、封面生成等业务逻辑）
    setPageActionHandler(handleCopilotAction)

    return () => {
      setPageActionCards([])
      setPageActionHandler(null)
    }
  }, [taskId, currentDetail?.status, handleCopilotAction])

  // ─── Content Change Handlers ───
  const handleContentChange = useCallback(
    (patch: Partial<{ title: string; body: string; tags: string[]; cover_image_url: string }>) => {
      if (!taskId) return
      updateContent(taskId, patch)
    },
    [taskId],
  )

  const handleCoverSelect = useCallback(
    (url: string) => {
      if (!taskId) return
      updateContent(taskId, { cover_image_url: url })
      setCoverModalOpen(false)
    },
    [taskId],
  )

  // ─── Loading & Error ───
  if (isLoading || !currentDetail) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="space-y-3 text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
          <p className="text-sm text-muted-foreground">加载审核详情...</p>
        </div>
      </div>
    )
  }

  const gc = currentDetail.generated_content

  return (
    <div className="h-full flex flex-col page-transition">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4 shrink-0">
        <button
          onClick={() => navigate('/review')}
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          返回审核列表
        </button>
        <div className="h-4 w-px bg-border" />
        <h1 className="text-sm font-medium text-foreground truncate max-w-md">
          {gc?.title || currentDetail.task_name}
        </h1>
        <StatusBadge status={currentDetail.status} />
        {coverGenerating && (
          <span className="flex items-center gap-1 text-xs text-primary ml-auto">
            <Loader2 className="w-3 h-3 animate-spin" />
            生成封面中...
          </span>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 flex items-center gap-2 text-sm text-destructive shrink-0">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={clearError} className="text-xs underline hover:no-underline">关闭</button>
        </div>
      )}

      {/* Main Content — Two Column */}
      <div className="flex-1 flex gap-5 min-h-0 overflow-hidden">
        {/* Left Column — Editor */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1 pb-4">
          {/* Cover Grid */}
          {gc?.images && gc.images.length > 0 && (
            <div className="grid grid-cols-3 gap-2">
              {gc.images.map((url, idx) => (
                <div
                  key={idx}
                  className="relative aspect-square rounded-lg overflow-hidden bg-muted group"
                >
                  <img src={url} alt="" className="w-full h-full object-cover" />
                  {idx === 0 && (
                    <span className="absolute top-1.5 left-1.5 text-[10px] px-1.5 py-0.5 rounded bg-primary text-primary-foreground">
                      首图
                    </span>
                  )}
                </div>
              ))}
              <button
                onClick={() => setCoverModalOpen(true)}
                className="aspect-square rounded-lg border-2 border-dashed border-border flex flex-col items-center justify-center gap-1 text-muted-foreground hover:border-primary/40 hover:text-primary transition-colors"
              >
                <ImagePlus className="w-5 h-5" />
                <span className="text-[10px]">更换封面</span>
              </button>
            </div>
          )}

          {/* Editor */}
          {gc && (
            <NoteEditorPanel
              content={gc}
              editable={currentDetail.status === 'human_wait'}
              onChange={handleContentChange}
              platformSchema={null}
              contentFormat={currentDetail.platform}
            />
          )}

          {/* Topic Report */}
          <TopicReportPanel report={currentDetail.topic_report} />

          {/* Agent Summary */}
          <AgentSummaryPanel detail={currentDetail} />
        </div>

        {/* Right Column — Preview */}
        <div className="w-[380px] shrink-0 overflow-y-auto space-y-4 pb-4">
          <NotePreviewPanel
            content={gc}
            location=""
            mentions={[]}
            visibility="public"
            declaration="none"
          />

          {/* AI Suggestions */}
          {currentDetail.copilot_context?.suggested_improvements &&
            currentDetail.copilot_context.suggested_improvements.length > 0 && (
            <div className="p-3 rounded-xl bg-primary/5 border border-primary/10">
              <div className="flex items-center gap-1.5 mb-2">
                <Sparkles className="w-3.5 h-3.5 text-primary" />
                <span className="text-xs font-medium text-primary">AI 建议</span>
              </div>
              <ul className="space-y-1">
                {currentDetail.copilot_context.suggested_improvements.map((s, i) => (
                  <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                    <span className="text-primary mt-0.5">•</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Cover Picker Modal */}
      <CoverPickerModal
        open={coverModalOpen}
        onClose={() => setCoverModalOpen(false)}
        onSelect={handleCoverSelect}
      />
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    human_wait: { label: '审核中', className: 'bg-primary/10 text-primary' },
    approved_waiting_publish: { label: '待发布', className: 'bg-success/10 text-success' },
    rejected: { label: '已驳回', className: 'bg-destructive/10 text-destructive' },
    revision_requested: { label: '已打回', className: 'bg-warning/10 text-warning' },
    running: { label: '发布中', className: 'bg-info/10 text-info' },
    completed: { label: '已完成', className: 'bg-muted text-muted-foreground' },
  }
  const c = config[status] || { label: status, className: 'bg-muted text-muted-foreground' }
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${c.className}`}>
      {c.label}
    </span>
  )
}
