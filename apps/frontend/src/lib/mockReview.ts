/**
 * 审核发布业务 Mock 服务 — v4.0 Step 3 前端并行开发
 * 后端 Sprint 2 就绪前，前端使用此 mock 继续开发
 *
 * 覆盖:
 *   - GET /api/review-publish-center/conclusions
 *   - GET /api/review-publish-center/conclusions/{id}
 *   - POST /api/human-in-the-loop/tasks/{id}/approve|reject|revise
 *   - PUT /api/review-publish-center/conclusions/{id}/content
 *   - POST /api/review-publish-center/conclusions/{id}/confirm-publish
 *   - POST /api/review-publish-center/conclusions/{id}/regenerate
 */

import type { ReviewConclusion, ReviewDetail } from '../stores/reviewPublishStore'

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

// ───────────────────────────────────────────────
// Mock Data
// ───────────────────────────────────────────────

const MOCK_CONCLUSIONS: ReviewConclusion[] = [
  {
    task_id: 'task_demo_001',
    task_name: '猫咪驱虫避坑指南',
    content_title: '猫咪驱虫避坑指南，这3个误区90%的人都不知道',
    platform: 'xhs',
    account_name: '小艾养猫记',
    status: 'human_wait',
    review_decision: null,
    reviewed_at: null,
    reviewer: null,
    review_reason: null,
    content_preview: '作为一个养猫3年的铲屎官，我发现很多新手在驱虫这件事上踩了不少坑...',
    waiting_since: new Date(Date.now() - 7200000).toISOString(),
    priority: 80,
    risk_level: 'low',
    can_publish_now: false,
    has_cron_job: false,
    compliance_score: 96,
    quality_score: 88,
    cover_image_url: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400',
  },
  {
    task_id: 'task_demo_002',
    task_name: '第一次带猫体检',
    content_title: '第一次带猫体检全流程，新手必看',
    platform: 'xhs',
    account_name: '小艾养猫记',
    status: 'human_wait',
    review_decision: null,
    reviewed_at: null,
    reviewer: null,
    review_reason: null,
    content_preview: '带猫咪第一次去体检，需要注意哪些事项？今天一次性讲清楚...',
    waiting_since: new Date(Date.now() - 3600000).toISOString(),
    priority: 70,
    risk_level: 'low',
    can_publish_now: false,
    has_cron_job: false,
    compliance_score: 92,
    quality_score: 85,
    cover_image_url: 'https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=400',
  },
  {
    task_id: 'task_demo_003',
    task_name: '狗狗洗澡频率指南',
    content_title: '狗狗多久洗一次澡？不同季节频率不同',
    platform: 'douyin',
    account_name: '狗哥日记',
    status: 'human_wait',
    review_decision: null,
    reviewed_at: null,
    reviewer: null,
    review_reason: null,
    content_preview: '很多铲屎官问我狗狗到底多久洗一次澡...',
    waiting_since: new Date(Date.now() - 1800000).toISOString(),
    priority: 60,
    risk_level: 'medium',
    can_publish_now: false,
    has_cron_job: false,
    compliance_score: 78,
    quality_score: 72,
    cover_image_url: null,
  },
]

function buildMockDetail(taskId: string): ReviewDetail {
  const base = MOCK_CONCLUSIONS.find((c) => c.task_id === taskId)
  if (!base) {
    throw new Error(`Task ${taskId} not found`)
  }

  return {
    task_id: base.task_id,
    task_name: base.task_name,
    platform: base.platform,
    status: base.status,
    content_preview: base.content_preview,
    generated_content: {
      title: base.content_title || base.task_name,
      body: `${base.content_preview}\n\n正文详细内容...\n\n## 第一个误区\n很多人认为驱虫药越贵越好，其实...\n\n## 第二个误区\n驱虫频率不是越多越好...\n\n## 第三个误区\n体内体外驱虫可以同时进行...`,
      tags: ['驱虫', '新手养猫', '养宠攻略', '猫咪健康'],
      platform: base.platform,
      content_type: 'note_image',
      cover_image_url: base.cover_image_url || undefined,
      cover_image_ratio: '3:4',
      images: base.cover_image_url ? [base.cover_image_url] : [],
    },
    agent_summary: 'Agent 执行摘要：选题通过 → 结构生成 → 正文撰写 → 合规检查(L1-L4通过) → 互动预演',
    compliance_result: {
      level: base.compliance_score && base.compliance_score >= 85 ? 'pass' : 'warning',
      violations: base.compliance_score && base.compliance_score < 80 ? ['图片建议添加来源标注'] : [],
      l1_check: true,
      l2_check: true,
      l3_check: true,
      l4_check: base.compliance_score ? base.compliance_score >= 80 : true,
    },
    prediction_result: {
      engagement_interval: { likes: '25-60', comments: '5-15', saves: '10-30' },
      viral_probability: 0.72,
      best_publish_time: '18:00',
    },
    quality_score: {
      overall: base.quality_score || 80,
      dimensions: {
        title_attractiveness: 85,
        body_completeness: 90,
        tag_relevance: 88,
        readability: 92,
        engagement_potential: 86,
        compliance: base.compliance_score || 80,
      },
    },
    injection_context: {},
    topic_report: {
      report_id: 'rpt_001',
      selected_topic: '猫咪驱虫',
      topics: [
        { id: 't1', title: '猫咪驱虫避坑指南', source_report: 'rpt_001', estimated_engagement: 0.85, tags: ['驱虫', '新手'], status: 'selected' },
        { id: 't2', title: '驱虫药品牌对比', source_report: 'rpt_001', estimated_engagement: 0.72, tags: ['驱虫', '评测'], status: 'alternative' },
      ],
      '5a_stage': 'action',
      audience_fit_score: 0.91,
    },
    cover_image_url: base.cover_image_url ?? null,
    review_history: [],
    risk_level: base.risk_level,
    can_publish: base.status === 'approved_waiting_publish',
    has_primary_approval: false,
    account_id: 'acc_001',
    account_name: base.account_name,
    draft_id: 'draft_001',
    cron_schedule: null,
    copilot_context: {
      recommended_action: base.compliance_score && base.compliance_score >= 85 ? 'approve' : 'revise',
      confidence: 0.94,
      reasoning: `合规分 ${base.compliance_score} 分，L1-L4 全部通过，质量分 ${base.quality_score} 分`,
      risk_factors: base.compliance_score && base.compliance_score < 80 ? ['合规分偏低'] : [],
      suggested_improvements:
        base.compliance_score && base.compliance_score >= 90
          ? ['标题加入具体数字可提升点击率', '文末添加驱虫时间表卡片']
          : ['补充图片来源标注', '调整标题关键词密度'],
    },
    available_copilot_cards: ['review-decision', 'cover-generation', 'title-optimization'],
  }
}

// ───────────────────────────────────────────────
// Mock API
// ───────────────────────────────────────────────

export async function mockFetchConclusions(statusFilter?: string): Promise<{
  items: ReviewConclusion[]
  copilot_summary?: {
    total_pending: number
    recommended_priority: string[]
    batch_suggestion: string
  }
}> {
  await delay(400)

  let items = [...MOCK_CONCLUSIONS]

  if (statusFilter && statusFilter !== 'all') {
    if (statusFilter === 'pending') items = items.filter((i) => i.status === 'human_wait')
    if (statusFilter === 'approved') items = items.filter((i) => i.review_decision === 'APPROVE')
    if (statusFilter === 'rejected') items = items.filter((i) => i.review_decision === 'REJECT')
    if (statusFilter === 'revised') items = items.filter((i) => i.review_decision === 'REVISE')
  }

  const pending = items.filter((i) => i.status === 'human_wait')

  return {
    items,
    copilot_summary: {
      total_pending: pending.length,
      recommended_priority: pending.sort((a, b) => (b.compliance_score || 0) - (a.compliance_score || 0)).map((i) => i.task_id),
      batch_suggestion: `${pending.length} 条待审中，${pending.filter((i) => (i.compliance_score || 0) < 80).length} 条合规分低于 80 分建议优先处理。`,
    },
  }
}

export async function mockFetchDetail(taskId: string): Promise<ReviewDetail> {
  await delay(300)
  return buildMockDetail(taskId)
}

export async function mockDecideTask(
  _taskId: string,
  decision: 'approve' | 'reject' | 'revise',
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _reason?: string,
): Promise<{ success: boolean; status?: string; copilot_followup?: { message: string; suggested_cards: Array<Record<string, unknown>> } }> {
  await delay(500)

  const newStatus =
    decision === 'approve'
      ? 'approved_waiting_publish'
      : decision === 'reject'
        ? 'rejected'
        : 'revision_requested'

  const result: { success: boolean; status: string; copilot_followup?: { message: string; suggested_cards: Array<Record<string, unknown>> } } = {
    success: true,
    status: newStatus,
  }

  if (decision === 'approve') {
    result.copilot_followup = {
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
    }
  }

  return result
}

export async function mockUpdateContent(
  taskId: string,
  patch: { title?: string; body?: string; tags?: string[]; cover_image_url?: string },
): Promise<{ success: boolean; updated_at?: string }> {
  await delay(300)
  const item = MOCK_CONCLUSIONS.find((c) => c.task_id === taskId)
  if (item && patch.title) item.content_title = patch.title
  return { success: true, updated_at: new Date().toISOString() }
}

export async function mockConfirmPublish(
  _taskId: string,
  config: { publish_mode: string; scheduled_at?: string; cron_schedule?: string },
): Promise<{ success: boolean; publish_task_id?: string; cron_job_id?: string }> {
  await delay(400)
  return {
    success: true,
    publish_task_id: `pub_${Date.now()}`,
    cron_job_id: config.cron_schedule ? `cron_${Date.now()}` : undefined,
  }
}

export async function mockRegenerate(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _taskId: string,
): Promise<{ success: boolean; status?: string; message?: string }> {
  await delay(300)
  return { success: true, status: 'regenerating', message: '已提交重新生成，预计 30 秒完成' }
}
