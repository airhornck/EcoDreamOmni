import { useEffect, useState, useMemo } from 'react'
import {
  Clock,
  Play,
  CheckCircle,
  XCircle,
  RotateCcw,
  Trash2,
  Edit,
  Pause,
  Filter,
  AlertTriangle,
  Activity,
  Percent,
  Inbox,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { useCronCockpitStore } from '../stores/cronCockpitStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import type { BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'

function estimateNextRun(schedule: string): string {
  const parts = schedule.trim().split(/\s+/)
  if (parts.length !== 5) return '未知'
  const [minute, hour] = parts
  const now = new Date()

  if (minute !== '*' && hour !== '*' && parts[2] === '*' && parts[3] === '*' && parts[4] === '*') {
    const targetHour = parseInt(hour, 10)
    const targetMin = parseInt(minute, 10)
    if (isNaN(targetHour) || isNaN(targetMin)) return '近期执行'
    if (now.getHours() < targetHour || (now.getHours() === targetHour && now.getMinutes() < targetMin)) {
      return `今天 ${String(targetHour).padStart(2, '0')}:${String(targetMin).padStart(2, '0')}`
    }
    return `明天 ${String(targetHour).padStart(2, '0')}:${String(targetMin).padStart(2, '0')}`
  }
  if (minute !== '*' && hour === '*') {
    const targetMin = parseInt(minute, 10)
    if (!isNaN(targetMin)) {
      if (now.getMinutes() < targetMin) return `${targetMin - now.getMinutes()}分钟后`
      return `${60 - now.getMinutes() + targetMin}分钟后`
    }
  }
  if (parts[4] !== '*') {
    return '下周同一时间'
  }
  return '近期执行'
}

function formatDuration(ms: number | null): string {
  if (ms == null) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${Math.floor(ms / 1000)}s`
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
}

export function CronCockpitPage() {
  const {
    jobs, executions, dlq,
    isLoading, error, activeTab,
    fetchJobs, fetchExecutions, fetchDLQ,
    deleteJob, executeJob, retryExecution, reviewDLQ,
    setActiveTab, clearError,
  } = useCronCockpitStore()

  const [disabledJobs, setDisabledJobs] = useState<Set<string>>(new Set())
  const [executionFilter, setExecutionFilter] = useState<'ALL' | 'SUCCESS' | 'FAILED'>('ALL')
  const [expandedDLQ, setExpandedDLQ] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchJobs()
    fetchExecutions()
    fetchDLQ()
  }, [fetchJobs, fetchExecutions, fetchDLQ])

  const tabs = [
    { key: 'jobs' as const, label: '定时任务', icon: Clock },
    { key: 'executions' as const, label: '执行历史', icon: Activity },
    { key: 'dlq' as const, label: '死信队列', icon: AlertTriangle },
  ] as const

  const todayStr = new Date().toISOString().slice(0, 10)

  const successRate = useMemo(() => {
    const now = new Date()
    const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString()
    const recent = executions.filter((e) => e.scheduled_at >= sevenDaysAgo)
    if (recent.length === 0) return '-'
    const success = recent.filter((e) => e.status === 'SUCCESS').length
    return `${Math.round((success / recent.length) * 100)}%`
  }, [executions])

  const stats = [
    { label: '活跃任务数', value: jobs.filter((j) => j.status === 'ACTIVE' && !disabledJobs.has(j.id)).length, icon: Activity },
    { label: '今日执行数', value: executions.filter((e) => e.scheduled_at?.slice(0, 10) === todayStr).length, icon: CheckCircle },
    { label: '成功率（近7日）', value: successRate, icon: Percent },
    { label: 'DLQ待处理', value: dlq.filter((d) => d.status !== 'REVIEWED').length, icon: Inbox },
  ]

  const filteredExecutions = useMemo(() => {
    if (executionFilter === 'ALL') return executions
    return executions.filter((e) => e.status === executionFilter)
  }, [executions, executionFilter])

  const toggleJobEnabled = (id: string) => {
    setDisabledJobs((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleDLQExpand = (id: string) => {
    setExpandedDLQ((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const jobStatusVariant = (status: string, isDisabled: boolean): BadgeVariant => {
    if (isDisabled) return 'default'
    switch (status) {
      case 'ACTIVE': return 'success'
      case 'PAUSED': return 'warning'
      case 'ARCHIVED': return 'default'
      default: return 'default'
    }
  }

  const execStatusVariant = (status: string): BadgeVariant => {
    switch (status) {
      case 'SUCCESS': return 'success'
      case 'FAILED': return 'danger'
      case 'RUNNING': return 'info'
      case 'SKIPPED': return 'default'
      default: return 'default'
    }
  }

  const dlqStatusVariant = (retryExhausted: boolean): BadgeVariant => {
    return retryExhausted ? 'danger' : 'warning'
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="定时任务"
        subtitle="Cron 任务调度、执行历史与死信队列管理"
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

      {/* Jobs Tab */}
      {activeTab === 'jobs' && !isLoading && (
        <section>
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">名称</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">Cron 表达式</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">目标</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">并发策略</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">下次执行</th>
                    <th className="text-left px-5 py-3 font-medium text-muted-foreground">状态</th>
                    <th className="text-right px-5 py-3 font-medium text-muted-foreground">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {jobs.map((j) => {
                    const isDisabled = disabledJobs.has(j.id)
                    return (
                      <tr key={j.id} className="hover:bg-muted/50">
                        <td className="px-5 py-3 text-foreground font-medium">
                          <div className="flex items-center gap-2">
                            {j.name}
                            {isDisabled && <Badge variant="default">已停用</Badge>}
                          </div>
                        </td>
                        <td className="px-5 py-3 font-mono text-muted-foreground">{j.schedule}</td>
                        <td className="px-5 py-3 text-muted-foreground">{j.target_type}:{j.target_id}</td>
                        <td className="px-5 py-3 text-muted-foreground">{j.concurrency_policy}</td>
                        <td className="px-5 py-3 text-muted-foreground text-xs">{estimateNextRun(j.schedule)}</td>
                        <td className="px-5 py-3">
                          <Badge variant={jobStatusVariant(j.status, isDisabled)}>{isDisabled ? 'PAUSED' : j.status}</Badge>
                        </td>
                        <td className="px-5 py-3 text-right">
                          <div className="inline-flex items-center gap-1">
                            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => executeJob(j.id)} title="执行">
                              <Play className="w-3.5 h-3.5" />
                            </Button>
                            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" title="编辑">
                              <Edit className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0"
                              onClick={() => toggleJobEnabled(j.id)}
                              title={isDisabled ? '启用' : '停用'}
                            >
                              {isDisabled ? <Play className="w-3.5 h-3.5 text-success" /> : <Pause className="w-3.5 h-3.5 text-warning" />}
                            </Button>
                            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => deleteJob(j.id)} title="删除">
                              <Trash2 className="w-3.5 h-3.5 text-destructive" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                  {jobs.length === 0 && (
                    <tr>
                      <td colSpan={7}>
                        <EmptyState icon={Clock} title="暂无定时任务" />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </section>
      )}

      {/* Executions Tab */}
      {activeTab === 'executions' && !isLoading && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">筛选:</span>
            {(['ALL', 'SUCCESS', 'FAILED'] as const).map((f) => (
              <Button
                key={f}
                variant={executionFilter === f ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setExecutionFilter(f)}
              >
                {f === 'ALL' ? '全部' : f === 'SUCCESS' ? '成功' : '失败'}
              </Button>
            ))}
          </div>
          <div className="space-y-2">
            {filteredExecutions.map((ex) => (
              <Card key={ex.id} shadow="sm" hover>
                <CardContent className="flex items-center gap-4 py-3">
                  <span className="text-xs font-mono text-muted-foreground w-20">{ex.id.slice(0, 12)}</span>
                  <Badge variant="default" className="shrink-0">{ex.execution_type}</Badge>
                  <Badge variant={execStatusVariant(ex.status)} className="shrink-0">{ex.status}</Badge>
                  <span className="text-sm text-foreground flex-1 truncate">{ex.output_summary ?? ex.error_message ?? '-'}</span>
                  <span className="text-xs text-muted-foreground shrink-0">{formatDuration(ex.duration_ms)}</span>
                  {ex.status === 'FAILED' && (
                    <Button variant="ghost" size="sm" className="h-7 px-2 shrink-0" onClick={() => retryExecution(ex.id)}>
                      <RotateCcw className="w-3.5 h-3.5 mr-1" />
                      <span className="text-xs">重试</span>
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
            {filteredExecutions.length === 0 && (
              <EmptyState icon={Activity} title="暂无执行记录" description="选择其他筛选条件或稍后再试" />
            )}
          </div>
        </section>
      )}

      {/* DLQ Tab */}
      {activeTab === 'dlq' && !isLoading && (
        <section className="space-y-2">
          {dlq.map((d) => (
            <Card key={d.id} shadow="sm" hover>
              <CardContent className="py-3">
                <div className="flex items-center gap-4">
                  <span className="text-xs font-mono text-muted-foreground w-20">{d.id.slice(0, 12)}</span>
                  <span className="text-xs text-muted-foreground">{d.job_id}</span>
                  <Badge variant={dlqStatusVariant(d.retry_exhausted)}>{d.retry_exhausted ? '已耗尽' : '可重试'}</Badge>
                  <div className="flex gap-1 ml-auto">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2"
                      onClick={() => reviewDLQ(d.id, 'RETRIED', 'admin')}
                    >
                      <RotateCcw className="w-3.5 h-3.5 mr-1 text-primary" />
                      <span className="text-xs">重试</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2"
                      onClick={() => reviewDLQ(d.id, 'IGNORED', 'admin')}
                    >
                      <XCircle className="w-3.5 h-3.5 mr-1 text-muted-foreground" />
                      <span className="text-xs">忽略</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => toggleDLQExpand(d.id)}
                    >
                      {expandedDLQ.has(d.id) ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </Button>
                  </div>
                </div>
                {expandedDLQ.has(d.id) && (
                  <div className="mt-3 p-3 rounded-md bg-destructive/5 border border-destructive/10">
                    <div className="text-xs font-medium text-destructive mb-1">错误详情</div>
                    <div className="text-xs text-muted-foreground font-mono">{d.error_message}</div>
                    <div className="text-xs text-muted-foreground mt-1">错误类型: {d.error_type}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
          {dlq.length === 0 && (
            <EmptyState icon={Inbox} title="死信队列为空" description="所有任务均正常执行" />
          )}
        </section>
      )}
    </div>
  )
}
