import { useEffect, useState } from 'react'
import { useTaskHubStore } from '../stores/taskHubStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Badge, type BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import {
  ListTodo,
  Layers,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Clock,
  Zap,
  CalendarClock,
} from 'lucide-react'

const statusLabels: Record<string, string> = {
  draft: '草稿',
  configuring: '配置中',
  queued: '排队中',
  running: '运行中',
  paused: '已暂停',
  human_wait: '等待审核',
  approved_waiting_publish: '审核通过待发布',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
  dlq: '死信队列',
}

const statusVariants: Record<string, string> = {
  draft: 'default',
  configuring: 'default',
  queued: 'info',
  running: 'primary',
  paused: 'warning',
  human_wait: 'warning',
  approved_waiting_publish: 'amber',
  completed: 'success',
  failed: 'danger',
  cancelled: 'default',
  dlq: 'danger',
}

const seriesStatusLabels: Record<string, string> = {
  planning: '规划中',
  active: '执行中',
  completed: '已完成',
}

const seriesStatusVariants: Record<string, BadgeVariant> = {
  planning: 'info',
  active: 'primary',
  completed: 'success',
}

type TabKey = 'tasks' | 'series' | 'dlq'

export function TaskHubPage() {
  const {
    tasks,
    contentSeries,
    dlqItems,
    isLoading,
    error,
    fetchTasks,
    fetchContentSeries,
    fetchDLQ,
  } = useTaskHubStore()

  const [activeTab, setActiveTab] = useState<TabKey>('tasks')
  const [filter, setFilter] = useState('')
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)

  // Expand series task list
  const [expandedSeries, setExpandedSeries] = useState<Record<string, boolean>>({})

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  useEffect(() => {
    if (activeTab === 'series') fetchContentSeries()
    if (activeTab === 'dlq') fetchDLQ()
  }, [activeTab, fetchContentSeries, fetchDLQ])

  const filteredTasks = tasks.filter(
    (t) =>
      t.name.toLowerCase().includes(filter.toLowerCase()) ||
      t.status.toLowerCase().includes(filter.toLowerCase()) ||
      (t.account_name && t.account_name.toLowerCase().includes(filter.toLowerCase()))
  )

  const filteredSeries = contentSeries.filter(
    (s) =>
      s.name.toLowerCase().includes(filter.toLowerCase()) ||
      (s.story_name && s.story_name.toLowerCase().includes(filter.toLowerCase()))
  )

  const filteredDLQ = dlqItems.filter(
    (d) =>
      d.task_name.toLowerCase().includes(filter.toLowerCase()) ||
      d.error_reason.toLowerCase().includes(filter.toLowerCase())
  )

  const toggleSeries = (id: string) => {
    setExpandedSeries((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const tabs: { key: TabKey; label: string; icon: React.ElementType }[] = [
    { key: 'tasks', label: '任务列表', icon: ListTodo },
    { key: 'series', label: '系列规划', icon: Layers },
    { key: 'dlq', label: 'DLQ', icon: AlertTriangle },
  ]

  return (
    <div className="space-y-6">
      {/* Mode C: 工作区禁止新建按钮，操作走 Copilot Action Card */}
      <PageHeader
        title="任务中心"
        subtitle="管理内容生产任务的全生命周期"
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-1">
        {tabs.map((t) => {
          const Icon = t.icon
          const active = activeTab === t.key
          return (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                active
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="w-4 h-4" />
              {t.label}
            </button>
          )
        })}
        <div className="ml-auto">
          <input
            type="text"
            placeholder="搜索..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="h-8 px-3 rounded-lg border border-border bg-background text-xs w-56"
          />
        </div>
      </div>

      {/* Task List Tab */}
      {activeTab === 'tasks' && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ListTodo className="w-4 h-4 text-primary" />
              <h2 className="text-base font-semibold">任务列表</h2>
              <Badge variant="default">{filteredTasks.length}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
            {!isLoading && filteredTasks.length === 0 && (
              <EmptyState icon={ListTodo} title="暂无任务" description="请在右侧 Copilot 面板中操作" />
            )}
            <div className="space-y-2">
              {filteredTasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => setSelectedTaskId(task.id)}
                  className={`flex items-start justify-between p-3 rounded-lg border transition-colors cursor-pointer ${
                    selectedTaskId === task.id
                      ? 'border-primary ring-1 ring-primary bg-primary/5'
                      : 'border-border hover:bg-secondary/30'
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-foreground">{task.name}</span>
                      <Badge variant={(statusVariants[task.status] as BadgeVariant) || 'default'}>
                        {statusLabels[task.status] || task.status}
                      </Badge>
                      {task.priority > 0 && (
                        <Badge variant="warning">P{task.priority}</Badge>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5 text-xs text-muted-foreground">
                      {task.account_name && <span>账号: {task.account_name}</span>}
                      {task.persona_name && <span>人设: {task.persona_name}</span>}
                      {task.story_name && <span>故事: {task.story_name}</span>}
                      {task.current_node_theme && <span>节点: {task.current_node_theme}</span>}
                      {task.workflow_template_name && (
                        <span>模板: {task.workflow_template_name}</span>
                      )}
                      {task.platform && (
                        <span className="text-primary">
                          平台: {task.platform === 'xhs' ? '小红书' : task.platform === 'douyin' ? '抖音' : task.platform === 'wechat_channels' ? '视频号' : task.platform}
                        </span>
                      )}
                      {task.current_step_label && (
                        <span className="flex items-center gap-1 text-primary">
                          <Zap className="w-3 h-3" />
                          {task.current_step_label}
                        </span>
                      )}
                      {task.estimated_completion_at && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          预计: {new Date(task.estimated_completion_at).toLocaleString()}
                        </span>
                      )}
                      {task.scheduled_at && (
                        <span className="flex items-center gap-1">
                          <CalendarClock className="w-3 h-3" />
                          定时: {new Date(task.scheduled_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                  {/* Mode C: 工作区禁止启动/暂停/继续/重试/完成/取消/删除等操作按钮，操作走 Copilot Action Card */}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Content Series Tab */}
      {activeTab === 'series' && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-primary" />
              <h2 className="text-base font-semibold">系列规划</h2>
              <Badge variant="default">{filteredSeries.length}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
            {!isLoading && filteredSeries.length === 0 && (
              <EmptyState icon={Layers} title="暂无系列规划" description="新建任务时可绑定或创建系列" />
            )}
            <div className="space-y-2">
              {filteredSeries.map((series) => {
                const progress = series.total_tasks > 0 ? Math.round((series.completed_tasks / series.total_tasks) * 100) : 0
                const expanded = !!expandedSeries[series.id]
                const seriesTasks = tasks.filter((t) => t.content_series_id === series.id)
                return (
                  <div
                    key={series.id}
                    className="p-3 rounded-lg border border-border hover:bg-secondary/30 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium text-foreground">{series.name}</span>
                          <Badge variant={(seriesStatusVariants[series.status] as BadgeVariant) || 'default'}>
                            {seriesStatusLabels[series.status] || series.status}
                          </Badge>
                          {series.story_name && (
                            <span className="text-xs text-muted-foreground">{series.story_name}</span>
                          )}
                        </div>
                        <div className="mt-2">
                          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                            <span>
                              进度 {series.completed_tasks}/{series.total_tasks}
                            </span>
                            <span>{progress}%</span>
                          </div>
                          <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary transition-all"
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => toggleSeries(series.id)}
                        className="p-1.5 hover:bg-secondary rounded ml-3"
                      >
                        {expanded ? (
                          <ChevronUp className="w-4 h-4 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-muted-foreground" />
                        )}
                      </button>
                    </div>
                    {expanded && (
                      <div className="mt-3 space-y-1 border-t border-border pt-2">
                        {seriesTasks.length === 0 && (
                          <p className="text-xs text-muted-foreground">系列内暂无任务</p>
                        )}
                        {seriesTasks.map((t) => (
                          <div
                            key={t.id}
                            className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-secondary/50"
                          >
                            <span className="text-xs text-foreground">{t.name}</span>
                            <Badge variant={(statusVariants[t.status] as BadgeVariant) || 'default'}>
                              {statusLabels[t.status] || t.status}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* DLQ Tab */}
      {activeTab === 'dlq' && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-danger" />
              <h2 className="text-base font-semibold">死信队列</h2>
              <Badge variant="danger">{filteredDLQ.length}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
            {!isLoading && filteredDLQ.length === 0 && (
              <EmptyState icon={AlertTriangle} title="DLQ为空" description="当前没有需要处理失败任务" />
            )}
            <div className="space-y-2">
              {filteredDLQ.map((item) => (
                <div
                  key={item.id}
                  className="flex items-start justify-between p-3 rounded-lg border border-border hover:bg-secondary/30 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-foreground">{item.task_name}</span>
                      <Badge variant="danger">失败</Badge>
                      <Badge variant="warning">重试 {item.retry_count}</Badge>
                    </div>
                    <div className="mt-1 text-xs text-destructive">{item.error_reason}</div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      最后失败: {new Date(item.last_failed_at).toLocaleString()}
                    </div>
                  </div>
                  {/* Mode C: 工作区禁止重试/丢弃操作按钮，操作走 Copilot Action Card */}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
