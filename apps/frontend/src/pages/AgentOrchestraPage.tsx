import { useEffect, useState } from 'react'
import { useAgentCockpitStore } from '../stores/agentCockpitStore'
import { PageHeader } from '../components/common/PageHeader'
import { StatCard } from '../components/common/StatCard'
import { Card, CardHeader, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import {
  LayoutDashboard,
  Bot,
  BarChart3,
  Bell,
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  WifiOff,
  ChevronDown,
  ChevronUp,
  Clock,
  DollarSign,
  Zap,
  Server,
  TrendingUp,
} from 'lucide-react'

interface AgentDetail {
  version?: string
  environment?: string
  dependencies?: {
    overall: string
    healthy: number
    degraded: number
    down: number
  }
}

const STATUS_COLORS: Record<string, string> = {
  REGISTERED: 'bg-muted text-foreground',
  ACTIVE: 'bg-success/15 text-success',
  DEGRADED: 'bg-yellow-100 text-yellow-700',
  PAUSED: 'bg-info/15 text-info',
  OFFLINE: 'bg-destructive/15 text-destructive',
}

const ALERT_SEVERITY_COLORS: Record<string, string> = {
  P0: 'bg-destructive/15 text-destructive border-destructive/30',
  P1: 'bg-warning/15 text-warning border-warning/30',
  P2: 'bg-yellow-100 text-yellow-700 border-yellow-200',
}

const ROLE_LABELS: Record<string, string> = {
  TREND_SCOUT: '趋势侦察',
  CONTENT_FORGE: '内容锻造',
  COMPLIANCE_GUARD: '合规守卫',
  PUBLISHER: '发布调度',
  DATA_ANALYST: '数据分析师',
  POOL_PREDICTOR: '流量预测',
  MARKETING_METHODOLOGY: '营销方法论',
  PLATFORM_RULE: '平台规则',
  ORCHESTRATOR: '编排器',
  planner: '策划',
  content_planner: '内容策划',
  generator: '内容生成',
  checker: '合规检查',
  publisher: '发布调度',
  noop: '空操作',
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins} 分钟前`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} 小时前`
  return `${Math.floor(hrs / 24)} 天前`
}

export function AgentOrchestraPage() {
  const store = useAgentCockpitStore()
  const {
    dashboard,
    agents,
    agentDetail,
    agentConfigs,
    alerts,
    overallMetrics,
    costByAgent,
    activity,
    alertSummary,
    isLoading,
    error,
    activeTab,
    fetchDashboard,
    fetchAgents,
    fetchAgentDetail,
    fetchAgentConfigs,
    fetchAlerts,
    ackAlert,
    fetchOverallMetrics,
    fetchCostByAgent,
    fetchActivity,
    fetchAlertSummary,
    setActiveTab,
    clearError,
  } = store

  const [expandedAgentId, setExpandedAgentId] = useState<string | null>(null)

  useEffect(() => {
    fetchDashboard()
    fetchAlertSummary()
  }, [fetchDashboard, fetchAlertSummary])

  useEffect(() => {
    if (activeTab === 'agents') fetchAgents()
    if (activeTab === 'metrics') {
      fetchOverallMetrics()
      fetchCostByAgent()
    }
    if (activeTab === 'alerts') fetchAlerts()
    if (activeTab === 'dashboard') {
      fetchActivity()
    }
  }, [activeTab, fetchAgents, fetchAlerts, fetchOverallMetrics, fetchCostByAgent, fetchActivity])

  const tabs = [
    { key: 'dashboard' as const, label: '驾驶舱', icon: LayoutDashboard },
    { key: 'agents' as const, label: 'Agents', icon: Bot },
    { key: 'metrics' as const, label: '统计', icon: BarChart3 },
    { key: 'alerts' as const, label: '告警', icon: Bell },
  ]

  const toggleAgent = (id: string) => {
    if (expandedAgentId === id) {
      setExpandedAgentId(null)
    } else {
      setExpandedAgentId(id)
      fetchAgentDetail(id)
      fetchAgentConfigs(id)
    }
  }

  const healthyCount = dashboard?.agent_summary.healthy ?? 0
  const unhealthyCount = dashboard?.agent_summary.unhealthy ?? 0
  const offlineCount = dashboard?.agents.filter((a) => a.status === 'OFFLINE').length ?? 0
  const degradedCount = dashboard?.agents.filter((a) => a.status === 'DEGRADED').length ?? 0

  return (
    <div className="space-y-6">
      <PageHeader title="Agent Cockpit" subtitle="Agent 驾驶舱 — 统一治理控制台" />

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/15 p-4 text-destructive">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="ghost" size="sm" onClick={clearError}>
              清除
            </Button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-border">
        {tabs.map((t) => {
          const Icon = t.icon
          const isActive = activeTab === t.key
          return (
            <button
              key={t.key}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveTab(t.key)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                isActive
                  ? 'border-blue-600 text-info'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-4 w-4" />
              {t.label}
            </button>
          )
        })}
      </div>

      {/* ─── Dashboard Tab ─── */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {/* Fleet Status Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="健康" value={healthyCount} icon={CheckCircle} variant="success" />
            <StatCard label="降级" value={degradedCount} icon={AlertTriangle} variant="warning" />
            <StatCard label="故障" value={unhealthyCount} icon={XCircle} variant="danger" />
            <StatCard label="离线" value={offlineCount} icon={WifiOff} variant="default" />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Agent Table */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <h3 className="text-base font-semibold text-foreground">Agent  fleet 状态</h3>
              </CardHeader>
              <CardContent>
                {dashboard?.agents.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="border-b border-border">
                        <tr className="text-left text-muted-foreground">
                          <th className="pb-2 pr-4 font-medium">名称</th>
                          <th className="pb-2 pr-4 font-medium">角色</th>
                          <th className="pb-2 pr-4 font-medium">状态</th>
                          <th className="pb-2 pr-4 font-medium">队列深度</th>
                          <th className="pb-2 pr-4 font-medium">完成率</th>
                          <th className="pb-2 font-medium">1h 任务</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {dashboard.agents.map((a) => (
                          <tr key={a.agent_id} className="hover:bg-muted">
                            <td className="py-2 pr-4 font-medium text-foreground">{a.name}</td>
                            <td className="py-2 pr-4 text-muted-foreground">{ROLE_LABELS[a.role] || a.role}</td>
                            <td className="py-2 pr-4">
                              <Badge variant={a.healthy ? 'success' : 'danger'}>
                                {a.healthy ? '健康' : '异常'}
                              </Badge>
                            </td>
                            <td className="py-2 pr-4 text-muted-foreground">{a.queue_depth}</td>
                            <td className="py-2 pr-4 text-muted-foreground">
                              {(a.completion_rate * 100).toFixed(0)}%
                            </td>
                            <td className="py-2 text-muted-foreground">{a.total_tasks_1h}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyState title="暂无 Agent 数据" description="暂无数据" icon={Bot} />
                )}
              </CardContent>
            </Card>

            {/* Right Column: Alerts + Activity */}
            <div className="space-y-6">
              {/* Alert Summary */}
              <Card>
                <CardHeader>
                  <h3 className="text-base font-semibold text-foreground">告警摘要</h3>
                </CardHeader>
                <CardContent>
                  {alertSummary ? (
                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        <Badge variant="danger">P0: {alertSummary.by_severity.P0 ?? 0}</Badge>
                        <Badge variant="warning">P1: {alertSummary.by_severity.P1 ?? 0}</Badge>
                        <Badge variant="default">P2: {alertSummary.by_severity.P2 ?? 0}</Badge>
                      </div>
                      <div className="space-y-2">
                        {alertSummary.latest.map((a) => (
                          <div
                            key={a.id}
                            className={`rounded-md border px-3 py-2 text-xs ${
                              ALERT_SEVERITY_COLORS[a.severity] || 'bg-muted text-foreground'
                            }`}
                          >
                            <span className="font-semibold">[{a.severity}]</span> {a.message}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <EmptyState title="暂无告警" description="暂无告警数据" icon={Bell} />
                  )}
                </CardContent>
              </Card>

              {/* Activity Stream */}
              <Card>
                <CardHeader>
                  <h3 className="text-base font-semibold text-foreground">最近活动</h3>
                </CardHeader>
                <CardContent>
                  {activity.length ? (
                    <div className="max-h-80 space-y-3 overflow-y-auto pr-1">
                      {activity.map((item, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-sm">
                          {item.type === 'task' && <Zap className="mt-0.5 h-4 w-4 text-blue-500" />}
                          {item.type === 'alert' && <Bell className="mt-0.5 h-4 w-4 text-red-500" />}
                          {item.type === 'heartbeat' && <Activity className="mt-0.5 h-4 w-4 text-green-500" />}
                          <div className="flex-1">
                            <p className="text-foreground">
                              {item.type === 'task' && (
                                <>
                                  Agent <span className="font-medium">{item.agent_id}</span> 完成任务
                                  {item.outcome === 'success' ? ' ✅' : ' ❌'}
                                </>
                              )}
                              {item.type === 'alert' && (
                                <>
                                  <span className="font-medium">[{item.severity}]</span> {item.message}
                                </>
                              )}
                              {item.type === 'heartbeat' && (
                                <>
                                  Agent <span className="font-medium">{item.agent_id}</span> 心跳 —{' '}
                                  {item.status}
                                </>
                              )}
                            </p>
                            <p className="text-xs text-gray-400">{formatRelativeTime(item.timestamp)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="暂无活动" description="暂无活动数据" icon={Activity} />
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      )}

      {/* ─── Agents Tab ─── */}
      {activeTab === 'agents' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <h3 className="text-base font-semibold text-foreground">Agent 列表</h3>
            </CardHeader>
            <CardContent>
              {agents.length ? (
                <div className="space-y-3">
                  {agents.map((agent) => (
                    <div key={agent.id} className="rounded-lg border border-border">
                      <button
                        onClick={() => toggleAgent(agent.id)}
                        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-muted"
                      >
                        <div className="flex items-center gap-3">
                          <Bot className="h-5 w-5 text-blue-500" />
                          <div>
                            <p className="font-medium text-foreground">{agent.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {ROLE_LABELS[agent.role] || agent.role} · {agent.owner}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span
                            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                              STATUS_COLORS[agent.status] || 'bg-muted text-foreground'
                            }`}
                          >
                            {agent.status}
                          </span>
                          {expandedAgentId === agent.id ? (
                            <ChevronUp className="h-4 w-4 text-gray-400" />
                          ) : (
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                          )}
                        </div>
                      </button>

                      {expandedAgentId === agent.id && agentDetail && (
                        <div className="border-t border-border px-4 py-3">
                          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <div>
                              <h4 className="mb-2 text-sm font-semibold text-foreground">基本信息</h4>
                              <dl className="space-y-1 text-sm">
                                <div className="flex justify-between">
                                  <dt className="text-muted-foreground">ID</dt>
                                  <dd className="font-mono text-foreground">{agent.id}</dd>
                                </div>
                                <div className="flex justify-between">
                                  <dt className="text-muted-foreground">描述</dt>
                                  <dd className="text-foreground">{agent.description || '—'}</dd>
                                </div>
                                <div className="flex justify-between">
                                  <dt className="text-muted-foreground">版本</dt>
                                  <dd className="text-foreground">
                                    {(agentDetail as AgentDetail).version || '—'}
                                  </dd>
                                </div>
                                <div className="flex justify-between">
                                  <dt className="text-muted-foreground">环境</dt>
                                  <dd className="text-foreground">
                                    {(agentDetail as AgentDetail).environment || '—'}
                                  </dd>
                                </div>
                              </dl>
                            </div>
                            <div>
                              <h4 className="mb-2 text-sm font-semibold text-foreground">依赖健康</h4>
                              {(agentDetail as AgentDetail).dependencies ? (
                                <dl className="space-y-1 text-sm">
                                  <div className="flex justify-between">
                                    <dt className="text-muted-foreground">总体</dt>
                                    <dd>
                                      <Badge
                                        variant={
                                          (agentDetail as AgentDetail).dependencies?.overall === 'healthy'
                                            ? 'success'
                                            : 'warning'
                                        }
                                      >
                                        {(agentDetail as AgentDetail).dependencies?.overall}
                                      </Badge>
                                    </dd>
                                  </div>
                                  <div className="flex justify-between">
                                    <dt className="text-muted-foreground">健康 / 降级 / 故障</dt>
                                    <dd className="text-foreground">
                                      {(agentDetail as AgentDetail).dependencies?.healthy} /{' '}
                                      {(agentDetail as AgentDetail).dependencies?.degraded} /{' '}
                                      {(agentDetail as AgentDetail).dependencies?.down}
                                    </dd>
                                  </div>
                                </dl>
                              ) : (
                                <p className="text-sm text-gray-400">暂无依赖数据</p>
                              )}
                            </div>
                          </div>

                          {/* Config Versions */}
                          <div className="mt-4">
                            <h4 className="mb-2 text-sm font-semibold text-foreground">配置版本</h4>
                            {agentConfigs.length ? (
                              <div className="overflow-x-auto">
                                <table className="w-full text-xs">
                                  <thead className="border-b border-border">
                                    <tr className="text-left text-muted-foreground">
                                      <th className="pb-1 pr-3 font-medium">版本</th>
                                      <th className="pb-1 pr-3 font-medium">环境</th>
                                      <th className="pb-1 pr-3 font-medium">SHA256</th>
                                      <th className="pb-1 font-medium">创建时间</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-gray-100">
                                    {agentConfigs.map((cfg) => (
                                      <tr key={cfg.id}>
                                        <td className="py-1 pr-3 font-mono">v{cfg.version}</td>
                                        <td className="py-1 pr-3">{cfg.env}</td>
                                        <td className="py-1 pr-3 font-mono text-muted-foreground">
                                          {cfg.sha256?.slice(0, 8)}...
                                        </td>
                                        <td className="py-1 text-muted-foreground">
                                          {formatRelativeTime(cfg.created_at)}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            ) : (
                              <p className="text-sm text-gray-400">暂无配置版本</p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="暂无 Agent" description="暂无 Agent 数据" icon={Bot} />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ─── Metrics Tab ─── */}
      {activeTab === 'metrics' && (
        <div className="space-y-6">
          {/* Overall Metrics Cards */}
          {overallMetrics && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                label="总任务数"
                value={overallMetrics.total_tasks}
                icon={Server}
                variant="default"
              />
              <StatCard
                label="完成率"
                value={`${(overallMetrics.overall_completion_rate * 100).toFixed(1)}%`}
                icon={TrendingUp}
                variant="success"
              />
              <StatCard
                label="Token 消耗"
                value={overallMetrics.total_tokens.toLocaleString()}
                icon={Zap}
                variant="primary"
              />
              <StatCard
                label="成本 (USD)"
                value={`$${overallMetrics.total_cost_usd.toFixed(4)}`}
                icon={DollarSign}
                variant="warning"
              />
            </div>
          )}

          {/* Cost by Agent Table */}
          <Card>
            <CardHeader>
              <h3 className="text-base font-semibold text-foreground">成本归因（按 Agent）</h3>
            </CardHeader>
            <CardContent>
              {costByAgent.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b border-border">
                      <tr className="text-left text-muted-foreground">
                        <th className="pb-2 pr-4 font-medium">Agent</th>
                        <th className="pb-2 pr-4 font-medium">角色</th>
                        <th className="pb-2 pr-4 font-medium">任务数</th>
                        <th className="pb-2 pr-4 font-medium">Token 数</th>
                        <th className="pb-2 font-medium">成本 (USD)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {costByAgent.map((c) => (
                        <tr key={c.agent_id} className="hover:bg-muted">
                          <td className="py-2 pr-4 font-medium text-foreground">{c.agent_id}</td>
                          <td className="py-2 pr-4 text-muted-foreground">
                            {ROLE_LABELS[c.agent_role] || c.agent_role}
                          </td>
                          <td className="py-2 pr-4 text-muted-foreground">{c.task_count}</td>
                          <td className="py-2 pr-4 text-muted-foreground">
                            {c.total_tokens.toLocaleString()}
                          </td>
                          <td className="py-2 font-medium text-foreground">
                            ${c.total_cost_usd.toFixed(4)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState title="暂无成本数据" description="暂无成本数据" icon={DollarSign} />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ─── Alerts Tab ─── */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <h3 className="text-base font-semibold text-foreground">告警列表</h3>
            </CardHeader>
            <CardContent>
              {alerts.length ? (
                <div className="space-y-3">
                  {alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className={`flex items-start justify-between rounded-lg border px-4 py-3 ${
                        ALERT_SEVERITY_COLORS[alert.severity] || 'bg-muted border-border'
                      }`}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold">[{alert.severity}]</span>
                          <span className="text-sm text-foreground">{alert.message}</span>
                        </div>
                        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                          <span>类型: {alert.alert_type}</span>
                          <span>Agent: {alert.agent_id}</span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatRelativeTime(alert.created_at)}
                          </span>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={async () => {
                          const ok = await ackAlert(alert.id, 'operator')
                          if (ok) fetchAlerts()
                        }}
                      >
                        确认
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="暂无告警" description="暂无告警数据" icon={Bell} />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12 text-gray-400">
          <Activity className="mr-2 h-5 w-5 animate-spin" />
          加载中...
        </div>
      )}
    </div>
  )
}
