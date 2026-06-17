import { useEffect, useState } from 'react'
import { useTaskHubStore } from '../stores/taskHubStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Badge, type BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import {
  ListTodo,
  Clock,
  Zap,
  CalendarClock,
  Play,
  Pause,
  Trash2,
  Settings,
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

type TabKey = 'tasks'

export function TaskHubPage() {
  const {
    tasks,
    isLoading,
    error,
    fetchTasks,
    updateTaskStatus,
    startWorkflow,
    configureTask,
    deleteTask,
  } = useTaskHubStore()

  const [activeTab, setActiveTab] = useState<TabKey>('tasks')
  const [filter, setFilter] = useState('')
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const filteredTasks = tasks.filter(
    (t) =>
      t.name.toLowerCase().includes(filter.toLowerCase()) ||
      t.status.toLowerCase().includes(filter.toLowerCase()) ||
      (t.account_name && t.account_name.toLowerCase().includes(filter.toLowerCase()))
  )

  const tabs: { key: TabKey; label: string; icon: React.ElementType }[] = [
    { key: 'tasks', label: '任务列表', icon: ListTodo },
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
                  <div className="flex items-center gap-1 ml-2">
                    {(task.status === 'draft' || task.status === 'configuring') && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          configureTask(task.id)
                        }}
                        className="p-1.5 hover:bg-secondary rounded text-muted-foreground hover:text-foreground"
                        title="配置并启动"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                    )}
                    {(task.status === 'draft' || task.status === 'configuring' || task.status === 'paused') && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          startWorkflow(task.id)
                        }}
                        className="p-1.5 hover:bg-secondary rounded text-muted-foreground hover:text-primary"
                        title="启动"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    )}
                    {task.status === 'running' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          updateTaskStatus(task.id, 'paused')
                        }}
                        className="p-1.5 hover:bg-secondary rounded text-muted-foreground hover:text-warning"
                        title="暂停"
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    )}
                    {(task.status === 'draft' || task.status === 'configuring' || task.status === 'paused' || task.status === 'failed' || task.status === 'cancelled') && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          deleteTask(task.id)
                        }}
                        className="p-1.5 hover:bg-secondary rounded text-muted-foreground hover:text-destructive"
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
