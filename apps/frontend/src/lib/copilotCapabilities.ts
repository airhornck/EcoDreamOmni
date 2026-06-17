/**
 * Copilot Capability Registry — Frontend Navigate Map
 *
 * 前端只保留纯导航类能力（不需要后端执行逻辑）。
 * 所有业务类 action（审核、生成、发布等）统一通过 /api/ai/copilot/agent 路由到后端
 * CapabilityRegistry + MetaOrchestrator 动态执行。
 *
 * Phase 2 对齐后端 CAPABILITY_REGISTRY（src/services/copilot_action_router.py）。
 */

export type NavigateCapability = {
  type: 'navigate'
  target: string
}

/** 前端纯导航能力表：action_id → navigate target */
export const FRONTEND_NAVIGATE_MAP: Record<string, NavigateCapability> = {
  // Dashboard
  create: { type: 'navigate', target: '/generate/create' },
  review: { type: 'navigate', target: '/review' },
  publish: { type: 'navigate', target: '/review' },

  // Generate
  create_task: { type: 'navigate', target: '/generate/create' },
  quick_create: { type: 'navigate', target: '/generate/create' },
  open_wizard: { type: 'navigate', target: '/generate/create' },
  browse_templates: { type: 'navigate', target: '/templates' },

  // Analytics
  generate: { type: 'navigate', target: '/analytics' },
  export: { type: 'navigate', target: '/analytics' },

  // Accounts
  add: { type: 'navigate', target: '/accounts' },
  check: { type: 'navigate', target: '/accounts' },

  // Assets
  upload: { type: 'navigate', target: '/assets' },
  auto_tag: { type: 'navigate', target: '/assets' },

  // Agents
  deploy: { type: 'navigate', target: '/agents' },
  monitor: { type: 'navigate', target: '/agents' },

  // Models
  switch: { type: 'navigate', target: '/models' },
  benchmark: { type: 'navigate', target: '/models' },

  // Settings
  save: { type: 'navigate', target: '/settings' },
  reset: { type: 'navigate', target: '/settings' },

  // Lab
  run: { type: 'navigate', target: '/lab' },
  results: { type: 'navigate', target: '/lab' },

  // Keywords
  add_kw: { type: 'navigate', target: '/keywords' },
  recommend: { type: 'navigate', target: '/keywords' },

  // Templates
  use: { type: 'navigate', target: '/strategy-elements' },
  create_tpl: { type: 'navigate', target: '/strategy-elements' },

  // Strategy Elements
  create_element: { type: 'navigate', target: '/strategy-elements' },
  go_lab: { type: 'navigate', target: '/lab' },
  apply_to_task: { type: 'navigate', target: '/generate/create' },
  manage_strategy_elements: { type: 'navigate', target: '/strategy-elements' },

  // Rules
  add_rule: { type: 'navigate', target: '/rules' },
  test_rule: { type: 'navigate', target: '/rules' },
}

/** Quick Action 文本 → navigate target */
export const QUICK_ACTION_NAVIGATE_MAP: Record<string, NavigateCapability> = {
  '为@省钱狗爸生成驱虫内容': { type: 'navigate', target: '/generate/create' },
  '分析最近7天爆款趋势': { type: 'navigate', target: '/analytics' },
  '优化这条文案的标题': { type: 'navigate', target: '/lab' },
  '检查合规风险': { type: 'navigate', target: '/review' },
  // 默认兜底快捷动作（后端 action-cards 失败时）
  '新建任务': { type: 'navigate', target: '/generate/create' },
  '新建内容': { type: 'navigate', target: '/generate/create' },
  '查看全部': { type: 'navigate', target: '/generate' },
  '查看趋势': { type: 'navigate', target: '/analytics' },
}

export function isNavigateAction(actionId: string): boolean {
  return actionId in FRONTEND_NAVIGATE_MAP
}

export function resolveNavigateAction(actionId: string): NavigateCapability | null {
  return FRONTEND_NAVIGATE_MAP[actionId] || QUICK_ACTION_NAVIGATE_MAP[actionId] || null
}
