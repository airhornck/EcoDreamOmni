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
    quickActions: ['添加账号', '生成发布计划', '查看健康分'],
    actionCards: [
      {
        id: 'add-account',
        type: 'decision',
        title: '➕ 添加素人账号',
        description: '新增平台账号到矩阵中',
        priority: 1,
        actions: [
          { id: 'add_account', label: '添加账号', variant: 'primary' },
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
      {
        id: 'account-health',
        type: 'info',
        title: '💚 账号健康度',
        description: '查看矩阵中账号的健康分、风险等级与违规历史',
        priority: 3,
      },
    ],
  },

  /* ── 素材库 ── */
  '/assets': {
    welcomeMessage: '素材库管理。管理图片、视频等素材，支持 AI 批量打标签与一键应用到任务。',
    quickActions: ['上传素材', 'AI 打标签', '筛选未标签'],
    actionCards: [
      {
        id: 'upload-asset',
        type: 'decision',
        title: '📤 上传素材',
        description: '拖拽或选择文件上传至素材库',
        priority: 1,
        actions: [
          { id: 'upload_asset', label: '上传', variant: 'primary' },
        ],
      },
      {
        id: 'batch-tag',
        type: 'decision',
        title: '🏷️ AI 批量打标签',
        description: '为未打标签的素材自动生成标签',
        priority: 2,
        actions: [
          { id: 'auto_tag_assets', label: '开始打标签', variant: 'primary' },
        ],
      },
      {
        id: 'apply-asset-to-task',
        type: 'suggestion',
        title: '🚀 应用到任务',
        description: '选中素材后带入内容生产流程',
        priority: 3,
        actions: [
          { id: 'apply_to_task', label: '去创建任务', variant: 'secondary' },
        ],
      },
    ],
  },

  /* ── Agent 驾驶舱 ── */
  '/agents': {
    welcomeMessage: 'Agent 驾驶舱。查看 v4.0 Agent-First 舰队，与 TaskHub Step3 同款数据源。',
    quickActions: ['刷新列表'],
    actionCards: [
      {
        id: 'agent-refresh',
        type: 'decision',
        title: '🔄 刷新 Agent 列表',
        description: '重新拉取 Agent 舰队最新状态',
        priority: 1,
        actions: [
          { id: 'refresh', label: '刷新', variant: 'primary' },
        ],
      },
    ],
  },

  /* ── AI 引擎（原模型中心）── */
  '/models': {
    welcomeMessage: 'AI 引擎管理。注册 LLM 模型、配置账号池代理、监控成本与性能。',
    quickActions: ['新增模型', '新增代理', '查看成本', '查看日志'],
    actionCards: [
      {
        id: 'model-add',
        type: 'decision',
        title: '➕ 新增模型',
        description: '快速添加一个 AI 模型配置并测试连通性',
        priority: 1,
        actions: [
          { id: 'add_model', label: '添加', variant: 'primary' },
        ],
      },
      {
        id: 'proxy-add',
        type: 'decision',
        title: '🌐 新增代理',
        description: '添加新的 HTTP/SOCKS5 代理以提升调用稳定性',
        priority: 2,
        actions: [
          { id: 'add_proxy', label: '添加', variant: 'primary' },
        ],
      },
      {
        id: 'model-cost',
        type: 'info',
        title: '📊 成本看板',
        description: '查看最近 7 天模型调用成本与 token 消耗趋势',
        priority: 3,
        actions: [
          { id: 'view_cost', label: '查看', variant: 'secondary' },
        ],
      },
      {
        id: 'model-logs',
        type: 'info',
        title: '📜 调用日志',
        description: '浏览模型调用日志、延迟与错误分析',
        priority: 4,
        actions: [
          { id: 'view_logs', label: '查看', variant: 'secondary' },
        ],
      },
    ],
  },

  /* ── 实验室 ── */
  '/lab': {
    welcomeMessage: '实验室。使用 AI 能力进行爆款笔记分析、文案优化和模板生成。',
    quickActions: ['爆款分析', '标题优化', '封面生成', 'A/B 测试'],
    actionCards: [
      {
        id: 'lab-viral',
        type: 'decision',
        title: '🔥 爆款笔记分析',
        description: '粘贴爆款内容，AI 拆解结构并生成可复用模板',
        priority: 1,
        actions: [
          { id: 'open_viral_analyzer', label: '打开', variant: 'primary' },
        ],
      },
      {
        id: 'lab-title',
        type: 'info',
        title: '✍️ 标题优化器',
        description: '标题 A/B 测试与优化（计划 2026-Q3 上线）',
        priority: 2,
        actions: [
          { id: 'open_title_optimizer', label: '预览', variant: 'secondary' },
        ],
      },
      {
        id: 'lab-cover',
        type: 'info',
        title: '🖼️ 封面生成器',
        description: 'AI 封面设计与排版优化（计划 2026-Q3 上线）',
        priority: 3,
        actions: [
          { id: 'open_cover_generator', label: '预览', variant: 'secondary' },
        ],
      },
      {
        id: 'lab-ab',
        type: 'info',
        title: '🧪 A/B 测试',
        description: '多版本内容效果预测与对比（计划 2026-Q4 上线）',
        priority: 4,
        actions: [
          { id: 'open_ab_test', label: '预览', variant: 'secondary' },
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
    welcomeMessage: '系统设置。配置平台名称、API、通知与安全选项。',
    quickActions: ['通用', 'API', '通知', '安全', '保存'],
    actionCards: [
      {
        id: 'settings-general',
        type: 'info',
        title: '⚙️ 通用设置',
        description: '配置平台名称、默认平台与时区',
        priority: 1,
        actions: [
          { id: 'tab_general', label: '查看', variant: 'secondary' },
        ],
      },
      {
        id: 'settings-api',
        type: 'info',
        title: '🔑 API 配置',
        description: '设置 API 基地址与请求超时',
        priority: 2,
        actions: [
          { id: 'tab_api', label: '查看', variant: 'secondary' },
        ],
      },
      {
        id: 'settings-notify',
        type: 'info',
        title: '🔔 通知开关',
        description: '管理发布、合规、Agent 等消息通知',
        priority: 3,
        actions: [
          { id: 'tab_notifications', label: '查看', variant: 'secondary' },
        ],
      },
      {
        id: 'settings-security',
        type: 'info',
        title: '🛡️ 安全设置',
        description: '访问控制与密码策略',
        priority: 4,
        actions: [
          { id: 'tab_security', label: '查看', variant: 'secondary' },
        ],
      },
      {
        id: 'settings-save',
        type: 'decision',
        title: '💾 保存当前配置',
        description: '保存当前 Tab 下的设置项',
        priority: 5,
        actions: [
          { id: 'save', label: '保存', variant: 'primary' },
        ],
      },
    ],
  },

  /* ── 策略元素 ── */
  '/strategy-elements': {
    welcomeMessage: '策略元素管理中心。统一管理关键词策略、Hook 模式、结构框架、CTA 模式等可复用内容组件。',
    quickActions: ['创建元素', '爆款分析', '应用到任务'],
    actionCards: [
      {
        id: 'strategy-elements-create-default',
        type: 'decision',
        title: '➕ 创建策略元素',
        description: '手动创建一个新的策略元素，补充到内容策略库',
        priority: 1,
        actions: [
          { id: 'create_element', label: '开始创建', variant: 'primary' },
        ],
      },
      {
        id: 'strategy-elements-analyze-default',
        type: 'suggestion',
        title: '🧪 爆款分析提取',
        description: '前往实验室分析爆款笔记，自动提取策略元素',
        priority: 2,
        actions: [
          { id: 'go_lab', label: '去实验室', variant: 'secondary' },
        ],
      },
    ],
  },

  /* ── 平台规则 ── */
  '/rules': {
    welcomeMessage: '平台规则管理。配置 L1-L4 四层风控规则，支持试跑与状态切换。',
    quickActions: ['新建规则', '规则试跑', '切换状态'],
    actionCards: [
      {
        id: 'rule-create',
        type: 'decision',
        title: '➕ 新建平台规则',
        description: '创建一条新的 L1-L4 风控规则',
        priority: 1,
        actions: [
          { id: 'create_rule', label: '新建', variant: 'primary' },
        ],
      },
      {
        id: 'rule-test',
        type: 'decision',
        title: '🧪 规则试跑',
        description: '输入内容并测试当前平台规则命中情况',
        priority: 2,
        actions: [
          { id: 'test_rule', label: '试跑', variant: 'secondary' },
        ],
      },
      {
        id: 'rule-toggle',
        type: 'decision',
        title: '🔁 切换首条规则',
        description: '启用/禁用列表中的第一条规则',
        priority: 3,
        actions: [
          { id: 'toggle_rule', label: '切换', variant: 'secondary' },
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
    welcomeMessage: '代理配置中心。代理配置已合并到 AI 引擎，建议从左侧导航进入。',
    quickActions: ['新增代理', '测试连接', '切换状态', 'AI 引擎'],
    actionCards: [
      {
        id: 'proxy-create',
        type: 'decision',
        title: '➕ 新增代理',
        description: '添加新的 HTTP/SOCKS5 代理配置',
        priority: 1,
        actions: [
          { id: 'create_proxy', label: '添加', variant: 'primary' },
        ],
      },
      {
        id: 'proxy-test',
        type: 'decision',
        title: '🧪 测试首个代理',
        description: '对列表中的第一条代理进行连通性测试',
        priority: 2,
        actions: [
          { id: 'test_first_proxy', label: '测试', variant: 'secondary' },
        ],
      },
      {
        id: 'proxy-toggle',
        type: 'decision',
        title: '🔁 切换首条代理状态',
        description: '启用/禁用列表中的第一条代理',
        priority: 3,
        actions: [
          { id: 'toggle_first_proxy', label: '切换', variant: 'secondary' },
        ],
      },
      {
        id: 'proxy-to-engine',
        type: 'info',
        title: '🚀 前往 AI 引擎',
        description: '代理管理已合并至 AI 引擎，推荐统一入口',
        priority: 4,
        actions: [
          { id: 'goto_engine', label: '前往', variant: 'secondary' },
        ],
      },
    ],
  },
  '/timeline': {
    welcomeMessage: '时间线视图。查看账号矩阵的历史发布记录。',
    quickActions: ['查看记录', '筛选'],
    actionCards: [],
  },
  '/vetdrug': {
    welcomeMessage: '兽药批文库。录入批文、宣称校验、到期预警与产品关联。',
    quickActions: ['新增批文', '宣称校验', '到期预警', 'CSV 导入'],
    actionCards: [
      {
        id: 'vet-create',
        type: 'decision',
        title: '➕ 新增兽药批文',
        description: '录入新的兽药批准文号及产品信息',
        priority: 1,
        actions: [
          { id: 'create_drug', label: '新增', variant: 'primary' },
        ],
      },
      {
        id: 'vet-validate',
        type: 'decision',
        title: '🛡️ 宣称校验',
        description: '校验产品宣称适应症是否在批文范围内',
        priority: 2,
        actions: [
          { id: 'validate_claim', label: '校验', variant: 'primary' },
        ],
      },
      {
        id: 'vet-expiry',
        type: 'info',
        title: '⏰ 到期预警',
        description: '查看 90 天内即将过期或已失效的批文',
        priority: 3,
        actions: [
          { id: 'expiry_warnings', label: '查看', variant: 'secondary' },
        ],
      },
      {
        id: 'vet-import',
        type: 'decision',
        title: '📤 CSV 批量导入',
        description: '通过 CSV 批量导入兽药批文数据',
        priority: 4,
        actions: [
          { id: 'bulk_import', label: '导入', variant: 'secondary' },
        ],
      },
    ],
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
