import { Link } from 'react-router-dom'
import {
  ListTodo,
  TrendingUp,
  Hammer,
  ShieldCheck,
  Send,
  PieChart,
  Users,
  Sparkles,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface ShortcutItem {
  path: string
  label: string
  icon: LucideIcon
  description: string
}

/**
 * 快捷导航 —— 对齐 PRD v5.0 核心业务流程（8 Phase）
 *
 * 按内容生产 → 风控 → 发布 → 数据回流的完整链路排列，
 * 覆盖用户最高频的 8 个功能入口。
 */
const shortcuts: ShortcutItem[] = [
  { path: '/task-hub', label: '任务中心', icon: ListTodo, description: '创建并追踪任务' },
  { path: '/trend-scout', label: '趋势侦察', icon: TrendingUp, description: '热点情报洞察' },
  { path: '/content-forge', label: '内容锻造', icon: Hammer, description: 'AI 内容生成' },
  { path: '/compliance', label: '合规审核', icon: ShieldCheck, description: '四层风控审核' },
  { path: '/publisher', label: '发布管理', icon: Send, description: '多平台分发' },
  { path: '/data-analyst', label: '数据报表', icon: PieChart, description: '24h 战报分析' },
  { path: '/account-pool', label: '账号池', icon: Users, description: '素人矩阵管理' },
  { path: '/agent-orchestra', label: 'Agent 编排', icon: Sparkles, description: '智能体工作流' },
]

export function ShortcutNav() {
  return (
    <section>
      <h2 className="text-base font-semibold text-foreground mb-3">快捷导航</h2>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {shortcuts.map((item) => {
          const Icon = item.icon
          return (
            <Link
              key={item.path}
              to={item.path}
              className="group p-4 bg-card rounded-xl border border-border hover:border-primary/30 hover:shadow-sm transition-all"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Icon className="w-4 h-4 text-primary" />
                </div>
              </div>
              <div className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                {item.label}
              </div>
              {item.description && (
                <div className="text-xs text-muted-foreground mt-0.5">{item.description}</div>
              )}
            </Link>
          )
        })}
      </div>
    </section>
  )
}
