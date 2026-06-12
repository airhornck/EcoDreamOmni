import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDashboardStore } from '../stores/dashboardStore'
import { Card, CardContent, CardHeader } from './ui/Card'
import { Badge } from './ui/Badge'
import { FileText, Plus } from 'lucide-react'

const statusVariantMap: Record<string, 'default' | 'warning' | 'info' | 'success' | 'danger'> = {
  draft: 'default',
  reviewing: 'warning',
  approved: 'info',
  published: 'success',
  rejected: 'danger',
}

const statusLabels: Record<string, string> = {
  draft: '草稿',
  reviewing: '审核中',
  approved: '已通过',
  published: '已发布',
  rejected: '已驳回',
}

export function ContentLibrary() {
  const navigate = useNavigate()
  const { contentDrafts, fetchContentDrafts } = useDashboardStore()

  useEffect(() => {
    fetchContentDrafts()
  }, [fetchContentDrafts])

  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold text-foreground">内容库</h2>
        </div>
        <button 
          onClick={() => navigate('/content-forge')}
          className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          生成内容
        </button>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {contentDrafts.length === 0 && (
            <div className="col-span-full text-center py-8 text-sm text-muted-foreground bg-secondary/50 rounded-lg border border-border border-dashed">
              暂无内容草稿
            </div>
          )}
          {contentDrafts.map((draft) => (
            <div
              key={draft.id}
              className="p-4 bg-card rounded-lg border border-border hover:border-primary/30 hover:shadow-sm transition-all"
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-sm font-medium text-foreground line-clamp-1">{draft.title}</h3>
                <Badge variant={statusVariantMap[draft.status] || 'default'}>
                  {statusLabels[draft.status] || draft.status}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{draft.body}</p>
              <div className="flex items-center gap-2">
                <Badge variant="default">{draft.platform}</Badge>
                <span className="text-xs text-muted-foreground">{draft.content_type}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
