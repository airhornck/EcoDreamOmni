import { useEffect } from 'react'
import { useDashboardStore } from '../stores/dashboardStore'
import { Card, CardContent, CardHeader } from './ui/Card'
import { Badge } from './ui/Badge'
import { ListTodo, ExternalLink } from 'lucide-react'

const statusVariantMap: Record<string, 'warning' | 'info' | 'primary' | 'success' | 'danger' | 'default'> = {
  pending: 'warning',
  scheduled: 'info',
  publishing: 'primary',
  published: 'success',
  failed: 'danger',
  cancelled: 'default',
}

const statusLabels: Record<string, string> = {
  pending: '待处理',
  scheduled: '已调度',
  publishing: '发布中',
  published: '已发布',
  failed: '失败',
  cancelled: '已取消',
}

export function TaskBoard() {
  const { publishTasks, fetchPublishTasks } = useDashboardStore()

  useEffect(() => {
    fetchPublishTasks()
  }, [fetchPublishTasks])

  return (
    <Card>
      <CardHeader className="flex items-center gap-2">
        <ListTodo className="w-4 h-4 text-primary" />
        <h2 className="text-base font-semibold text-foreground">发布任务看板</h2>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {publishTasks.length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-muted-foreground">暂无发布任务</div>
          )}
          {publishTasks.map((task) => (
            <div key={task.id} className="px-5 py-3 flex items-center gap-3">
              <span className="text-sm font-medium text-foreground min-w-[6rem]">{task.draft_id}</span>
              <Badge variant="default">{task.platform}</Badge>
              <Badge variant={statusVariantMap[task.status] || 'default'}>
                {statusLabels[task.status] || task.status}
              </Badge>
              {task.scheduled_at && (
                <span className="text-xs text-muted-foreground ml-auto">
                  {new Date(task.scheduled_at).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
              {task.status === 'published' && task.published_url && (
                <a
                  href={task.published_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline ml-auto flex items-center gap-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  查看
                </a>
              )}
              {task.status === 'failed' && task.error_reason && (
                <span className="text-xs text-destructive ml-auto">{task.error_reason}</span>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
