import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAICopilotStore } from '../stores/aiCopilotStore'
import type { PageActionCard } from '../stores/aiCopilotStore'
import { apiClient } from '../lib/api'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import type { BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { Search, FileText, LayoutTemplate, Loader2 } from 'lucide-react'

/* ── types ── */

interface ContentTemplate {
  id: string
  template_id: string
  source: 'manual' | 'viral_analyzer' | 'ai_generated'
  structure_type: string
  usage_count: number
  status: 'active' | 'inactive' | 'draft'
  title?: string
  description?: string
}

/* ── constants ── */

const sourceLabels: Record<string, string> = {
  manual: '手动创建',
  viral_analyzer: '爆款分析',
  ai_generated: 'AI 生成',
}

const sourceVariants: Record<string, BadgeVariant> = {
  manual: 'default',
  viral_analyzer: 'warning',
  ai_generated: 'primary',
}

const statusLabels: Record<string, string> = {
  active: '生效中',
  inactive: '已停用',
  draft: '草稿',
}

const statusVariants: Record<string, BadgeVariant> = {
  active: 'success',
  inactive: 'default',
  draft: 'warning',
}

const templateKeys = {
  all: ['content-templates'] as const,
  list: () => [...templateKeys.all, 'list'] as const,
}

/* ── page ── */

export function TemplateLibraryPage() {
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { setPageActionCards, setPageActionHandler } = useAICopilotStore()

  const { data: templates = [], isLoading } = useQuery({
    queryKey: templateKeys.list(),
    queryFn: async () => {
      const res = await apiClient<{ templates: ContentTemplate[] }>('/api/content-templates')
      return res.templates ?? []
    },
  })

  const structureTypes = useMemo(() => {
    const types = new Set<string>()
    templates.forEach((t) => { if (t.structure_type) types.add(t.structure_type) })
    return Array.from(types).sort()
  }, [templates])

  const filtered = useMemo(() => {
    return templates.filter((t) => {
      if (sourceFilter !== 'all' && t.source !== sourceFilter) return false
      if (typeFilter !== 'all' && t.structure_type !== typeFilter) return false
      if (search) {
        const q = search.toLowerCase()
        const text = `${t.template_id} ${t.title || ''} ${t.structure_type}`.toLowerCase()
        if (!text.includes(q)) return false
      }
      return true
    })
  }, [templates, sourceFilter, typeFilter, search])

  /* Copilot Action Cards — 上下文由 useCopilotPageSync 统一注入 */
  useEffect(() => {
    setPageActionHandler(async (_cardId, actionId) => {
      if (actionId === 'preview') {
        console.log('Preview template:', selectedId)
      } else if (actionId === 'apply') {
        console.log('Apply template:', selectedId)
      } else if (actionId === 'delete') {
        console.log('Delete template:', selectedId)
      }
    })

    return () => {
      setPageActionCards([])
      setPageActionHandler(null)
    }
  }, [setPageActionCards, setPageActionHandler, selectedId])

  useEffect(() => {
    if (!selectedId) {
      setPageActionCards([])
      return
    }
    const selected = templates.find((t) => t.id === selectedId)
    if (!selected) return

    const cards: PageActionCard[] = [
      {
        id: 'template-preview',
        type: 'info',
        title: '预览模板',
        description: `查看模板 ${selected.template_id} 的详细结构`,
        actions: [{ id: 'preview', label: '预览', variant: 'primary' }],
      },
      {
        id: 'template-apply',
        type: 'suggestion',
        title: '应用到内容生产',
        description: `将模板 ${selected.template_id} 应用到内容锻造流程`,
        actions: [{ id: 'apply', label: '应用', variant: 'primary' }],
      },
      {
        id: 'template-delete',
        type: 'decision',
        title: '删除模板',
        description: `确认删除模板 ${selected.template_id}？此操作不可撤销。`,
        actions: [
          { id: 'delete', label: '确认删除', variant: 'primary' },
          { id: 'cancel', label: '取消', variant: 'ghost' },
        ],
      },
    ]
    setPageActionCards(cards)
  }, [selectedId, templates, setPageActionCards])

  return (
    <div className="h-full flex flex-col space-y-5">
      <PageHeader
        title="模板库"
        subtitle="ContentTemplate 管理 · 实验室爆款笔记分析"
      />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索模板 ID、标题、结构类型..."
            className="w-full h-9 pl-9 pr-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
          />
        </div>
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:border-primary transition-colors"
        >
          <option value="all">全部来源</option>
          <option value="manual">手动创建</option>
          <option value="viral_analyzer">爆款分析</option>
          <option value="ai_generated">AI 生成</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:border-primary transition-colors"
        >
          <option value="all">全部结构类型</option>
          {structureTypes.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={LayoutTemplate}
          title="暂无模板"
          description="尝试调整筛选条件或在 Copilot 中创建新模板"
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((t) => (
            <div
              key={t.id}
              className="cursor-pointer"
              onClick={() => setSelectedId(t.id === selectedId ? null : t.id)}
            >
              <Card
                hover
                className={`transition-all ${selectedId === t.id ? 'border-2 border-primary' : 'border border-border'}`}
              >
                <CardContent className="p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="w-4 h-4 text-primary shrink-0" />
                    <span className="text-sm font-medium truncate">{t.template_id}</span>
                  </div>
                  <Badge variant={statusVariants[t.status] || 'default'}>
                    {statusLabels[t.status] || t.status}
                  </Badge>
                </div>
                {t.title && (
                  <p className="text-xs text-muted-foreground truncate">{t.title}</p>
                )}
                <div className="flex flex-wrap gap-2">
                  <Badge variant={sourceVariants[t.source] || 'default'}>
                    {sourceLabels[t.source] || t.source}
                  </Badge>
                  {t.structure_type && (
                    <Badge variant="default">{t.structure_type}</Badge>
                  )}
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground pt-1 border-t border-border">
                  <span>使用次数</span>
                  <span className="font-medium text-foreground">{t.usage_count}</span>
                </div>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      )}

      {/* Source Legend */}
      <div className="flex items-center gap-4 text-[11px] text-muted-foreground">
        <span className="font-medium">来源图例：</span>
        <span className="flex items-center gap-1"><Badge variant="default" className="text-[10px]">手动创建</Badge></span>
        <span className="flex items-center gap-1"><Badge variant="warning" className="text-[10px]">爆款分析</Badge></span>
        <span className="flex items-center gap-1"><Badge variant="primary" className="text-[10px]">AI 生成</Badge></span>
      </div>
    </div>
  )
}
