/**
 * Copilot 通用 Mock 服务 — v4.0 Step 3 前端并行开发
 * 后端 Sprint 1 就绪前，前端使用此 mock 继续开发
 *
 * 覆盖:
 *   - POST /api/ai/copilot/context
 *   - GET /api/ai/copilot/action-cards
 *   - POST /api/ai/copilot/execute
 *   - POST /api/ai/generate-cover
 *   - GET /api/ai/generate-cover/{job_id}
 */

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

// ───────────────────────────────────────────────
// Types
// ───────────────────────────────────────────────

export interface CopilotContextPayload {
  session_id: string
  page: string
  page_title?: string
  selected_items: string[]
  selected_content?: Record<string, unknown>
  workspace_state?: Record<string, unknown>
}

export interface CopilotContextResult {
  context_id: string
  suggested_cards: Array<{
    card_type: string
    priority: number
    target_page: string
    reasoning: string
  }>
  ai_insights: string[]
}

export interface ActionCard {
  id: string
  type: 'decision' | 'generation' | 'suggestion' | 'info'
  title: string
  description: string
  priority: number
  inputs: Array<{
    name: string
    label: string
    type: string
    placeholder?: string
  }>
  actions: Array<{
    id: string
    label: string
    variant: 'primary' | 'secondary' | 'ghost'
    api?: { method: string; endpoint: string; payload: Record<string, unknown> }
    needs_reason?: boolean
  }>
}

export interface CopilotExecutePayload {
  context_id?: string
  card_id: string
  action_id: string
  inputs?: Record<string, unknown>
  payload?: Record<string, unknown>
}

export interface CopilotFollowup {
  message: string
  suggested_cards: Array<{
    type: string
    title: string
    actions: Array<{ id: string; label: string }>
  }>
}

export interface GenerateCoverPayload {
  task_id: string
  prompt?: string
  auto_prompt?: boolean
  content_summary?: string
  style_preset?: string
  count?: number
  ratio?: string
}

export interface CoverJobResult {
  job_id: string
  status: 'queued' | 'generating' | 'completed' | 'failed'
  results?: Array<{
    url: string
    thumbnail_url: string
    ratio: string
    prompt_used: string
    seed: number
  }>
  completed_at?: string
}

// ───────────────────────────────────────────────
// Mock: Context
// ───────────────────────────────────────────────

export async function mockCopilotContext(
  payload: CopilotContextPayload,
): Promise<CopilotContextResult> {
  await delay(150)

  const suggestedCards: CopilotContextResult['suggested_cards'] = []
  const aiInsights: string[] = []

  if (payload.page === '/review') {
    if (payload.selected_items.length > 0) {
      suggestedCards.push(
        { card_type: 'decision', priority: 1, target_page: '/review', reasoning: '选中待审任务，建议进行审核决策' },
        { card_type: 'generation', priority: 2, target_page: '/review', reasoning: '可为当前任务生成封面' },
      )
    } else {
      suggestedCards.push(
        { card_type: 'suggestion', priority: 1, target_page: '/review', reasoning: '列表模式，建议批量审核' },
      )
      aiInsights.push('3 条待审中，1 条合规分低于 80 分建议优先处理')
    }
  }

  return {
    context_id: `ctx_${Date.now().toString(36)}`,
    suggested_cards: suggestedCards,
    ai_insights: aiInsights,
  }
}

// ───────────────────────────────────────────────
// Mock: Action Cards
// ───────────────────────────────────────────────

export async function mockGetActionCards(
  page: string,
  taskId?: string,
): Promise<{ cards: ActionCard[] }> {
  await delay(200)

  const cards: ActionCard[] = []

  if (page === '/review' && taskId) {
    cards.push({
      id: `review-decision-${taskId}`,
      type: 'decision',
      title: '审核决策',
      description: '合规分 96 分，质量分 88 分，L1-L4 全部通过。建议直接通过。',
      priority: 1,
      inputs: [],
      actions: [
        {
          id: 'approve',
          label: '✅ 审核通过',
          variant: 'primary',
          api: { method: 'POST', endpoint: `/api/human-in-the-loop/tasks/${taskId}/approve`, payload: {} },
        },
        {
          id: 'revise',
          label: '🔄 打回修改',
          variant: 'secondary',
          needs_reason: true,
        },
        {
          id: 'reject',
          label: '❌ 驳回',
          variant: 'ghost',
          needs_reason: true,
        },
      ],
    })
    cards.push({
      id: `cover-gen-${taskId}`,
      type: 'generation',
      title: '🎨 生成封面',
      description: '让 AI 根据内容生成封面图',
      priority: 2,
      inputs: [
        {
          name: 'prompt',
          label: '描述',
          type: 'textarea',
          placeholder: '描述你想要的封面风格...',
        },
      ],
      actions: [
        {
          id: 'generate',
          label: '生成封面',
          variant: 'primary',
          api: { method: 'POST', endpoint: '/api/ai/generate-cover', payload: { task_id: taskId } },
        },
      ],
    })
  } else if (page === '/review') {
    cards.push({
      id: 'batch-review-list',
      type: 'suggestion',
      title: '批量审核',
      description: '选中多条内容后可批量处理',
      priority: 1,
      inputs: [],
      actions: [
        { id: 'batch_approve', label: '批量通过', variant: 'primary' },
        { id: 'batch_revise', label: '批量打回', variant: 'secondary' },
      ],
    })
    cards.push({
      id: 'ai-analysis-list',
      type: 'info',
      title: 'AI 分析',
      description: '3 条待审中，1 条合规分低于 80 分建议优先处理',
      priority: 2,
      inputs: [],
      actions: [],
    })
  }

  return { cards }
}

// ───────────────────────────────────────────────
// Mock: Execute Action
// ───────────────────────────────────────────────

export async function mockExecuteAction(
  payload: CopilotExecutePayload,
): Promise<{ success: boolean; data: Record<string, unknown>; copilot_followup?: CopilotFollowup }> {
  await delay(600)

  // Simulate approve → publish confirmation followup
  if (payload.action_id === 'approve') {
    return {
      success: true,
      data: { status: 'approved_waiting_publish' },
      copilot_followup: {
        message: '审核已通过！合规分 96 分，质量优秀。要现在发布还是定时发布？',
        suggested_cards: [
          {
            type: 'decision',
            title: '发布确认',
            actions: [
              { id: 'publish_now', label: '立即发布' },
              { id: 'schedule', label: '定时发布' },
            ],
          },
        ],
      },
    }
  }

  return {
    success: true,
    data: { executed: true, card_id: payload.card_id, action_id: payload.action_id },
  }
}

// ───────────────────────────────────────────────
// Mock: Cover Generation
// ───────────────────────────────────────────────

export async function mockGenerateCover(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _payload: GenerateCoverPayload,
): Promise<{ job_id: string; status: string; estimated_seconds: number }> {
  await delay(200)
  return {
    job_id: `mock_cover_${Date.now()}`,
    status: 'queued',
    estimated_seconds: 8,
  }
}

export async function mockGetCoverStatus(jobId: string): Promise<CoverJobResult> {
  await delay(300)
  return {
    job_id: jobId,
    status: 'completed',
    results: [
      {
        url: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600',
        thumbnail_url: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=200',
        ratio: '3:4',
        prompt_used: '温馨可爱的猫咪，阳光照射',
        seed: 42,
      },
      {
        url: 'https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=600',
        thumbnail_url: 'https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=200',
        ratio: '3:4',
        prompt_used: '温馨可爱的猫咪，阳光照射',
        seed: 43,
      },
    ],
    completed_at: new Date().toISOString(),
  }
}
