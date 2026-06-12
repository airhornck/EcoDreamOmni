/**
 * Copilot 页面默认配置 — 后端 action-cards 接口返回空时的优雅降级
 *
 * ⚠️ 临时兜底：当后端 `GET /api/ai/copilot/action-cards` 覆盖全部页面后，
 *    本文件可标记为 deprecated 并逐步移除。
 *
 * 设计原则：
 * - 仅提供导航级 Action Cards（不依赖页面内部状态）
 * - 每个页面至少 1 个默认 Action Card + 1 条欢迎语 + 1-2 个 Quick Action
 * - 页面级复杂集成（如 TaskHubCreatePage 的 Step 3 确认创建）仍由页面组件自行注入
 */

import type { PageActionCard } from '../stores/aiCopilotStore'

export interface PageCopilotDefaultConfig {
  welcomeMessage: string
  quickActions: string[]
  actionCards: PageActionCard[]
}

/** 页面路由 → 默认 Copilot 配置 */
export const DEFAULT_PAGE_COPILOT_CONFIG: Record<string, PageCopilotDefaultConfig> = {
  /* ── 工作台 ── */
  '/': {
    welcomeMessage: '欢迎回到工作台。可查看今日待办、账号健康度或生成 AI 战报。',
    quickActions: ['查看趋势', '新建任务'],
    actionCards: [
      {
        id: 'dashboard-overview',
        type: 'info',
        title: '📊 工作台概览',
        description: '查看矩阵数据、待审内容和今日发布计划',
        priority: 1,
      },
      {
        id: 'dashboard-create-task',
        type: 'decision',
        title: '➕ 快速创建任务',
        description: '输入主题+平台，快速创建内容生产任务',
        priority: 2,
        actions: [
          { id: 'create_task', label: '前往创建', variant: 'primary' },
        ],
      },
    ],
  },

  /* ── 内容生产 ── */
  '/generate': {
    welcomeMessage: '管理内容生产任务。可新建任务、查看进度或批量操作。',
    quickActions: ['新建内容', '查看全部'],
    actionCards: [
      {
        id: 'create-content-default',
        type: 'decision',
        title: '➕ 新建内容',
        description: '输入主题+平台，快速创建内容任务',
        priority: 1,
        actions: [
          { id: 'quick_create', label: '快速创建', variant: 'primary' },
          { id: 'open_wizard', label: '完整向导', variant: 'secondary' },
        ],
      },
      {
        id: 'agent-recommend',
        type: 'info',
        title: '🤖 Agent 推荐',
        description: '根据近期数据，小红书图文 Agent 成功率 94%，建议使用',
        priority: 2,
      },
    ],
  },

  '/generate/create': {
    welcomeMessage: '配置任务参数，完成后进入第 4 步确认创建',
    quickActions: ['上一步', '下一步', '取消'],
    actionCards: [
      {
        id: 'wizard-progress',
        type: 'info',
        title: '📝 创建向导',
        description: '当前步骤：配置中。完成全部 4 步后可在 Copilot 中确认创建。',
        priority: 1,
      },
    ],
  },

  '/generate/editor': {
    welcomeMessage: '编辑内容草稿。完成后可保存或提交审核。',
    quickActions: ['保存草稿', '提交审核', '重新生成'],
    actionCards: [
      {
        id: 'save-draft',
        type: 'decision',
        title: '💾 保存草稿',
        description: '保存当前编辑内容',
        priority: 1,
        actions: [
          { id: 'save', label: '保存', variant: 'primary' },
        ],
      },
      {
        id: 'submit-review',
        type: 'decision',
        title: '🚀 提交审核',
        description: '保存并提交至审核发布中心',
        priority: 2,
        actions: [
          { id: 'save_and_submit', label: '保存并提交', variant: 'primary' },
        ],
      },
      {
        id: 'regenerate',
        type: 'decision',
        title: '🔄 重新生成',
        description: '使用不同风格重新生成内容',
        priority: 3,
        actions: [
          { id: 'regenerate', label: '重新生成', variant: 'primary' },
        ],
      },
    ],
  },

  /* ── 审核发布 ── */
  '/review': {
    welcomeMessage: '审核发布中心。查看待审内容、审核决策和发布计划。',
    quickActions: ['查看待审', '批量审核'],
    actionCards: [
      {
        id: 'review-pending',
        type: 'info',
        title: '🛡️ 待审内容',
        description: '查看待人工审核的内容列表',
        priority: 1,
      },
    ],
  },

  '/review/:taskId': {
    welcomeMessage: '审核详情页。查看内容合规分、质量分和审核决策建议。',
    quickActions: ['通过', '打回', '驳回'],
    actionCards: [
      {
        id: 'review-decision',
        type: 'decision',
        title: '审核决策',
        description: '查看合规分和质量分，进行审核决策',
        priority: 1,
        actions: [
          { id: 'approve', label: '✅ 通过', variant: 'primary' },
          { id: 'revise', label: '🔄 打回', variant: 'secondary' },
          { id: 'reject', label: '❌ 驳回', variant: 'ghost' },
        ],
      },
      {
        id: 'generate-cover',
        type: 'generation',
        title: '🎨 生成封面',
        description: '为内容生成 AI 封面图',
        priority: 2,
        actions: [
          { id: 'generate_cover', label: '生成封面', variant: 'primary' },
        ],
      },
    ],
  },

  /* ── 数据报表 ── */
  '/analytics': {
    welcomeMessage: '数据报表中心。查看账号矩阵数据、互动趋势和 AI 洞察。',
    quickActions: ['生成战报', '查看趋势'],
    actionCards: [
      {
        id: 'generate-report',
        type: 'decision',
        title: '📋 生成 AI 战报',
        description: '基于近期数据生成自然语言总结报告',
        priority: 1,
        actions: [
          { id: 'generate_report', label: '生成战报', variant: 'primary' },
        ],
      },
      {
        id: 'export-data',
        type: 'decision',
        title: '📤 导出数据',
        description: '导出当前报表数据为 Excel/CSV',
        priority: 2,
        actions: [
          { id: 'export', label: '导出', variant: 'secondary' },
        ],
      },
    ],
  },

  /* ── 账号矩阵 ── */
  '/accounts': {
    welcomeMessage: '账号矩阵管理。查看素人账号健康度、发布计划和人设配置。',
    quickActions: ['添加账号', '生成发布计划'],
    actionCards: [
      {
        id: 'add-account',
        type: 'decision',
        title: '➕ 添加素人账号',
        description: '新增平台账号到矩阵中',
        priority: 1,
        actions: [
          { id: 'add', label: '添加账号', variant: 'primary' },
        ],
      },
      {
        id: 'publish-schedule',
        type: 'decision',
        title: '📅 生成发布计划',
        description: '基于账号历史数据生成最优发布时间表',
        priority: 2,
        actions: [
          { id: 'generate_schedule', label: '生成计划', variant: 'primary' },
        ],
      },
    ],
  },

  /* ── 素材库 ── */
  '/assets': {
    welcomeMessage: '素材库管理。管理图片、视频等素材，支持 AI 批量打标签。',
    quickActions: ['上传素材', 'AI 打标签'],
    actionCards: [
      {
        id: 'upload-asset',
        type: 'decision',
        title: '📤 上传素材',
        description: '拖拽或选择文件上传至素材库',
        priority: 1,
        actions: [
          { id: 'upload', label: '上传', variant: 'primary' },
        ],
      },
      {
        id: 'batch-tag',
        type: 'decision',
        title: '🏷️ AI 批量打标签',
        description: '为未打标签的素材自动生成标签',
        priority: 2,
        actions: [
          { id: 'auto_tag', label: '开始打标签', variant: 'primary' },
        ],
      },
    ],
  },

  /* ── Agent 舰队 ── */
  '/agents': {
    welcomeMessage: 'Agent 舰队管理。查看 Agent 状态、部署新 Agent 或调整配置。',
    quickActions: ['部署 Agent', '查看状态'],
    actionCards: [
      {
        id: 'deploy-agent',
        type: 'decision',
        title: '🚀 部署 Agent',
        description: '部署新的 AI Agent 到生产环境',
        priority: 1,
        actions: [
          { id: 'deploy', label: '部署', variant: 'primary' },
        ],
      },
      {
        id: 'agent-status',
        type: 'info',
        title: '📊 Agent 状态',
        description: '查看所有 Agent 的运行状态和队列情况',
        priority: 2,
      },
    ],
  },

  /* ── 模型中心 ── */
  '/models': {
    welcomeMessage: '模型管理中心。查看 LLM 模型配置、成本监控和性能基准。',
    quickActions: ['切换模型', '运行基准测试'],
    actionCards: [
      {
        id: 'switch-model',
        type: 'decision',
        title: '⚡ 切换模型',
        description: '切换至其他 LLM 提供商或模型版本',
        priority: 1,
        actions: [
          { id: 'switch', label: '切换', variant: 'primary' },
        ],
      },
      {
        id: 'benchmark',
        type: 'decision',
        title: '📊 运行基准测试',
        description: '对比不同模型的性能和质量',
        priority: 2,
        actions: [
          { id: 'benchmark', label: '运行测试', variant: 'secondary' },
        ],
      },
    ],
  },

  /* ── 实验室 ── */
  '/lab': {
    welcomeMessage: '实验室。使用 AI 能力进行爆款笔记分析、文案优化和模板生成。',
    quickActions: ['分析笔记', '生成模板'],
    actionCards: [
      {
        id: 'analyze-note',
        type: 'decision',
        title: '🔍 爆款笔记分析',
        description: '输入小红书笔记链接，分析其爆款结构',
        priority: 1,
        actions: [
          { id: 'analyze', label: '开始分析', variant: 'primary' },
        ],
      },
      {
        id: 'generate-template',
        type: 'decision',
        title: '📝 生成模板',
        description: '基于分析报告生成可复用的 ContentTemplate',
        priority: 2,
        actions: [
          { id: 'generate_template', label: '生成模板', variant: 'primary' },
        ],
      },
    ],
  },

  /* ── 关键词库 ── */
  '/keywords': {
    welcomeMessage: '关键词库管理。查看、添加和推荐高热度关键词。',
    quickActions: ['添加关键词', '查看推荐'],
    actionCards: [
      {
        id: 'add-keyword',
        type: 'decision',
        title: '➕ 添加关键词',
        description: '手动添加或批量导入关键词',
        priority: 1,
        actions: [
          { id: 'add_kw', label: '添加', variant: 'primary' },
        ],
      },
      {
        id: 'recommend-kw',
        type: 'decision',
        title: '💡 关键词推荐',
        description: '基于近期爆款内容推荐高热度关键词',
        priority: 2,
        actions: [
          { id: 'recommend', label: '查看推荐', variant: 'secondary' },
        ],
      },
    ],
  },

  /* ── 模板库 ── */
  '/templates': {
    welcomeMessage: '模板库管理。查看、创建和使用 ContentTemplate。',
    quickActions: ['使用模板', '创建模板'],
    actionCards: [
      {
        id: 'use-template',
        type: 'decision',
        title: '📋 使用模板',
        description: '选择模板并应用到内容生产',
        priority: 1,
        actions: [
          { id: 'use', label: '选择模板', variant: 'primary' },
        ],
      },
      {
        id: 'create-template',
        type: 'decision',
        title: '➕ 创建模板',
        description: '基于现有内容创建新的 ContentTemplate',
        priority: 2,
        actions: [
          { id: 'create_tpl', label: '创建', variant: 'secondary' },
        ],
      },
    ],
  },

  /* ── 设置 ── */
  '/settings': {
    welcomeMessage: '系统设置。配置账号、通知、权限和平台规则。',
    quickActions: ['保存设置', '重置'],
    actionCards: [
      {
        id: 'save-settings',
        type: 'decision',
        title: '💾 保存设置',
        description: '保存当前所有配置更改',
        priority: 1,
        actions: [
          { id: 'save', label: '保存', variant: 'primary' },
        ],
      },
      {
        id: 'reset-settings',
        type: 'decision',
        title: '🔄 重置',
        description: '将所有设置恢复为默认值',
        priority: 2,
        actions: [
          { id: 'reset', label: '重置', variant: 'ghost' },
        ],
      },
    ],
  },

  /* ── 工作流编排 ── */
  '/workflows': {
    welcomeMessage: '工作流编排中心。设计、部署和管理自动化工作流。',
    quickActions: ['创建工作流', '运行工作流'],
    actionCards: [
      {
        id: 'create-workflow',
        type: 'decision',
        title: '➕ 创建工作流',
        description: '设计新的自动化工作流',
        priority: 1,
        actions: [
          { id: 'create_wf', label: '创建', variant: 'primary' },
        ],
      },
      {
        id: 'run-workflow',
        type: 'decision',
        title: '▶️ 运行工作流',
        description: '手动触发工作流执行',
        priority: 2,
        actions: [
          { id: 'run_wf', label: '运行', variant: 'secondary' },
        ],
      },
    ],
  },

  /* ── 平台规则 ── */
  '/rules': {
    welcomeMessage: '平台规则管理。配置各平台的发布规则、合规要求和限制。',
    quickActions: ['添加规则', '测试规则'],
    actionCards: [
      {
        id: 'add-rule',
        type: 'decision',
        title: '➕ 添加规则',
        description: '新增平台规则或合规要求',
        priority: 1,
        actions: [
          { id: 'add_rule', label: '添加', variant: 'primary' },
        ],
      },
      {
        id: 'test-rule',
        type: 'decision',
        title: '🧪 测试规则',
        description: '验证规则配置是否正确',
        priority: 2,
        actions: [
          { id: 'test_rule', label: '测试', variant: 'secondary' },
        ],
      },
    ],
  },

  /* ── 子功能路由兜底 ── */
  '/compliance': {
    welcomeMessage: '合规检查中心。扫描内容合规风险并生成报告。',
    quickActions: ['扫描内容', '查看报告'],
    actionCards: [],
  },
  '/publisher': {
    welcomeMessage: '发布管理中心。管理已发布内容和发布计划。',
    quickActions: ['查看计划', '批量发布'],
    actionCards: [],
  },
  '/engagement-tracking': {
    welcomeMessage: '互动追踪中心。监控内容互动数据和用户反馈。',
    quickActions: ['查看趋势', '生成报告'],
    actionCards: [],
  },
  '/skillhub': {
    welcomeMessage: '技能库管理。查看和管理 Agent 可用的技能。',
    quickActions: ['添加技能', '查看技能'],
    actionCards: [],
  },
  '/cron-cockpit': {
    welcomeMessage: '定时任务中心。配置和管理 Cron 定时任务。',
    quickActions: ['创建任务', '查看日志'],
    actionCards: [],
  },
  '/platform-rules/schema': {
    welcomeMessage: '平台 Schema 管理。配置各平台的内容格式和字段要求。',
    quickActions: ['添加 Schema', '查看配置'],
    actionCards: [],
  },
  '/proxy-config': {
    welcomeMessage: '代理配置中心。管理网络代理和 API 密钥配置。',
    quickActions: ['添加代理', '测试连接'],
    actionCards: [],
  },
  '/timeline': {
    welcomeMessage: '时间线视图。查看账号矩阵的历史发布记录。',
    quickActions: ['查看记录', '筛选'],
    actionCards: [],
  },
  '/vetdrug': {
    welcomeMessage: '兽药查询中心。查询宠物用药信息和合规要求。',
    quickActions: ['查询药品', '查看说明'],
    actionCards: [],
  },
  '/predictions': {
    welcomeMessage: '预测分析中心。基于历史数据预测内容表现趋势。',
    quickActions: ['生成预测', '查看模型'],
    actionCards: [],
  },
}

/** 根据路由匹配默认配置（支持动态路由前缀匹配） */
export function getPageCopilotDefaultConfig(pathname: string): PageCopilotDefaultConfig | null {
  // 1. 精确匹配
  if (DEFAULT_PAGE_COPILOT_CONFIG[pathname]) {
    return DEFAULT_PAGE_COPILOT_CONFIG[pathname]
  }

  // 2. 最长前缀匹配（避免 /generate/create 被 /generate 错误匹配）
  // 排序：最长键优先，确保子路由优先于父路由
  const candidates = Object.keys(DEFAULT_PAGE_COPILOT_CONFIG)
    .filter((k) => pathname.startsWith(k + '/'))
    .sort((a, b) => b.length - a.length)

  if (candidates.length > 0) {
    return DEFAULT_PAGE_COPILOT_CONFIG[candidates[0]]
  }

  // 3. 兜底：无前缀匹配时返回 null
  return null
}
