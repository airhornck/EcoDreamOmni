import { useEffect, useMemo, useState } from 'react'
import { usePublisherStore, type PublishTask } from '../stores/publisherStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge, type BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import {
  Send,
  Play,
  Trash2,
  ExternalLink,
  RotateCcw,
  X,
  Calendar as CalendarIcon,
  List,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Tag,
  Image as ImageIcon,
  Info,
} from 'lucide-react'

const statusLabels: Record<string, string> = {
  pending: '待发布',
  scheduled: '已排期',
  publishing: '发布中',
  published: '已发布',
  failed: '失败',
}

const statusVariants: Record<string, BadgeVariant> = {
  pending: 'warning',
  scheduled: 'info',
  publishing: 'primary',
  published: 'success',
  failed: 'danger',
}

const platformLabels: Record<string, string> = {
  xhs: '小红书',
  douyin: '抖音',
  wechat_channels: '视频号',
}

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

function formatDateKey(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

function getCalendarDays(date: Date) {
  const year = date.getFullYear()
  const month = date.getMonth()
  const firstDayOfMonth = new Date(year, month, 1)
  const startDay = firstDayOfMonth.getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  const days: { date: Date; isCurrentMonth: boolean }[] = []

  const prevMonthLastDay = new Date(year, month, 0).getDate()
  for (let i = startDay - 1; i >= 0; i--) {
    days.push({ date: new Date(year, month - 1, prevMonthLastDay - i), isCurrentMonth: false })
  }

  for (let i = 1; i <= daysInMonth; i++) {
    days.push({ date: new Date(year, month, i), isCurrentMonth: true })
  }

  const remaining = (7 - (days.length % 7)) % 7
  for (let i = 1; i <= remaining; i++) {
    days.push({ date: new Date(year, month + 1, i), isCurrentMonth: false })
  }

  return days
}

function getIntensityClass(count: number): string {
  if (count === 0) return 'bg-transparent'
  if (count === 1) return 'bg-primary/10'
  if (count <= 3) return 'bg-primary/20'
  if (count <= 5) return 'bg-primary/30'
  return 'bg-primary/40'
}

export function PublisherPage() {
  const {
    tasks,
    drafts,
    accounts,
    stats,
    isLoading,
    isFormLoading,
    error,
    fetchTasks,
    fetchDrafts,
    fetchAccounts,
    createTask,
    executeTask,
    retryTask,
    deleteTask,
  } = usePublisherStore()

  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list')
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'published' | 'failed'>('all')

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [draftId, setDraftId] = useState('')
  const [accountId, setAccountId] = useState('')
  const [scheduleMode, setScheduleMode] = useState<'immediate' | 'scheduled'>('immediate')
  const [scheduledAt, setScheduledAt] = useState('')

  const [previewTask, setPreviewTask] = useState<PublishTask | null>(null)

  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [selectedDateKey, setSelectedDateKey] = useState<string | null>(null)

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  useEffect(() => {
    if (drawerOpen) {
      fetchDrafts()
      fetchAccounts()
    }
  }, [drawerOpen, fetchDrafts, fetchAccounts])

  const handleCreate = async () => {
    if (!draftId || !accountId) return
    const account = accounts.find((a) => a.id === accountId)
    const success = await createTask({
      draft_id: draftId,
      account_id: accountId,
      platform: account?.platform || 'xhs',
      scheduled_at: scheduleMode === 'scheduled' && scheduledAt ? scheduledAt : undefined,
    })
    if (success) {
      setDrawerOpen(false)
    }
  }

  const selectedDraft = useMemo(() => drafts.find((d) => d.id === draftId), [drafts, draftId])
  const selectedAccount = useMemo(() => accounts.find((a) => a.id === accountId), [accounts, accountId])

  const filteredTasks = useMemo(() => {
    if (filterStatus === 'all') return tasks
    if (filterStatus === 'pending') return tasks.filter((t) => ['pending', 'scheduled', 'publishing'].includes(t.status))
    return tasks.filter((t) => t.status === filterStatus)
  }, [tasks, filterStatus])

  const calendarDays = useMemo(() => getCalendarDays(currentMonth), [currentMonth])

  const tasksByDate = useMemo(() => {
    const map = new Map<string, PublishTask[]>()
    tasks.forEach((task) => {
      const dateStr = task.scheduled_at || task.published_at || task.created_at
      if (!dateStr) return
      const key = formatDateKey(new Date(dateStr))
      if (!map.has(key)) map.set(key, [])
      map.get(key)!.push(task)
    })
    return map
  }, [tasks])

  const selectedDateTasks = useMemo(() => {
    if (!selectedDateKey) return []
    return tasksByDate.get(selectedDateKey) || []
  }, [selectedDateKey, tasksByDate])

  const monthLabel = `${currentMonth.getFullYear()}年${currentMonth.getMonth() + 1}月`

  const today = new Date()

  const statCards = [
    {
      label: '今日发布数',
      value: stats.todayPublished,
      icon: CheckCircle2,
      color: 'text-success',
      bg: 'bg-success/10',
    },
    {
      label: '待发布数',
      value: stats.pendingCount,
      icon: Clock,
      color: 'text-warning',
      bg: 'bg-warning/10',
    },
    {
      label: '近7日成功率',
      value: `${stats.successRate7d}%`,
      icon: TrendingUp,
      color: 'text-primary',
      bg: 'bg-primary/10',
    },
    {
      label: '失败待重试',
      value: stats.failedRetryCount,
      icon: AlertCircle,
      color: 'text-danger',
      bg: 'bg-destructive/15',
    },
  ]

  const handleCardClick = (task: PublishTask) => {
    setPreviewTask(task)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="发布管理"
        subtitle="管理内容的多平台分发与排期"
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {/* 发布入口提示 */}
      <div className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20 text-sm">
        <Info className="w-4 h-4 text-primary mt-0.5 shrink-0" />
        <div className="text-foreground">
          <span className="font-medium">发布入口已统一：</span>
          新建发布任务请前往
          <a href="/review-publish-center" className="text-primary hover:underline ml-1">审核发布中心</a>
          确认审核结论后发起发布。
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((s) => {
          const Icon = s.icon
          return (
            <Card key={s.label}>
              <CardContent className="flex items-center gap-4 py-4">
                <div className={`p-2.5 rounded-lg ${s.bg}`}>
                  <Icon className={`w-5 h-5 ${s.color}`} />
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">{s.value}</div>
                  <div className="text-xs text-muted-foreground">{s.label}</div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Tabs + Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-2 border-b border-border pb-1">
          <button
            onClick={() => setViewMode('list')}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              viewMode === 'list'
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <List className="w-4 h-4" />
            列表视图
          </button>
          <button
            onClick={() => setViewMode('calendar')}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              viewMode === 'calendar'
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <CalendarIcon className="w-4 h-4" />
            日历视图
          </button>
        </div>
        <div className="flex gap-1 bg-secondary rounded-lg p-0.5">
          {(['all', 'pending', 'published', 'failed'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilterStatus(tab)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                filterStatus === tab
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab === 'all' ? '全部' : tab === 'pending' ? '待发布' : tab === 'published' ? '已发布' : '失败'}
            </button>
          ))}
        </div>
      </div>

      {/* List View */}
      {viewMode === 'list' && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Send className="w-4 h-4 text-primary" />
              <h2 className="text-base font-semibold">发布任务</h2>
              <Badge variant="default">{filteredTasks.length}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
            {!isLoading && filteredTasks.length === 0 && (
              <EmptyState icon={Send} title="暂无发布任务" description="点击「新建发布任务」开始分发内容" />
            )}
            <div className="space-y-2">
              {filteredTasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => handleCardClick(task)}
                  className="flex items-start justify-between p-3 rounded-lg border border-border hover:bg-secondary/30 transition-colors cursor-pointer"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-foreground">
                        {task.draft_title || `任务 #${task.id.slice(0, 8)}`}
                      </span>
                      <Badge variant={statusVariants[task.status] || 'default'}>
                        {statusLabels[task.status] || task.status}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5 text-xs text-muted-foreground">
                      <span>
                        {platformLabels[task.platform] || task.platform} · {task.account_name || task.account_id}
                      </span>
                      {task.scheduled_at && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          排期: {new Date(task.scheduled_at).toLocaleString('zh-CN')}
                        </span>
                      )}
                      {task.published_at && (
                        <span className="flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          发布: {new Date(task.published_at).toLocaleString('zh-CN')}
                        </span>
                      )}
                      {task.published_url && (
                        <a
                          href={task.published_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline flex items-center gap-1"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink className="w-3 h-3" /> 查看已发布内容
                        </a>
                      )}
                      {task.status === 'published' && task.platform === 'xhs' && (
                        <span className="flex items-center gap-1 text-muted-foreground">
                          <TrendingUp className="w-3 h-3" />
                          24h后自动获取互动数据
                        </span>
                      )}
                      {task.error_reason && (
                        <span className="text-destructive flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" /> 错误: {task.error_reason}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 ml-3 mt-0.5" onClick={(e) => e.stopPropagation()}>
                    {['pending', 'scheduled'].includes(task.status) && (
                      <button
                        onClick={() => executeTask(task.id)}
                        className="p-1.5 hover:bg-primary/10 rounded"
                        title="立即发布"
                      >
                        <Play className="w-4 h-4 text-primary" />
                      </button>
                    )}
                    {task.status === 'failed' && (
                      <button
                        onClick={() => retryTask(task.id)}
                        className="p-1.5 hover:bg-primary/10 rounded"
                        title="重新发布"
                      >
                        <RotateCcw className="w-4 h-4 text-primary" />
                      </button>
                    )}
                    <button
                      onClick={() => deleteTask(task.id)}
                      className="p-1.5 hover:bg-destructive/10 rounded"
                      title="删除"
                    >
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Calendar View */}
      {viewMode === 'calendar' && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CalendarIcon className="w-4 h-4 text-primary" />
              <h2 className="text-base font-semibold">发布日历</h2>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))}
                className="p-1 hover:bg-secondary rounded"
              >
                <ChevronLeft className="w-4 h-4 text-muted-foreground" />
              </button>
              <span className="text-sm font-medium w-28 text-center">{monthLabel}</span>
              <button
                onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))}
                className="p-1 hover:bg-secondary rounded"
              >
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Weekday headers */}
            <div className="grid grid-cols-7 gap-1 mb-1">
              {weekDays.map((d) => (
                <div key={d} className="text-center text-xs font-medium text-muted-foreground py-1">
                  {d}
                </div>
              ))}
            </div>
            {/* Calendar grid */}
            <div className="grid grid-cols-7 gap-1">
              {calendarDays.map((day, idx) => {
                const key = formatDateKey(day.date)
                const dayTasks = tasksByDate.get(key) || []
                const taskCount = dayTasks.length
                const isToday = isSameDay(day.date, today)
                const intensity = getIntensityClass(taskCount)

                return (
                  <button
                    key={idx}
                    onClick={() => taskCount > 0 && setSelectedDateKey(key)}
                    className={`relative aspect-square rounded-lg border flex flex-col items-center justify-center transition-colors ${
                      day.isCurrentMonth
                        ? 'border-border hover:border-primary/50'
                        : 'border-transparent opacity-40 hover:opacity-60'
                    } ${intensity} ${isToday ? 'ring-2 ring-primary' : ''}`}
                  >
                    <span className={`text-sm font-medium ${isToday ? 'text-primary' : 'text-foreground'}`}>
                      {day.date.getDate()}
                    </span>
                    {taskCount > 0 && (
                      <span className="text-[10px] text-muted-foreground mt-0.5">{taskCount} 项</span>
                    )}
                  </button>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Drawer Backdrop */}
      {drawerOpen && (
        <div className="fixed inset-0 bg-black/50 z-40" onClick={() => setDrawerOpen(false)} />
      )}

      {/* Drawer */}
      <div
        className={`fixed right-0 top-0 h-full w-[28rem] max-w-full bg-card border-l border-border shadow-xl z-50 transform transition-transform duration-300 flex flex-col ${
          drawerOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="text-base font-semibold">新建发布任务</h3>
          <button onClick={() => setDrawerOpen(false)} className="p-1 hover:bg-secondary rounded">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Draft select */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium">选择草稿</label>
            <select
              value={draftId}
              onChange={(e) => setDraftId(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            >
              <option value="">选择已通过审核的草稿</option>
              {drafts.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title}
                </option>
              ))}
            </select>
          </div>

          {/* Content preview */}
          {selectedDraft && (
            <div className="rounded-lg border border-border p-3 space-y-2 bg-secondary/20">
              <div className="text-xs font-medium text-muted-foreground mb-1">内容预览</div>
              <div className="text-sm font-medium text-foreground">{selectedDraft.title}</div>
              {selectedDraft.cover_image_url ? (
                <img
                  src={selectedDraft.cover_image_url}
                  alt="封面"
                  className="w-full h-32 object-cover rounded-md"
                />
              ) : (
                <div className="w-full h-32 bg-secondary rounded-md flex items-center justify-center">
                  <ImageIcon className="w-6 h-6 text-muted-foreground" />
                </div>
              )}
              {selectedDraft.body && (
                <p className="text-xs text-muted-foreground line-clamp-3">{selectedDraft.body}</p>
              )}
              {selectedDraft.tags && selectedDraft.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {selectedDraft.tags.map((tag) => (
                    <span key={tag} className="inline-flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
                      <Tag className="w-3 h-3" />
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Account select */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium">选择账号</label>
            <select
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            >
              <option value="">选择活跃账号</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.username} ({platformLabels[a.platform] || a.platform})
                </option>
              ))}
            </select>
          </div>

          {/* Platform auto-display */}
          {selectedAccount && (
            <div className="text-xs text-muted-foreground">
              发布平台：{platformLabels[selectedAccount.platform] || selectedAccount.platform}
            </div>
          )}

          {/* Schedule */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium">发布时间</label>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-1.5 text-sm">
                <input
                  type="radio"
                  name="schedule"
                  checked={scheduleMode === 'immediate'}
                  onChange={() => setScheduleMode('immediate')}
                />
                立即
              </label>
              <label className="flex items-center gap-1.5 text-sm">
                <input
                  type="radio"
                  name="schedule"
                  checked={scheduleMode === 'scheduled'}
                  onChange={() => setScheduleMode('scheduled')}
                />
                定时
              </label>
            </div>
            {scheduleMode === 'scheduled' && (
              <input
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm mt-2"
              />
            )}
          </div>
        </div>

        <div className="px-5 py-4 border-t border-border flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDrawerOpen(false)}>
            取消
          </Button>
          <Button onClick={handleCreate} isLoading={isFormLoading} disabled={!draftId || !accountId}>
            创建
          </Button>
        </div>
      </div>

      {/* Preview Modal Backdrop */}
      {previewTask && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setPreviewTask(null)}>
          <div
            className="bg-card rounded-xl border border-border shadow-xl w-full max-w-lg max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h3 className="text-base font-semibold">内容预览</h3>
              <button onClick={() => setPreviewTask(null)} className="p-1 hover:bg-secondary rounded">
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div className="text-lg font-bold text-foreground">{previewTask.draft_title || `任务 #${previewTask.id.slice(0, 8)}`}</div>

              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <Badge variant={statusVariants[previewTask.status] || 'default'}>
                  {statusLabels[previewTask.status] || previewTask.status}
                </Badge>
                <span>
                  {platformLabels[previewTask.platform] || previewTask.platform} · {previewTask.account_name || previewTask.account_id}
                </span>
              </div>

              {previewTask.cover_image_url ? (
                <img src={previewTask.cover_image_url} alt="封面" className="w-full h-48 object-cover rounded-lg" />
              ) : (
                <div className="w-full h-48 bg-secondary rounded-lg flex items-center justify-center">
                  <ImageIcon className="w-8 h-8 text-muted-foreground" />
                </div>
              )}

              {previewTask.body && (
                <div className="text-sm text-foreground whitespace-pre-wrap">{previewTask.body}</div>
              )}

              {previewTask.tags && previewTask.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {previewTask.tags.map((tag) => (
                    <span key={tag} className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-primary/10 text-primary">
                      <Tag className="w-3 h-3" />
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <div className="pt-3 border-t border-border space-y-1 text-xs text-muted-foreground">
                {previewTask.scheduled_at && (
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    排期时间: {new Date(previewTask.scheduled_at).toLocaleString('zh-CN')}
                  </div>
                )}
                {previewTask.published_at && (
                  <div className="flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    发布时间: {new Date(previewTask.published_at).toLocaleString('zh-CN')}
                  </div>
                )}
                {previewTask.published_url && (
                  <a
                    href={previewTask.published_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline flex items-center gap-1"
                  >
                    <ExternalLink className="w-3 h-3" /> 查看已发布内容
                  </a>
                )}
                {previewTask.status === 'published' && previewTask.platform === 'xhs' && (
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <TrendingUp className="w-3 h-3" />
                    24h后自动获取互动数据
                  </div>
                )}
                {previewTask.error_reason && (
                  <div className="text-destructive flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> 错误: {previewTask.error_reason}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Date popup for calendar */}
      {selectedDateKey && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedDateKey(null)}
        >
          <div
            className="bg-card rounded-xl border border-border shadow-xl w-full max-w-md max-h-[70vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h3 className="text-base font-semibold">{selectedDateKey} 的发布任务</h3>
              <button onClick={() => setSelectedDateKey(null)} className="p-1 hover:bg-secondary rounded">
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
            <div className="p-4 space-y-2">
              {selectedDateTasks.length === 0 && (
                <EmptyState icon={CalendarIcon} title="当日无排期" description="该日期没有发布任务" />
              )}
              {selectedDateTasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => {
                    setSelectedDateKey(null)
                    setPreviewTask(task)
                  }}
                  className="p-3 rounded-lg border border-border hover:bg-secondary/30 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-foreground">
                      {task.draft_title || `任务 #${task.id.slice(0, 8)}`}
                    </span>
                    <Badge variant={statusVariants[task.status] || 'default'}>
                      {statusLabels[task.status] || task.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {platformLabels[task.platform] || task.platform} · {task.account_name || task.account_id}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
