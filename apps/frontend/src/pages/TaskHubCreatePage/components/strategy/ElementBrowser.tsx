import { useMemo, useState } from 'react'
import { Search, Plus, Wand2 } from 'lucide-react'
import { useDroppable } from '@dnd-kit/core'
import { Badge } from '../../../../components/ui/Badge'
import { EmptyState } from '../../../../components/ui/EmptyState'
import type { ElementType, StrategyElement } from '../../../../types/strategy'
import { ELEMENT_TYPE_ICONS, ELEMENT_TYPE_LABELS } from '../../../../types/strategy'

interface ElementBrowserProps {
  elements: StrategyElement[]
  selectedIds: string[]
  platform?: string
  topic?: string
  onAdd: (elementId: string) => void
  onRecommend?: () => void
}

export function ElementBrowser({
  elements,
  selectedIds,
  platform,
  topic,
  onAdd,
  onRecommend,
}: ElementBrowserProps) {
  const [search, setSearch] = useState('')
  const [activeFilter, setActiveFilter] = useState<ElementType | 'all'>('all')

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return elements.filter((el) => {
      if (el.status !== 'active') return false
      if (activeFilter !== 'all' && el.element_type !== activeFilter) return false
      if (platform && el.platform && el.platform !== platform) return false
      if (!q) return true
      return (
        el.name.toLowerCase().includes(q) ||
        (el.description ?? '').toLowerCase().includes(q) ||
        (el.category ?? '').toLowerCase().includes(q)
      )
    })
  }, [elements, activeFilter, platform, search])

  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = { all: elements.filter((e) => e.status === 'active').length }
    for (const el of elements) {
      if (el.status !== 'active') continue
      counts[el.element_type] = (counts[el.element_type] || 0) + 1
    }
    return counts
  }, [elements])

  const { setNodeRef, isOver } = useDroppable({ id: 'element-browser' })

  return (
    <div className="flex flex-col h-full" ref={setNodeRef}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold">元素库</h4>
        {onRecommend && topic && (
          <button
            onClick={onRecommend}
            className="flex items-center gap-1 text-xs text-primary hover:underline"
            title="基于主题智能推荐"
          >
            <Wand2 className="w-3.5 h-3.5" />
            智能推荐
          </button>
        )}
      </div>

      {/* Search */}
      <div className="relative mb-3">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索策略元素..."
          className="w-full h-8 pl-8 pr-3 rounded-md border border-border bg-background text-sm placeholder:text-muted-foreground"
        />
      </div>

      {/* Type filter tabs */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        <button
          onClick={() => setActiveFilter('all')}
          className={`px-2 py-0.5 rounded-full text-xs font-medium transition-colors ${
            activeFilter === 'all'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          全部 ({typeCounts.all ?? 0})
        </button>
        {Object.entries(ELEMENT_TYPE_LABELS).map(([type, label]) => {
          const count = typeCounts[type] ?? 0
          if (count === 0) return null
          return (
            <button
              key={type}
              onClick={() => setActiveFilter(type as ElementType)}
              className={`px-2 py-0.5 rounded-full text-xs font-medium transition-colors ${
                activeFilter === type
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              {ELEMENT_TYPE_ICONS[type as ElementType]} {label} ({count})
            </button>
          )
        })}
      </div>

      {/* Element list */}
      <div
        className={`flex-1 overflow-y-auto space-y-2 pr-1 min-h-[200px] rounded-lg border p-2 ${
          isOver ? 'border-primary bg-primary/5' : 'border-border bg-background'
        }`}
      >
        {filtered.length === 0 ? (
          <EmptyState
            emoji="🧩"
            title={elements.length === 0 ? '元素库为空' : '暂无匹配元素'}
            description={
              elements.length === 0
                ? '暂无策略元素。可前往 Playground 从爆款分析提取，或联系管理员添加。'
                : '尝试更换筛选条件或搜索关键词'
            }
            className="py-6"
          />
        ) : (
          filtered.map((el) => {
            const isSelected = selectedIds.includes(el.element_id)
            return (
              <button
                key={el.element_id}
                onClick={() => !isSelected && onAdd(el.element_id)}
                disabled={isSelected}
                className={`w-full text-left rounded-lg border p-3 transition-all group ${
                  isSelected
                    ? 'opacity-50 border-border bg-muted cursor-not-allowed'
                    : 'border-border bg-card hover:border-primary/40 hover:shadow-sm cursor-pointer'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-base shrink-0">
                      {ELEMENT_TYPE_ICONS[el.element_type]}
                    </span>
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{el.name}</div>
                      {el.description && (
                        <div className="text-xs text-muted-foreground truncate">
                          {el.description}
                        </div>
                      )}
                    </div>
                  </div>
                  {!isSelected && (
                    <Plus className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0 mt-0.5" />
                  )}
                </div>
                <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                  <Badge variant="primary" className="text-[10px]">
                    {ELEMENT_TYPE_LABELS[el.element_type]}
                  </Badge>
                  {el.platform && (
                    <Badge variant="default" className="text-[10px]">
                      {el.platform}
                    </Badge>
                  )}
                  {el.effectiveness_score > 0 && (
                    <Badge variant="success" className="text-[10px]">
                      {el.effectiveness_score.toFixed(1)}
                    </Badge>
                  )}
                </div>
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}
