import { useEffect, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import { useAICopilotStore } from '../stores/aiCopilotStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Badge, type BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { Search, Tag, CheckSquare, Square } from 'lucide-react'

interface Keyword {
  id: string
  keyword: string
  dimension: 'structure' | 'function' | 'emotion' | 'industry' | 'effect'
  weight: number
  is_active: boolean
}

const dimensions = [
  { key: 'all', label: '全部' },
  { key: 'structure', label: '结构' },
  { key: 'function', label: '功能' },
  { key: 'emotion', label: '情感' },
  { key: 'industry', label: '行业' },
  { key: 'effect', label: '效果' },
] as const

const dimVariant: Record<string, BadgeVariant> = {
  structure: 'info', function: 'success', emotion: 'danger', industry: 'warning', effect: 'primary',
}
const dimLabel: Record<string, string> = {
  structure: '结构', function: '功能', emotion: '情感', industry: '行业', effect: '效果',
}

async function fetchKeywords(): Promise<Keyword[]> {
  const res = await apiClient<{ keywords: Keyword[] }>('/api/playground/keywords')
  return res.keywords ?? []
}

export function KeywordLibraryPage() {
  const queryClient = useQueryClient()
  const { setPageActionCards, setPageActionHandler } = useAICopilotStore()
  const [search, setSearch] = useState('')
  const [dimFilter, setDimFilter] = useState<string>('all')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const { data: keywords = [], isLoading } = useQuery({ queryKey: ['keywords'], queryFn: fetchKeywords })

  const createMut = useMutation({
    mutationFn: (payload: Omit<Keyword, 'id'>) =>
      apiClient('/api/playground/keywords', { method: 'POST', body: JSON.stringify(payload) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['keywords'] }),
  })
  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<Keyword> }) =>
      apiClient(`/api/playground/keywords/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['keywords'] }),
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => apiClient(`/api/playground/keywords/${id}`, { method: 'DELETE' }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['keywords'] }); setSelectedIds(new Set()) },
  })

  const filtered = useMemo(() => keywords.filter((k) => {
    const matchDim = dimFilter === 'all' || k.dimension === dimFilter
    const matchSearch = !search || k.keyword.toLowerCase().includes(search.toLowerCase())
    return matchDim && matchSearch
  }), [keywords, dimFilter, search])

  const selectedList = useMemo(() => keywords.filter((k) => selectedIds.has(k.id)), [keywords, selectedIds])

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    setSelectedIds(next)
  }
  const selectAll = () => {
    setSelectedIds(selectedIds.size === filtered.length && filtered.length > 0 ? new Set() : new Set(filtered.map((k) => k.id)))
  }

  // 上下文由 LayoutWrapper 的 useCopilotPageSync 统一注入。
  // 此处保留页面级 Action Cards（向后端驱动逐步迁移）。
  useEffect(() => {
    const sel = selectedList.length === 1 ? selectedList[0] : null
    setPageActionCards([
      {
        id: 'keyword-add', type: 'generation', title: '新增关键词',
        description: '在关键词库中新增一个爆款分析关键词', priority: 1,
        inputs: [
          { name: 'keyword', label: '关键词', type: 'text', placeholder: '输入关键词' },
          { name: 'dimension', label: '维度', type: 'text', placeholder: 'structure / function / emotion / industry / effect' },
          { name: 'weight', label: '权重', type: 'text', placeholder: '1-100' },
        ],
        actions: [{ id: 'create', label: '确认新增', variant: 'primary' }],
      },
      {
        id: 'keyword-edit', type: 'suggestion', title: '编辑选中',
        description: sel ? `编辑「${sel.keyword}」` : '请选中一条关键词进行编辑', priority: 2,
        inputs: sel ? [
          { name: 'keyword', label: '关键词', type: 'text', placeholder: sel.keyword },
          { name: 'dimension', label: '维度', type: 'text', placeholder: sel.dimension },
          { name: 'weight', label: '权重', type: 'text', placeholder: String(sel.weight) },
        ] : [],
        actions: sel ? [{ id: 'save', label: '保存修改', variant: 'primary' }] : [],
      },
      {
        id: 'keyword-delete', type: 'decision', title: '删除选中',
        description: selectedList.length > 0 ? `即将删除 ${selectedList.length} 个关键词` : '请选中至少一条关键词', priority: 3,
        actions: selectedList.length > 0 ? [{ id: 'confirm', label: '确认删除', variant: 'primary' }] : [],
      },
      {
        id: 'keyword-toggle', type: 'decision', title: '启用/停用',
        description: selectedList.length > 0 ? `切换 ${selectedList.length} 个关键词的启用状态` : '请选中至少一条关键词', priority: 4,
        actions: selectedList.length > 0 ? [
          { id: 'enable', label: '启用', variant: 'primary' },
          { id: 'disable', label: '停用', variant: 'secondary' },
        ] : [],
      },
    ])

    setPageActionHandler(async (cardId, actionId, payload) => {
      if (cardId === 'keyword-add') {
        const p = payload as Record<string, string>
        await createMut.mutateAsync({
          keyword: p.keyword || '', dimension: (p.dimension || 'structure') as Keyword['dimension'],
          weight: Number(p.weight) || 50, is_active: true,
        })
      } else if (cardId === 'keyword-edit' && sel) {
        const p = payload as Record<string, string>
        await updateMut.mutateAsync({
          id: sel.id, payload: {
            keyword: p.keyword || undefined, dimension: (p.dimension as Keyword['dimension']) || undefined,
            weight: p.weight ? Number(p.weight) : undefined,
          },
        })
      } else if (cardId === 'keyword-delete') {
        for (const k of selectedList) await deleteMut.mutateAsync(k.id)
      } else if (cardId === 'keyword-toggle') {
        for (const k of selectedList) await updateMut.mutateAsync({ id: k.id, payload: { is_active: actionId === 'enable' } })
      }
    })

    return () => { setPageActionCards([]); setPageActionHandler(null) }
  }, [selectedList, setPageActionCards, setPageActionHandler, createMut, updateMut, deleteMut])

  return (
    <div className="space-y-5">
      <PageHeader title="关键词库" subtitle="爆款笔记分析关键词管理 · 支持 5 大维度" />

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input type="text" placeholder="搜索关键词..." value={search} onChange={(e) => setSearch(e.target.value)}
            className="h-9 pl-9 pr-3 rounded-lg border border-border bg-background text-sm w-56 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all" />
        </div>
        <div className="flex gap-1">
          {dimensions.map((d) => (
            <button key={d.key} onClick={() => setDimFilter(d.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${dimFilter === d.key ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'}`}>
              {d.label}
            </button>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader className="flex items-center gap-2">
          <Tag className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold">关键词列表</h2>
          <Badge variant="default">{filtered.length}</Badge>
          {selectedIds.size > 0 && <Badge variant="primary">{selectedIds.size} 已选</Badge>}
        </CardHeader>
        <CardContent>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && filtered.length === 0 && (
            <EmptyState icon={Tag} title="暂无关键词" description="当前过滤条件下没有关键词" />
          )}
          {!isLoading && filtered.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="py-3 pr-4 w-10">
                      <button onClick={selectAll} className="hover:text-foreground">
                        {selectedIds.size === filtered.length && filtered.length > 0 ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
                      </button>
                    </th>
                    <th className="py-3 pr-4 font-medium">关键词</th>
                    <th className="py-3 pr-4 font-medium">维度</th>
                    <th className="py-3 pr-4 font-medium">权重</th>
                    <th className="py-3 pr-4 font-medium">状态</th>
                    <th className="py-3 font-medium">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((k) => (
                    <tr key={k.id} className={`border-b border-border last:border-0 transition-colors ${selectedIds.has(k.id) ? 'bg-primary/5' : 'hover:bg-secondary/30'}`}>
                      <td className="py-3 pr-4">
                        <button onClick={() => toggleSelect(k.id)} className="hover:text-foreground">
                          {selectedIds.has(k.id) ? <CheckSquare className="w-4 h-4 text-primary" /> : <Square className="w-4 h-4 text-muted-foreground" />}
                        </button>
                      </td>
                      <td className="py-3 pr-4 font-medium text-foreground">{k.keyword}</td>
                      <td className="py-3 pr-4"><Badge variant={dimVariant[k.dimension] || 'default'}>{dimLabel[k.dimension] || k.dimension}</Badge></td>
                      <td className="py-3 pr-4 text-muted-foreground">{k.weight}</td>
                      <td className="py-3 pr-4"><Badge variant={k.is_active ? 'success' : 'default'}>{k.is_active ? '启用' : '停用'}</Badge></td>
                      <td className="py-3 text-muted-foreground text-xs">{selectedIds.has(k.id) ? '已选' : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dimension Legend */}
      <div className="flex items-center gap-4 text-[11px] text-muted-foreground">
        <span className="font-medium">维度图例：</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500" />结构</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" />功能</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />情感</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />行业</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-violet-500" />效果</span>
      </div>
    </div>
  )
}
