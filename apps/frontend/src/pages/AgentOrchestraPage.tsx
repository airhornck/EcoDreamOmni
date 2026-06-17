import { useEffect, useMemo, useState } from 'react'
import {
  Bot,
  Activity,
  Zap,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  RefreshCw,
} from 'lucide-react'
import { useAgentFleetStore } from '../stores/agentFleetStore'
import { usePageCopilot } from '../hooks/usePageCopilot'
import { PageHeader } from '../components/common/PageHeader'
import { StatCard } from '../components/common/StatCard'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import type { Agent } from '../types/api'

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'bg-success/15 text-success border-success/20',
  DEGRADED: 'bg-warning/15 text-warning border-warning/20',
  PAUSED: 'bg-info/15 text-info border-info/20',
  OFFLINE: 'bg-destructive/15 text-destructive border-destructive/20',
}

const STATUS_LABELS: Record<string, string> = {
  ACTIVE: '活跃',
  DEGRADED: '降级',
  PAUSED: '暂停',
  OFFLINE: '离线',
}

function formatSuccessRate(rate?: number): string {
  return `${((rate ?? 0) * 100).toFixed(1)}%`
}

function formatDate(iso?: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString('zh-CN')
}

function AgentConfigSummary({ config }: { config: Record<string, unknown> }) {
  const snapshot = config?.platform_format_snapshot as Record<string, unknown> | undefined
  const safety = config?.safety_injection as Record<string, unknown> | undefined
  const tags: string[] = []

  if (snapshot?.platform_id && snapshot?.format_name) {
    tags.push(`平台格式: ${snapshot.platform_id} · ${snapshot.format_name}`)
  }

  const titleConstraints = snapshot?.title_constraints as Record<string, unknown> | undefined
  const bodyConstraints = snapshot?.body_constraints as Record<string, unknown> | undefined
  if (titleConstraints?.max_length) {
    tags.push(`标题≤${titleConstraints.max_length}字`)
  }
  if (bodyConstraints?.recommended) {
    tags.push(`正文${bodyConstraints.recommended}`)
  }

  const preCheck = safety?.pre_check_agents as string[] | undefined
  const postCheck = safety?.post_check_agents as string[] | undefined
  if (preCheck?.length || postCheck?.length) {
    const checks = [...(preCheck || []), ...(postCheck || [])]
    tags.push(`合规预检: ${checks.join('/')}`)
  }

  if (tags.length === 0) return null
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {tags.map((tag) => (
        <span
          key={tag}
          className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-secondary text-secondary-foreground"
        >
          {tag}
        </span>
      ))}
    </div>
  )
}

export function AgentOrchestraPage() {
  const { agents, isLoading, error, selectedAgentId, fetchAgents, selectAgent, clearError } =
    useAgentFleetStore()
  const [platformFilter, setPlatformFilter] = useState<string>('全部')

  useEffect(() => {
    fetchAgents()
  }, [fetchAgents])

  usePageCopilot(
    [
      {
        id: 'agent-refresh',
        type: 'decision',
        title: '🔄 刷新 Agent 列表',
        description: '重新拉取 Agent 舰队最新状态',
        priority: 1,
        actions: [{ id: 'refresh', label: '刷新', variant: 'primary' }],
      },
    ],
    async (_cardId, actionId) => {
      if (actionId === 'refresh') {
        await fetchAgents()
      }
    },
  )

  const platforms = useMemo(() => {
    const set = new Set<string>()
    agents.forEach((a) => a.supported_platforms?.forEach((p) => set.add(p)))
    return ['全部', ...Array.from(set)]
  }, [agents])

  const filteredAgents = useMemo(() => {
    if (platformFilter === '全部') return agents
    return agents.filter((a) => a.supported_platforms?.includes(platformFilter))
  }, [agents, platformFilter])

  const stats = useMemo(() => {
    const total = agents.length
    const active = agents.filter((a) => a.status === 'ACTIVE').length
    const avgSuccess =
      total > 0 ? agents.reduce((s, a) => s + (a.success_rate ?? 0), 0) / total : 0
    const recentTasks = agents.reduce((s, a) => s + (a.recent_tasks_1h ?? 0), 0)
    return { total, active, avgSuccess, recentTasks }
  }, [agents])

  const toggleAgent = (id: string) => {
    selectAgent(selectedAgentId === id ? null : id)
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Agent 驾驶舱" subtitle="v4.0 Agent-First 舰队 — TaskHub 同款 Agent" />

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/15 p-4 text-destructive">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => fetchAgents()}>
                <RefreshCw className="w-4 h-4 mr-1" />
                重试
              </Button>
              <Button variant="ghost" size="sm" onClick={clearError}>
                清除
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Agent 总数" value={stats.total} icon={Bot} variant="default" />
        <StatCard label="活跃" value={stats.active} icon={Activity} variant="success" />
        <StatCard
          label="平均成功率"
          value={formatSuccessRate(stats.avgSuccess)}
          icon={TrendingUp}
          variant="primary"
        />
        <StatCard label="近 1h 任务" value={stats.recentTasks} icon={Zap} variant="warning" />
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">平台筛选:</span>
        {platforms.map((p) => (
          <button
            key={p}
            onClick={() => setPlatformFilter(p)}
            className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
              platformFilter === p
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Agent Table */}
      <Card className="min-w-0 overflow-hidden">
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-foreground">Agent 列表</h3>
            <Button variant="outline" size="sm" onClick={() => fetchAgents()} disabled={isLoading}>
              <RefreshCw className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {filteredAgents.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-border">
                  <tr className="text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">名称</th>
                    <th className="pb-2 pr-4 font-medium">角色</th>
                    <th className="pb-2 pr-4 font-medium">平台</th>
                    <th className="pb-2 pr-4 font-medium">格式</th>
                    <th className="pb-2 pr-4 font-medium">技能</th>
                    <th className="pb-2 pr-4 font-medium">成功率</th>
                    <th className="pb-2 pr-4 font-medium">近1h任务</th>
                    <th className="pb-2 pr-4 font-medium">状态</th>
                    <th className="pb-2 font-medium"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredAgents.map((agent) => (
                    <AgentRow
                      key={agent.id}
                      agent={agent}
                      expanded={selectedAgentId === agent.id}
                      onToggle={() => toggleAgent(agent.id)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              title="暂无 Agent"
              description={isLoading ? '加载中...' : '当前没有符合条件的 Agent'}
              icon={Bot}
            />
          )}
        </CardContent>
      </Card>

      {isLoading && !agents.length && (
        <div data-testid="agent-fleet-loading" className="flex items-center justify-center py-12 text-muted-foreground">
          <Activity className="mr-2 h-5 w-5 animate-spin" />
          加载中...
        </div>
      )}
    </div>
  )
}

function AgentRow({
  agent,
  expanded,
  onToggle,
}: {
  agent: Agent
  expanded: boolean
  onToggle: () => void
}) {
  return (
    <>
      <tr className="hover:bg-muted/50">
        <td className="py-3 pr-4">
          <div className="flex items-center gap-3">
            <Bot className="w-5 h-5 text-primary flex-shrink-0" />
            <div>
              <p className="font-medium text-foreground">{agent.name}</p>
              <p className="text-xs text-muted-foreground font-mono">{agent.id}</p>
            </div>
          </div>
        </td>
        <td className="py-3 pr-4 text-muted-foreground">{agent.role}</td>
        <td className="py-3 pr-4">
          <TagList items={agent.supported_platforms} />
        </td>
        <td className="py-3 pr-4">
          <TagList items={agent.supported_formats} />
        </td>
        <td className="py-3 pr-4">
          <TagList items={agent.skills} />
        </td>
        <td className="py-3 pr-4 text-muted-foreground">
          {formatSuccessRate(agent.success_rate)}
        </td>
        <td className="py-3 pr-4 text-muted-foreground">{agent.recent_tasks_1h ?? 0}</td>
        <td className="py-3 pr-4">
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border ${
              STATUS_COLORS[agent.status] || 'bg-muted text-foreground border-border'
            }`}
          >
            {STATUS_LABELS[agent.status] || agent.status}
          </span>
        </td>
        <td className="py-3 text-right">
          <button
            onClick={onToggle}
            className="p-1 rounded-md hover:bg-muted text-muted-foreground"
            aria-label={expanded ? '收起详情' : '展开详情'}
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={9} className="bg-muted/30 px-4 py-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <h4 className="mb-2 text-sm font-semibold text-foreground">描述</h4>
                <p className="text-sm text-muted-foreground">{agent.description || '—'}</p>
              </div>
              <div>
                <h4 className="mb-2 text-sm font-semibold text-foreground">基本信息</h4>
                <dl className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">创建时间</dt>
                    <dd className="text-foreground">{formatDate(agent.created_at)}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">更新时间</dt>
                    <dd className="text-foreground">{formatDate(agent.updated_at)}</dd>
                  </div>
                </dl>
              </div>
            </div>
            <AgentConfigSummary config={agent.config || {}} />
          </td>
        </tr>
      )}
    </>
  )
}

function TagList({ items }: { items?: string[] }) {
  if (!items?.length) return <span className="text-muted-foreground">—</span>
  return (
    <div className="flex flex-wrap gap-1">
      {items.slice(0, 3).map((item) => (
        <Badge key={item} variant="default" className="text-[10px] font-normal">
          {item}
        </Badge>
      ))}
      {items.length > 3 && (
        <Badge variant="default" className="text-[10px] font-normal">
          +{items.length - 3}
        </Badge>
      )}
    </div>
  )
}
