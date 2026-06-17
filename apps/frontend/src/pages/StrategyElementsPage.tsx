import { useEffect, useMemo, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAICopilotStore } from '../stores/aiCopilotStore'
import { useAuthStore } from '../stores/authStore'
import {
  useStrategyElements,
  useCreateStrategyElement,
  useUpdateStrategyElement,
  useDeleteStrategyElement,
} from '../hooks/useStrategyQueries'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge, type BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { showToast } from '../lib/toast'
import {
  ELEMENT_TYPE_LABELS,
  ELEMENT_TYPE_ICONS,
  type ElementType,
  type ElementSource,
  type ElementStatus,
  type StrategyElement,
} from '../types/strategy'
import {
  Search,
  Plus,
  LayoutGrid,
  List,
  Sparkles,
  X,
  Pencil,
  Trash2,
  ArrowRight,
  BookOpen,
  Filter,
  ShieldCheck,
} from 'lucide-react'

/* ── config ── */

const sources: { key: ElementSource | 'all'; label: string }[] = [
  { key: 'all', label: '全部来源' },
  { key: 'manual', label: '手动创建' },
  { key: 'viral_analyzer', label: '爆款分析' },
  { key: 'ai_generated', label: 'AI 生成' },
  { key: 'system', label: '系统' },
]

const statuses: { key: ElementStatus | 'all'; label: string; variant: BadgeVariant }[] = [
  { key: 'all', label: '全部状态', variant: 'default' },
  { key: 'active', label: '生效中', variant: 'success' },
  { key: 'deprecated', label: '已停用', variant: 'default' },
  { key: 'draft', label: '草稿', variant: 'warning' },
]

const platforms = [
  { key: 'xiaohongshu', label: '小红书' },
  { key: 'douyin', label: '抖音' },
  { key: 'wechat_channels', label: '视频号' },
]

const contentFormats = [
  { key: 'text', label: '图文' },
  { key: 'video', label: '视频' },
  { key: 'image', label: '图片' },
  { key: 'live', label: '直播' },
]

const elementTypeOptions = Object.entries(ELEMENT_TYPE_LABELS).map(([key, label]) => ({
  key: key as ElementType,
  label,
  icon: ELEMENT_TYPE_ICONS[key as ElementType],
}))

/* ── helpers ── */

function safeJsonParse(text: string): Record<string, unknown> {
  try {
    return JSON.parse(text) as Record<string, unknown>
  } catch {
    return {}
  }
}

function safeJsonStringify(value: Record<string, unknown>): string {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return '{}'
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('zh-CN')
  } catch {
    return iso
  }
}

/* ── safety constraint editor ── */

interface SafetyConstraintContent {
  rule_source?: string
  rule_reference_ids?: string[]
  forbidden_terms?: string[]
  required_disclaimers?: string[]
  action?: 'block' | 'warn' | 'suggest'
  platforms?: string[]
  content_formats?: string[]
}

const SAFETY_ACTIONS: { value: SafetyConstraintContent['action']; label: string }[] = [
  { value: 'block', label: '拦截' },
  { value: 'warn', label: '警告' },
  { value: 'suggest', label: '建议' },
]

function SafetyConstraintEditor({
  value,
  onChange,
}: {
  value: SafetyConstraintContent
  onChange: (v: SafetyConstraintContent) => void
}) {
  const update = (patch: Partial<SafetyConstraintContent>) => onChange({ ...value, ...patch })
  const listToText = (arr?: string[]) => (arr || []).join('\n')
  const textToList = (text: string) => text.split('\n').map((s) => s.trim()).filter(Boolean)

  return (
    <div className="space-y-3 rounded-lg border border-border p-3">
      <div className="flex items-center gap-2 text-sm font-medium">
        <ShieldCheck className="w-4 h-4 text-primary" />
        内容安全约束配置
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">规则来源</label>
          <select
            value={value.rule_source || 'ad_law'}
            onChange={(e) => update({ rule_source: e.target.value })}
            className="w-full h-9 px-2 rounded-md border border-border bg-background text-sm"
          >
            <option value="ad_law">广告法</option>
            <option value="platform_rule">平台规则</option>
            <option value="vetdrug">兽药规范</option>
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">触发动作</label>
          <select
            value={value.action || 'warn'}
            onChange={(e) => update({ action: e.target.value as SafetyConstraintContent['action'] })}
            className="w-full h-9 px-2 rounded-md border border-border bg-background text-sm"
          >
            {SAFETY_ACTIONS.map((a) => (
              <option key={a.value} value={a.value}>{a.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">引用规则 ID（每行一个）</label>
        <textarea
          value={listToText(value.rule_reference_ids)}
          onChange={(e) => update({ rule_reference_ids: textToList(e.target.value) })}
          rows={2}
          placeholder="如 vetdrug-001&#10;rule-l1-002"
          className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm resize-y font-mono"
        />
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">禁用词 / 敏感词（每行一个）</label>
        <textarea
          value={listToText(value.forbidden_terms)}
          onChange={(e) => update({ forbidden_terms: textToList(e.target.value) })}
          rows={3}
          placeholder="如 处方药&#10;治愈率100%"
          className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm resize-y"
        />
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">必须声明（每行一个）</label>
        <textarea
          value={listToText(value.required_disclaimers)}
          onChange={(e) => update({ required_disclaimers: textToList(e.target.value) })}
          rows={2}
          placeholder="如 本品不能替代药品"
          className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm resize-y"
        />
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">适用平台（每行一个，留空表示全部）</label>
        <textarea
          value={listToText(value.platforms)}
          onChange={(e) => update({ platforms: textToList(e.target.value) })}
          rows={2}
          placeholder="xiaohongshu&#10;douyin"
          className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm resize-y font-mono"
        />
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-muted-foreground">适用内容格式（每行一个，留空表示全部）</label>
        <textarea
          value={listToText(value.content_formats)}
          onChange={(e) => update({ content_formats: textToList(e.target.value) })}
          rows={2}
          placeholder="图文&#10;视频"
          className="w-full px-3 py-2 rounded-md border border-border bg-background text-sm resize-y"
        />
      </div>
    </div>
  )
}

/* ── form component ── */

interface ElementFormProps {
  element?: StrategyElement | null
  onSubmit: (data: Partial<StrategyElement>) => void
  onCancel: () => void
  isSubmitting: boolean
}

function ElementForm({ element, onSubmit, onCancel, isSubmitting }: ElementFormProps) {
  const isCreate = !element
  const [name, setName] = useState(element?.name ?? '')
  const [elementType, setElementType] = useState<ElementType>(element?.element_type ?? 'keyword_strategy')
  const [source, setSource] = useState<ElementSource>(element?.source ?? 'manual')
  const [status, setStatus] = useState<ElementStatus>(element?.status ?? 'draft')
  const [platform, setPlatform] = useState(element?.platform ?? '')
  const [contentFormat, setContentFormat] = useState(element?.content_format ?? '')
  const [description, setDescription] = useState(element?.description ?? '')
  const [renderTemplate, setRenderTemplate] = useState(element?.render_template ?? '')
  const [contentText, setContentText] = useState(safeJsonStringify(element?.content ?? {}))
  const [safetyContent, setSafetyContent] = useState<SafetyConstraintContent>(
    (element?.content as SafetyConstraintContent) ?? {}
  )
  const isSafetyConstraint = elementType === 'safety_constraint'

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      showToast.error('请输入元素名称')
      return
    }
    const content = isSafetyConstraint
      ? { ...safetyContent, _type: 'safety_constraint' }
      : safeJsonParse(contentText)
    onSubmit({
      name: name.trim(),
      element_type: elementType,
      source,
      status,
      platform: platform || null,
      content_format: contentFormat || null,
      description: description || null,
      render_template: renderTemplate,
      content,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1">
        <label className="text-sm font-medium">名称</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="策略元素名称"
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:border-primary"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-sm font-medium">类型</label>
          <select
            value={elementType}
            onChange={(e) => setElementType(e.target.value as ElementType)}
            disabled={!isCreate}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm disabled:opacity-60"
          >
            {elementTypeOptions.map((t) => (
              <option key={t.key} value={t.key}>
                {t.icon} {t.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium">来源</label>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value as ElementSource)}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
          >
            {sources.filter((s) => s.key !== 'all').map((s) => (
              <option key={s.key} value={s.key}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-sm font-medium">状态</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as ElementStatus)}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
          >
            {statuses.filter((s) => s.key !== 'all').map((s) => (
              <option key={s.key} value={s.key}>{s.label}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium">平台</label>
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
          >
            <option value="">不限</option>
            {platforms.map((p) => (
              <option key={p.key} value={p.key}>{p.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium">内容格式</label>
        <select
          value={contentFormat}
          onChange={(e) => setContentFormat(e.target.value)}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
        >
          <option value="">不限</option>
          {contentFormats.map((f) => (
            <option key={f.key} value={f.key}>{f.label}</option>
          ))}
        </select>
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium">描述</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="描述该策略元素的用途和场景"
          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-y"
        />
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium">渲染模板</label>
        <textarea
          value={renderTemplate}
          onChange={(e) => setRenderTemplate(e.target.value)}
          rows={3}
          placeholder="例如：{{content}}"
          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-y font-mono"
        />
      </div>

      {isSafetyConstraint ? (
        <div className="space-y-1">
          <label className="text-sm font-medium">内容</label>
          <SafetyConstraintEditor value={safetyContent} onChange={setSafetyContent} />
        </div>
      ) : (
        <div className="space-y-1">
          <label className="text-sm font-medium">内容（JSON）</label>
          <textarea
            value={contentText}
            onChange={(e) => setContentText(e.target.value)}
            rows={6}
            placeholder='{"text": "...", "hook": "..."}'
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-y font-mono"
          />
        </div>
      )}

      <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={isSubmitting}>
          取消
        </Button>
        <Button type="submit" isLoading={isSubmitting}>
          {isCreate ? '创建' : '保存'}
        </Button>
      </div>
    </form>
  )
}

/* ── detail aside ── */

interface DetailAsideProps {
  element: StrategyElement
  onClose: () => void
  onEdit: () => void
  onApply: () => void
  onDelete: () => void
}

function DetailAside({ element, onClose, onEdit, onApply, onDelete }: DetailAsideProps) {
  return (
    <aside className="w-80 xl:w-96 flex-shrink-0 border-l border-border bg-card shadow-xl flex flex-col sticky top-0 max-h-full overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border">
        <h3 className="text-base font-semibold">策略元素详情</h3>
        <button
          type="button"
          onClick={onClose}
          className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          aria-label="关闭"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{ELEMENT_TYPE_ICONS[element.element_type]}</span>
            <h4 className="text-lg font-semibold break-words">{element.name}</h4>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="primary">{ELEMENT_TYPE_LABELS[element.element_type]}</Badge>
            <Badge variant={element.status === 'active' ? 'success' : element.status === 'draft' ? 'warning' : 'default'}>
              {statuses.find((s) => s.key === element.status)?.label ?? element.status}
            </Badge>
            <Badge variant="info">
              {sources.find((s) => s.key === element.source)?.label ?? element.source}
            </Badge>
          </div>
        </div>

        {element.description && (
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">描述</label>
            <p className="text-sm text-foreground break-words">{element.description}</p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <label className="text-xs font-medium text-muted-foreground">平台</label>
            <p>{element.platform ?? '不限'}</p>
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">内容格式</label>
            <p>{element.content_format ?? '不限'}</p>
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">使用次数</label>
            <p>{element.usage_count}</p>
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">效果分</label>
            <p>{Number(element.effectiveness_score ?? 0).toFixed(2)}</p>
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">创建时间</label>
            <p>{formatDate(element.created_at)}</p>
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">更新时间</label>
            <p>{formatDate(element.updated_at)}</p>
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">渲染模板</label>
          <pre className="text-xs bg-muted p-2 rounded-lg overflow-x-auto whitespace-pre-wrap break-words font-mono">
            {element.render_template}
          </pre>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">内容</label>
          <pre className="text-xs bg-muted p-2 rounded-lg overflow-x-auto whitespace-pre-wrap break-words font-mono">
            {safeJsonStringify(element.content)}
          </pre>
        </div>
      </div>
      <div className="border-t border-border p-4 flex flex-wrap gap-2">
        <Button size="sm" onClick={onApply}>
          <ArrowRight className="w-4 h-4 mr-1" />
          应用到任务
        </Button>
        <Button size="sm" variant="secondary" onClick={onEdit}>
          <Pencil className="w-4 h-4 mr-1" />
          编辑
        </Button>
        <Button size="sm" variant="ghost" className="text-destructive hover:text-destructive" onClick={onDelete}>
          <Trash2 className="w-4 h-4 mr-1" />
          删除
        </Button>
      </div>
    </aside>
  )
}

/* ── main page ── */

export function StrategyElementsPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { setPageActionCards, setPageActionHandler } = useAICopilotStore()

  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<ElementType | 'all'>('all')
  const [sourceFilter, setSourceFilter] = useState<ElementSource | 'all'>('all')
  const [statusFilter, setStatusFilter] = useState<ElementStatus | 'all'>('all')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [formMode, setFormMode] = useState<'closed' | 'create' | 'edit'>('closed')

  const { data: elements = [], isLoading } = useStrategyElements(
    { limit: 200 },
    { staleTime: 5 * 60 * 1000 }
  )
  const createMut = useCreateStrategyElement()
  const updateMut = useUpdateStrategyElement()
  const deleteMut = useDeleteStrategyElement()

  const selectedElement = useMemo(
    () => elements.find((e) => e.element_id === selectedId) ?? null,
    [elements, selectedId]
  )

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return elements.filter((el) => {
      if (typeFilter !== 'all' && el.element_type !== typeFilter) return false
      if (sourceFilter !== 'all' && el.source !== sourceFilter) return false
      if (statusFilter !== 'all' && el.status !== statusFilter) return false
      if (q) {
        const text = `${el.name} ${el.element_type} ${el.description ?? ''}`.toLowerCase()
        if (!text.includes(q)) return false
      }
      return true
    })
  }, [elements, typeFilter, sourceFilter, statusFilter, search])

  const stats = useMemo(() => {
    const total = elements.length
    const active = elements.filter((e) => e.status === 'active').length
    const fromViral = elements.filter((e) => e.source === 'viral_analyzer').length
    const fromAi = elements.filter((e) => e.source === 'ai_generated').length
    return { total, active, fromViral, fromAi }
  }, [elements])

  const handleCreate = useCallback(() => {
    setSelectedId(null)
    setFormMode('create')
  }, [])

  const handleEdit = useCallback(() => {
    setFormMode('edit')
  }, [])

  const handleCloseAside = useCallback(() => {
    setSelectedId(null)
    setFormMode('closed')
  }, [])

  const handleApply = useCallback(() => {
    if (!selectedElement) return
    navigate(`/generate/create?strategyElementId=${selectedElement.element_id}`)
  }, [navigate, selectedElement])

  const handleDelete = useCallback(async () => {
    if (!selectedElement) return
    if (!window.confirm(`确认删除策略元素「${selectedElement.name}」？`)) return
    try {
      await deleteMut.mutateAsync(selectedElement.element_id)
      showToast.success('删除成功')
      handleCloseAside()
    } catch {
      showToast.error('删除失败')
    }
  }, [selectedElement, deleteMut, handleCloseAside])

  const handleFormSubmit = useCallback(
    async (data: Partial<StrategyElement>) => {
      try {
        if (formMode === 'create') {
          await createMut.mutateAsync({
            ...data,
            created_by: user?.id ?? 'system',
            usage_count: 0,
            effectiveness_score: 0,
            avg_engagement: {},
            variables: [],
          })
          showToast.success('创建成功')
        } else if (selectedElement) {
          await updateMut.mutateAsync({ elementId: selectedElement.element_id, data })
          showToast.success('保存成功')
        }
        setFormMode('closed')
        setSelectedId(null)
      } catch {
        showToast.error(formMode === 'create' ? '创建失败' : '保存失败')
      }
    },
    [formMode, selectedElement, createMut, updateMut, user]
  )

  // Copilot Action Cards
  useEffect(() => {
    const cards = [
      {
        id: 'strategy-elements-create',
        type: 'generation' as const,
        title: '➕ 创建策略元素',
        description: '在策略元素库中新增一个手动创建的策略元素',
        priority: 1,
        actions: [{ id: 'create_element', label: '开始创建', variant: 'primary' as const }],
      },
      {
        id: 'strategy-elements-analyze',
        type: 'suggestion' as const,
        title: '🧪 爆款分析提取',
        description: '前往实验室分析爆款笔记并自动提取策略元素',
        priority: 2,
        actions: [{ id: 'go_lab', label: '去实验室', variant: 'secondary' as const }],
      },
      {
        id: 'strategy-elements-apply',
        type: 'suggestion' as const,
        title: '🚀 应用到任务',
        description: selectedElement
          ? `将「${selectedElement.name}」带入 TaskHub 创建流程`
          : '请先在页面中选择一个策略元素',
        priority: 3,
        actions: selectedElement
          ? [{ id: 'apply_to_task', label: '应用', variant: 'primary' as const }]
          : [],
      },
    ]
    setPageActionCards(cards)

    setPageActionHandler(async (cardId, actionId) => {
      if (cardId === 'strategy-elements-create' && actionId === 'create_element') {
        handleCreate()
      } else if (cardId === 'strategy-elements-analyze' && actionId === 'go_lab') {
        navigate('/lab')
      } else if (cardId === 'strategy-elements-apply' && actionId === 'apply_to_task') {
        handleApply()
      }
    })

    return () => {
      setPageActionCards([])
      setPageActionHandler(null)
    }
  }, [handleCreate, handleApply, navigate, selectedElement, setPageActionCards, setPageActionHandler])

  const isAsideOpen = formMode !== 'closed' || selectedId !== null

  return (
    <div className="flex gap-6 min-h-0">
      <div className="flex-1 min-w-0 space-y-5">
        <PageHeader
          title="策略元素"
          subtitle="关键词库 + 模板库合并 · 统一策略元素管理"
          action={
            <Button onClick={handleCreate}>
              <Plus className="w-4 h-4 mr-1" />
              创建元素
            </Button>
          }
        />

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="min-w-0 overflow-hidden">
            <CardContent className="p-4" data-testid="stat-total">
              <p className="text-xs text-muted-foreground">全部元素</p>
              <p className="text-2xl font-semibold mt-1">{stats.total}</p>
            </CardContent>
          </Card>
          <Card className="min-w-0 overflow-hidden">
            <CardContent className="p-4" data-testid="stat-active">
              <p className="text-xs text-muted-foreground">生效中</p>
              <p className="text-2xl font-semibold mt-1">{stats.active}</p>
            </CardContent>
          </Card>
          <Card className="min-w-0 overflow-hidden">
            <CardContent className="p-4" data-testid="stat-viral">
              <p className="text-xs text-muted-foreground">爆款分析来源</p>
              <p className="text-2xl font-semibold mt-1">{stats.fromViral}</p>
            </CardContent>
          </Card>
          <Card className="min-w-0 overflow-hidden">
            <CardContent className="p-4" data-testid="stat-ai">
              <p className="text-xs text-muted-foreground">AI 生成来源</p>
              <p className="text-2xl font-semibold mt-1">{stats.fromAi}</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card className="min-w-0 overflow-hidden">
          <CardContent className="p-4">
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative flex-1 min-w-[200px] max-w-sm">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="搜索名称、描述、类型..."
                    className="w-full h-9 pl-9 pr-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-muted-foreground" />
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value as ElementType | 'all')}
                    className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:border-primary"
                  >
                    <option value="all">全部类型</option>
                    {elementTypeOptions.map((t) => (
                      <option key={t.key} value={t.key}>{t.icon} {t.label}</option>
                    ))}
                  </select>
                  <select
                    value={sourceFilter}
                    onChange={(e) => setSourceFilter(e.target.value as ElementSource | 'all')}
                    className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:border-primary"
                  >
                    {sources.map((s) => (
                      <option key={s.key} value={s.key}>{s.label}</option>
                    ))}
                  </select>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as ElementStatus | 'all')}
                    className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:border-primary"
                  >
                    {statuses.map((s) => (
                      <option key={s.key} value={s.key}>{s.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  共 {filtered.length} 个元素
                </p>
                <div className="flex items-center gap-1 border border-border rounded-lg p-1">
                  <button
                    type="button"
                    onClick={() => setViewMode('grid')}
                    className={`p-1.5 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                    aria-label="网格视图"
                  >
                    <LayoutGrid className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('list')}
                    className={`p-1.5 rounded-md transition-colors ${viewMode === 'list' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                    aria-label="列表视图"
                  >
                    <List className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Content */}
        <Card className="min-w-0 overflow-hidden flex-1">
          <CardHeader className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-primary" />
            <h2 className="text-base font-semibold">策略元素库</h2>
            <Badge variant="default">{filtered.length}</Badge>
          </CardHeader>
          <CardContent>
            {isLoading && <div className="h-48 animate-pulse bg-secondary/50 rounded-lg" />}
            {!isLoading && filtered.length === 0 && (
              <EmptyState
                icon={Sparkles}
                title="暂无策略元素"
                description="当前过滤条件下没有策略元素，尝试调整筛选条件或创建新元素"
                action={
                  <Button onClick={handleCreate}>
                    <Plus className="w-4 h-4 mr-1" />
                    创建元素
                  </Button>
                }
              />
            )}
            {!isLoading && filtered.length > 0 && viewMode === 'grid' && (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {filtered.map((el) => (
                  <button
                    key={el.element_id}
                    type="button"
                    onClick={() => { setSelectedId(el.element_id); setFormMode('closed') }}
                    className={`text-left p-4 rounded-xl border transition-all hover:shadow-md ${selectedId === el.element_id ? 'border-primary bg-primary/5' : 'border-border bg-card hover:border-primary/30'}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-xl flex-shrink-0">{ELEMENT_TYPE_ICONS[el.element_type]}</span>
                        <h3 className="font-medium text-sm truncate">{el.name}</h3>
                      </div>
                      <Badge
                        variant={el.status === 'active' ? 'success' : el.status === 'draft' ? 'warning' : 'default'}
                        className="flex-shrink-0"
                      >
                        {statuses.find((s) => s.key === el.status)?.label ?? el.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                      {el.description || '暂无描述'}
                    </p>
                    <div className="flex items-center gap-2 mt-3 flex-wrap">
                      <Badge variant="primary">{ELEMENT_TYPE_LABELS[el.element_type]}</Badge>
                      <Badge variant="info">
                        {sources.find((s) => s.key === el.source)?.label ?? el.source}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground ml-auto">
                        使用 {el.usage_count}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
            {!isLoading && filtered.length > 0 && viewMode === 'list' && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="py-3 pr-4 font-medium">元素</th>
                      <th className="py-3 pr-4 font-medium">类型</th>
                      <th className="py-3 pr-4 font-medium">来源</th>
                      <th className="py-3 pr-4 font-medium">状态</th>
                      <th className="py-3 pr-4 font-medium">平台</th>
                      <th className="py-3 pr-4 font-medium">使用</th>
                      <th className="py-3 font-medium">效果分</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((el) => (
                      <tr
                        key={el.element_id}
                        onClick={() => { setSelectedId(el.element_id); setFormMode('closed') }}
                        className={`border-b border-border cursor-pointer transition-colors ${selectedId === el.element_id ? 'bg-primary/5' : 'hover:bg-muted/50'}`}
                      >
                        <td className="py-3 pr-4">
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="text-lg">{ELEMENT_TYPE_ICONS[el.element_type]}</span>
                            <div className="min-w-0">
                              <p className="font-medium truncate">{el.name}</p>
                              <p className="text-xs text-muted-foreground truncate">{el.description || '—'}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 pr-4 whitespace-nowrap">{ELEMENT_TYPE_LABELS[el.element_type]}</td>
                        <td className="py-3 pr-4 whitespace-nowrap">
                          {sources.find((s) => s.key === el.source)?.label ?? el.source}
                        </td>
                        <td className="py-3 pr-4">
                          <Badge variant={el.status === 'active' ? 'success' : el.status === 'draft' ? 'warning' : 'default'}>
                            {statuses.find((s) => s.key === el.status)?.label ?? el.status}
                          </Badge>
                        </td>
                        <td className="py-3 pr-4 whitespace-nowrap">{el.platform ?? '—'}</td>
                        <td className="py-3 pr-4 whitespace-nowrap">{el.usage_count}</td>
                        <td className="py-3 whitespace-nowrap">{Number(el.effectiveness_score ?? 0).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Aside: detail / form */}
      {isAsideOpen && (
        formMode === 'create' ? (
          <aside className="w-80 xl:w-96 flex-shrink-0 border-l border-border bg-card shadow-xl flex flex-col sticky top-0 max-h-full overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h3 className="text-base font-semibold">创建策略元素</h3>
              <button
                type="button"
                onClick={handleCloseAside}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                aria-label="关闭"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-5">
              <ElementForm
                onSubmit={handleFormSubmit}
                onCancel={handleCloseAside}
                isSubmitting={createMut.isPending || updateMut.isPending}
              />
            </div>
          </aside>
        ) : formMode === 'edit' && selectedElement ? (
          <aside className="w-80 xl:w-96 flex-shrink-0 border-l border-border bg-card shadow-xl flex flex-col sticky top-0 max-h-full overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h3 className="text-base font-semibold">编辑策略元素</h3>
              <button
                type="button"
                onClick={() => setFormMode('closed')}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                aria-label="关闭"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-5">
              <ElementForm
                element={selectedElement}
                onSubmit={handleFormSubmit}
                onCancel={() => setFormMode('closed')}
                isSubmitting={createMut.isPending || updateMut.isPending}
              />
            </div>
          </aside>
        ) : selectedElement ? (
          <DetailAside
            element={selectedElement}
            onClose={handleCloseAside}
            onEdit={handleEdit}
            onApply={handleApply}
            onDelete={handleDelete}
          />
        ) : null
      )}
    </div>
  )
}
