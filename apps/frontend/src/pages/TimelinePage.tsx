import { useEffect, useState } from 'react'
import { useTimelineStore } from '../stores/timelineStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { Calendar, Plus, Trash2, Repeat, Sparkles, Package, Clock } from 'lucide-react'

const typeLabels: Record<string, string> = {
  SEASONAL: '季节节点',
  PRODUCT_LAUNCH: '产品上市',
  PLATFORM_PROMO: '平台大促',
  CUSTOM: '自定义',
}

const typeIcons: Record<string, React.ElementType> = {
  SEASONAL: Clock,
  PRODUCT_LAUNCH: Package,
  PLATFORM_PROMO: Sparkles,
  CUSTOM: Calendar,
}

const statusColors: Record<string, string> = {
  active: 'bg-success/15 text-success',
  draft: 'bg-yellow-100 text-yellow-700',
  archived: 'bg-muted text-foreground',
}

interface TimelineForm {
  event_type: string
  status: string
  recurring: boolean
  year: number
  name?: string
  start_date?: string
  end_date?: string
  description?: string
  cron_expression?: string
  is_commercial?: boolean
  priority?: number
  color_code?: string
}

export function TimelinePage() {
  const { events, isLoading, error, fetchEvents, createEvent, deleteEvent } = useTimelineStore()
  const [showCreate, setShowCreate] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [filterYear, setFilterYear] = useState(new Date().getFullYear().toString())
  const [form, setForm] = useState<TimelineForm>({ event_type: 'SEASONAL', status: 'active', recurring: false, year: new Date().getFullYear() })

  useEffect(() => {
    const filters: Record<string, string> = {}
    if (filterType) filters.event_type = filterType
    if (filterYear) filters.year = filterYear
    fetchEvents(filters)
  }, [fetchEvents, filterType, filterYear])

  const handleCreate = async () => {
    if (!form.name?.trim() || !form.start_date || !form.end_date) return
    const success = await createEvent({
      name: form.name,
      event_type: form.event_type,
      start_date: form.start_date,
      end_date: form.end_date,
      description: form.description || undefined,
      recurring: !!form.recurring,
      cron_expression: form.cron_expression || undefined,
      year: Number(form.year) || new Date().getFullYear(),
      is_commercial: !!form.is_commercial,
      status: form.status || 'active',
      priority: Number(form.priority) || 0,
      color_code: form.color_code || undefined,
    } as Record<string, unknown>)
    if (success) {
      setShowCreate(false)
      setForm({ event_type: 'SEASONAL', status: 'active', recurring: false, year: new Date().getFullYear() })
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="时间线库"
        subtitle="产品上市时间线、季节营销节点、平台大促日历 — 驱动选题推荐与定时发布"
        action={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="w-4 h-4" />
            新增事件
          </Button>
        }
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap items-center gap-3">
            <select
              className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="">全部类型</option>
              <option value="SEASONAL">季节节点</option>
              <option value="PRODUCT_LAUNCH">产品上市</option>
              <option value="PLATFORM_PROMO">平台大促</option>
              <option value="CUSTOM">自定义</option>
            </select>
            <input
              type="number"
              placeholder="年份"
              className="h-9 px-3 rounded-lg border border-border bg-background text-sm w-24"
              value={filterYear}
              onChange={(e) => setFilterYear(e.target.value)}
            />
            <Button variant="ghost" size="sm" onClick={() => { setFilterType(''); setFilterYear(new Date().getFullYear().toString()) }}>
              重置
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Create Drawer */}
      {showCreate && (
        <Card>
          <CardHeader><h3 className="text-base font-semibold">新增时间线事件</h3></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                placeholder="事件名称 *"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.name || ''}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
              <select
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.event_type || 'SEASONAL'}
                onChange={(e) => setForm({ ...form, event_type: e.target.value })}
              >
                <option value="SEASONAL">季节节点</option>
                <option value="PRODUCT_LAUNCH">产品上市</option>
                <option value="PLATFORM_PROMO">平台大促</option>
                <option value="CUSTOM">自定义</option>
              </select>
              <input
                type="date"
                placeholder="开始日期 *"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.start_date || ''}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
              />
              <input
                type="date"
                placeholder="结束日期 *"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.end_date || ''}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
              />
              <input
                type="number"
                placeholder="年份"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.year || new Date().getFullYear()}
                onChange={(e) => setForm({ ...form, year: Number(e.target.value) })}
              />
              <input
                type="number"
                placeholder="优先级"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.priority || 0}
                onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })}
              />
            </div>
            <textarea
              placeholder="事件描述"
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
              value={form.description || ''}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={!!form.recurring}
                  onChange={(e) => setForm({ ...form, recurring: e.target.checked })}
                  className="rounded border-border"
                />
                周期性事件
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={!!form.is_commercial}
                  onChange={(e) => setForm({ ...form, is_commercial: e.target.checked })}
                  className="rounded border-border"
                />
                商业内容
              </label>
            </div>
            {form.recurring && (
              <input
                placeholder="Cron表达式（如 0 9 * * *）"
                className="h-9 px-3 rounded-lg border border-border bg-background text-sm"
                value={form.cron_expression || ''}
                onChange={(e) => setForm({ ...form, cron_expression: e.target.value })}
              />
            )}
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
              <Button onClick={handleCreate}>保存</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* List */}
      <Card>
        <CardHeader className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold">事件列表 ({events.length})</h2>
        </CardHeader>
        <CardContent>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && events.length === 0 && (
            <EmptyState icon={Calendar} title="暂无事件" description="创建你的第一个营销时间线事件" />
          )}
          <div className="space-y-2">
            {events.map((event) => {
              const Icon = typeIcons[event.event_type] || Calendar
              return (
                <div key={event.id} className="p-4 rounded-lg border border-border hover:border-primary/30 transition-all">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Icon className="w-4 h-4 text-muted-foreground" />
                        <h3 className="text-sm font-medium text-foreground">{event.name}</h3>
                        <Badge className={statusColors[event.status] || 'bg-muted'}>
                          {event.status === 'active' ? '活跃' : event.status === 'draft' ? '草稿' : '已归档'}
                        </Badge>
                        {event.recurring && (
                          <Badge variant="default" className="bg-transparent border-border text-muted-foreground flex items-center gap-1">
                            <Repeat className="w-3 h-3" /> 周期
                          </Badge>
                        )}
                        {event.is_commercial && (
                          <Badge variant="default" className="bg-transparent border-amber-200 text-amber-600">商业</Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">{event.description}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                        <span>{event.start_date?.slice(0, 10)} ~ {event.end_date?.slice(0, 10)}</span>
                        <span>类型: {typeLabels[event.event_type] || event.event_type}</span>
                        <span>年份: {event.year}</span>
                        {event.priority > 0 && <span>优先级: {event.priority}</span>}
                      </div>
                    </div>
                    <button onClick={() => deleteEvent(event.id)} className="p-1.5 hover:bg-destructive/10 rounded ml-2">
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
