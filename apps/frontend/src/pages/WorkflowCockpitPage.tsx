import { useEffect, useState } from 'react'
import {
  CheckCircle,
  Pause,
  Play,
  Clock,
  Bot,
  User,
  ArrowRight,
  Eye,
  LayoutDashboard,
  AlertCircle,
  Layers,
  ClipboardList,
} from 'lucide-react'
import { useWorkflowCockpitStore } from '../stores/workflowCockpitStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import type { BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'

const KANBAN_COLUMNS = [
  { key: 'DRAFT', label: '草稿', color: 'border-t-gray-300' },
  { key: 'CONFIGURING', label: '配置中', color: 'border-t-blue-300' },
  { key: 'QUEUED', label: '排队中', color: 'border-t-yellow-300' },
  { key: 'RUNNING', label: '运行中', color: 'border-t-green-300' },
  { key: 'HUMAN_WAIT', label: '人工审核', color: 'border-t-orange-300' },
  { key: 'COMPLETED', label: '已完成', color: 'border-t-green-500' },
  { key: 'FAILED', label: '失败', color: 'border-t-red-300' },
]

export function WorkflowCockpitPage() {
  const {
    tasks, templates, executions,
    isLoading, error, activeTab,
    fetchTasks, fetchTemplates, fetchExecutions,
    transitionTask, setActiveTab, clearError,
  } = useWorkflowCockpitStore()

  const [expandedExecutions, setExpandedExecutions] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchTasks()
    fetchTemplates()
    fetchExecutions()
  }, [fetchTasks, fetchTemplates, fetchExecutions])

  const tabs = [
    { key: 'kanban' as const, label: '任务 Kanban', icon: LayoutDashboard },
    { key: 'templates' as const, label: '工作流模板', icon: Layers },
    { key: 'executions' as const, label: '执行监控', icon: ClipboardList },
  ] as const

  const todayStr = new Date().toISOString().slice(0, 10)

  const stats = [
    { label: '总任务数', value: tasks.length, icon: ClipboardList },
    { label: '运行中', value: tasks.filter((t) => t.status === 'RUNNING').length, icon: Play },
    { label: '待人工审核', value: tasks.filter((t) => t.status === 'HUMAN_WAIT').length, icon: AlertCircle },
    {
      label: '今日完成',
      value: tasks.filter((t) => t.status === 'COMPLETED' && t.created_at?.slice(0, 10) === todayStr).length,
      icon: CheckCircle,
    },
  ]

  const toggleExecutionContext = (id: string) => {
    setExpandedExecutions((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const priorityVariant = (p: number): BadgeVariant => {
    if (p >= 80) return 'danger'
    if (p >= 50) return 'warning'
    return 'default'
  }

  const execStatusVariant = (status: string): BadgeVariant => {
    switch (status) {
      case 'RUNNING': return 'info'
      case 'COMPLETED': return 'success'
      case 'FAILED': return 'danger'
      case 'PAUSED': return 'warning'
      case 'PENDING': return 'default'
      case 'CANCELLED': return 'default'
      default: return 'default'
    }
  }

  const nodeTypeIcon = (type: string) => {
    switch (type) {
      case 'AGENT': return <Bot className="w-3.5 h-3.5 text-blue-500" />
      case 'HUMAN_APPROVAL': return <User className="w-3.5 h-3.5 text-orange-500" />
      case 'TIMER': return <Clock className="w-3.5 h-3.5 text-purple-500" />
      default: return <div className="w-3.5 h-3.5 rounded-full bg-gray-400" />
    }
  }

  const formatDuration = (started: string | null, ended: string | null) => {
    if (!started || !ended) return '-'
    const diff = new Date(ended).getTime() - new Date(started).getTime()
    if (diff < 1000) return `${diff}ms`
    if (diff < 60000) return `${Math.floor(diff / 1000)}s`
    return `${Math.floor(diff / 60000)}m ${Math.floor((diff % 60000) / 1000)}s`
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="工作流驾驶舱"
        subtitle="可视化任务看板、模板管理与执行监控"
      />

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 flex items-center justify-between">
          <p className="text-sm text-destructive">{error}</p>
          <Button variant="ghost" size="sm" onClick={clearError}>重试</Button>
        </div>
      )}

      {/* 统计看板 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <Card key={s.label} shadow="sm">
            <CardContent className="flex items-center gap-4">
              <div className="p-2.5 rounded-lg bg-primary/10">
                <s.icon className="w-5 h-5 text-primary" />
              </div>
              <div>
                <div className="text-2xl font-bold text-foreground">{s.value}</div>
                <div className="text-xs text-muted-foreground">{s.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex gap-2 border-b border-border">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === t.key
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">加载中...</p>
        </div>
      )}

      {/* Kanban Tab */}
      {activeTab === 'kanban' && !isLoading && (
        <section>
          <div className="flex gap-4 overflow-x-auto pb-4">
            {KANBAN_COLUMNS.map((col) => {
              const colTasks = tasks.filter((t) => t.status === col.key)
              return (
                <div key={col.key} className="flex-shrink-0 w-72">
                  <Card className={`border-t-4 ${col.color} h-full`}>
                    <CardHeader className="flex items-center justify-between py-3">
                      <span className="text-sm font-medium text-foreground">{col.label}</span>
                      <Badge variant="default">{colTasks.length}</Badge>
                    </CardHeader>
                    <CardContent className="space-y-2 min-h-[120px]">
                      {colTasks.map((task) => (
                        <Card key={task.id} hover shadow="sm" className="p-3">
                          <div className="text-sm font-medium text-foreground truncate">{task.name}</div>
                          <div className="text-xs text-muted-foreground mt-1">账号: {task.account_id}</div>
                          <div className="text-xs text-muted-foreground">节点: {task.current_node_index}</div>
                          <div className="flex items-center justify-between mt-2">
                            <Badge variant={priorityVariant(task.priority)}>P{task.priority}</Badge>
                            <div className="flex gap-1">
                              {col.key === 'HUMAN_WAIT' && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => transitionTask(task.id, 'RUNNING')}
                                  className="h-7 px-2"
                                >
                                  <CheckCircle className="w-3.5 h-3.5 text-success" />
                                  <span className="text-xs">通过</span>
                                </Button>
                              )}
                              {col.key === 'RUNNING' && (
                                <Button variant="ghost" size="sm" className="h-7 px-2">
                                  <Pause className="w-3.5 h-3.5 text-warning" />
                                  <span className="text-xs">暂停</span>
                                </Button>
                              )}
                            </div>
                          </div>
                        </Card>
                      ))}
                      {colTasks.length === 0 && (
                        <EmptyState
                          icon={ClipboardList}
                          title="无任务"
                          description="该状态下暂无任务"
                          className="py-6"
                        />
                      )}
                    </CardContent>
                  </Card>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && !isLoading && (
        <section className="space-y-4">
          {templates.map((tmpl) => (
            <Card key={tmpl.id} shadow="sm">
              <CardContent>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-base font-medium text-foreground">{tmpl.name}</div>
                  <Badge variant="primary">{tmpl.status}</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-4">{tmpl.description}</p>
                <div className="flex flex-wrap items-center gap-2">
                  {tmpl.nodes.map((n, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-muted border border-border text-xs">
                        {nodeTypeIcon(n.node_type)}
                        <span className="text-foreground font-medium">{n.node_name}</span>
                        {n.fail_strategy && n.fail_strategy !== 'FAIL_FAST' && (
                          <Badge variant="warning" className="ml-1">{n.fail_strategy}</Badge>
                        )}
                      </div>
                      {idx < tmpl.nodes.length - 1 && (
                        <ArrowRight className="w-4 h-4 text-muted-foreground" />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
          {templates.length === 0 && (
            <EmptyState
              icon={Layers}
              title="暂无工作流模板"
              description="创建模板以开始自动化工作流"
            />
          )}
        </section>
      )}

      {/* Executions Tab */}
      {activeTab === 'executions' && !isLoading && (
        <section>
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">执行ID</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">任务</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">模板</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">状态</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">当前节点</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">执行时长</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">上下文</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {executions.map((ex) => (
                    <tr key={ex.id} className="hover:bg-muted/50">
                      <td className="px-5 py-3 font-mono text-xs text-muted-foreground">{ex.id.slice(0, 12)}</td>
                      <td className="px-5 py-3 text-foreground">{ex.task_id.slice(0, 12)}</td>
                      <td className="px-5 py-3 text-muted-foreground">{ex.template_id}</td>
                      <td className="px-5 py-3">
                        <Badge variant={execStatusVariant(ex.status)}>{ex.status}</Badge>
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">{ex.current_node_index}</td>
                      <td className="px-5 py-3 text-muted-foreground">{formatDuration(ex.started_at, ex.ended_at)}</td>
                      <td className="px-5 py-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2"
                          onClick={() => toggleExecutionContext(ex.id)}
                        >
                          <Eye className="w-3.5 h-3.5 mr-1" />
                          <span className="text-xs">{expandedExecutions.has(ex.id) ? '收起' : '查看'}</span>
                        </Button>
                        {expandedExecutions.has(ex.id) && (
                          <div className="mt-2 p-2 rounded-md bg-muted border border-border text-xs text-muted-foreground font-mono whitespace-pre-wrap max-w-md">
                            {JSON.stringify(ex.context, null, 2)}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                  {executions.length === 0 && (
                    <tr>
                      <td colSpan={7}>
                        <EmptyState
                          icon={ClipboardList}
                          title="暂无执行记录"
                        />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </section>
      )}
    </div>
  )
}
