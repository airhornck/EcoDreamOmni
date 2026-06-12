import { useEffect, useMemo, useState } from 'react'
import { usePersonaPoolStore } from '../stores/personaPoolStore'
import { usePersonaStoryStore, type PersonaStory, type StoryNode } from '../stores/personaStoryStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { AlertBanner } from '../components/ui/AlertBanner'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import {
  UserCircle,
  BookOpen,
  Plus,
  Trash2,
  Copy,
  Archive,
  Play,
  ChevronRight,
  ChevronLeft,
  Save,
  X,
  Activity,
  AlertTriangle,
  Users,
  FileText,
} from 'lucide-react'

const EMOTION_CURVE_LABELS: Record<PersonaStory['emotion_curve_template'], string> = {
  gradual_growth: '渐进成长',
  valley_comeback: '低谷逆袭',
  suspense_reveal: '悬疑揭秘',
  steady_warm: '平稳温暖',
}

const EMOTION_CURVE_COLORS: Record<PersonaStory['emotion_curve_template'], string> = {
  gradual_growth: '#22c55e',
  valley_comeback: '#3b82f6',
  suspense_reveal: '#a855f7',
  steady_warm: '#f97316',
}

const STATUS_LABELS: Record<PersonaStory['status'], string> = {
  draft: '草稿',
  active: '活跃',
  completed: '已完成',
  archived: '已归档',
}

const STATUS_VARIANTS: Record<PersonaStory['status'], import('../components/ui/Badge').BadgeVariant> = {
  draft: 'default',
  active: 'primary',
  completed: 'success',
  archived: 'warning',
}

const EMOTION_VALUES: Record<StoryNode['emotion_tone'], number> = {
  low: 1,
  medium: 2,
  high: 3,
  burst: 4,
}

interface ConflictWarning {
  id: string
  type: 'duplicate_theme' | 'emotion_jump'
  title: string
  description: string
  nodeIndex: number
}

function detectConflicts(sortedNodes: StoryNode[]): ConflictWarning[] {
  const warnings: ConflictWarning[] = []
  for (let i = 0; i < sortedNodes.length - 1; i++) {
    const current = sortedNodes[i]
    const next = sortedNodes[i + 1]
    const themeA = current.theme?.trim().toLowerCase() || ''
    const themeB = next.theme?.trim().toLowerCase() || ''

    if (themeA && themeB && (themeA.includes(themeB) || themeB.includes(themeA))) {
      warnings.push({
        id: `duplicate-theme-${i}`,
        type: 'duplicate_theme',
        title: '相邻节点主题重复',
        description: `节点 ${i + 1}「${current.theme}」与节点 ${i + 2}「${next.theme}」主题相似，建议调整`,
        nodeIndex: i,
      })
    }

    const diff = Math.abs(EMOTION_VALUES[current.emotion_tone] - EMOTION_VALUES[next.emotion_tone])
    if (diff >= 2) {
      warnings.push({
        id: `emotion-jump-${i}`,
        type: 'emotion_jump',
        title: '情感跳跃过大',
        description: `节点 ${i + 1}（${current.emotion_tone}）→ 节点 ${i + 2}（${next.emotion_tone}）情感差值为 ${diff}，建议增加过渡节点`,
        nodeIndex: i,
      })
    }
  }
  return warnings
}

export function PersonasPage() {
  const {
    personas,
    isLoading: personaLoading,
    error: personaError,
    fetchPersonas,
    createPersona,
    deletePersona,
  } = usePersonaPoolStore()

  const {
    stories,
    nodes,
    isLoading: storyLoading,
    error: storyError,
    fetchStories,
    createStory,
    updateStory,
    deleteStory,
    cloneStory,
    updateStoryStatus,
    fetchNodes,
    createNode,
    updateNode,
    deleteNode,
    reorderNodes,
    clearError: clearStoryError,
  } = usePersonaStoryStore()

  const [activeTab, setActiveTab] = useState<'personas' | 'stories'>('personas')

  // Persona create form (existing)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [voiceStyle, setVoiceStyle] = useState('')

  // Story filters
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [personaFilter, setPersonaFilter] = useState<string>('')

  // Story form
  const [showStoryForm, setShowStoryForm] = useState(false)
  const [editingStory, setEditingStory] = useState<PersonaStory | null>(null)
  const [storyForm, setStoryForm] = useState<Partial<PersonaStory>>({
    name: '',
    description: '',
    persona_id: '',
    emotion_curve_template: 'gradual_growth',
    status: 'draft',
  })
  const [storyFormError, setStoryFormError] = useState<string | null>(null)

  // Node form
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [nodeForm, setNodeForm] = useState<Partial<StoryNode>>({
    theme: '',
    emotion_tone: 'medium',
    key_event: '',
    prev_recap: '',
    next_teaser: '',
  })

  // Dismissed warnings
  const [dismissedWarnings, setDismissedWarnings] = useState<Set<string>>(new Set())

  const isLoading = personaLoading || storyLoading
  const error = personaError || storyError

  useEffect(() => {
    fetchPersonas()
  }, [fetchPersonas])

  useEffect(() => {
    if (activeTab === 'stories') {
      fetchStories(personaFilter || undefined, statusFilter || undefined)
    }
  }, [activeTab, personaFilter, statusFilter, fetchStories])

  // Persona handlers
  const handleCreatePersona = async () => {
    if (!name.trim()) return
    const success = await createPersona({ name, voice_style: voiceStyle, target_platforms: ['xhs'] })
    if (success) {
      setShowCreate(false)
      setName('')
      setVoiceStyle('')
    }
  }

  // Story handlers
  const handleCreateStory = async () => {
    setStoryFormError(null)
    if (!storyForm.name?.trim()) {
      setStoryFormError('请输入剧本名称')
      return
    }
    if (!storyForm.persona_id) {
      setStoryFormError('请选择关联人设')
      return
    }
    // 只发送后端需要的字段，避免潜在兼容性问题
    const payload = {
      name: storyForm.name.trim(),
      description: storyForm.description || undefined,
      persona_id: storyForm.persona_id,
      emotion_curve_template: storyForm.emotion_curve_template || 'gradual_growth',
    }
    const story = await createStory(payload)
    if (story) {
      setShowStoryForm(false)
      resetStoryForm()
      setStoryFormError(null)
      // 自动打开新创建的剧本进行编辑
      await openStoryEditor(story)
    }
  }

  const handleUpdateStory = async () => {
    if (!editingStory) return
    const success = await updateStory(editingStory.id, storyForm)
    if (success) {
      // 更新本地 editingStory 状态以反映最新保存的内容，保持编辑器打开
      setEditingStory((prev) =>
        prev
          ? {
              ...prev,
              name: storyForm.name ?? prev.name,
              description: storyForm.description ?? prev.description,
              persona_id: storyForm.persona_id ?? prev.persona_id,
              emotion_curve_template: storyForm.emotion_curve_template ?? prev.emotion_curve_template,
              status: storyForm.status ?? prev.status,
            }
          : null
      )
    }
  }

  const handleSaveStoryMeta = async () => {
    if (editingStory) {
      await handleUpdateStory()
    } else {
      await handleCreateStory()
    }
  }

  const resetStoryForm = () => {
    setStoryForm({
      name: '',
      description: '',
      persona_id: '',
      emotion_curve_template: 'gradual_growth',
      status: 'draft',
    })
  }

  const openStoryEditor = async (story: PersonaStory) => {
    setEditingStory(story)
    setStoryForm({
      name: story.name,
      description: story.description ?? '',
      persona_id: story.persona_id,
      emotion_curve_template: story.emotion_curve_template,
      status: story.status,
    })
    try {
      await fetchNodes(story.id)
    } catch {
      // fetchNodes 内部已捕获错误并设置 store error，此处不再抛出
    }
    setSelectedNodeId(null)
    resetNodeForm()
    setDismissedWarnings(new Set())
  }

  const resetNodeForm = () => {
    setNodeForm({ theme: '', emotion_tone: 'medium', key_event: '', prev_recap: '', next_teaser: '' })
  }

  const handleCreateNode = async () => {
    if (!editingStory) return
    const nextIndex = nodes.length
    const success = await createNode(editingStory.id, { ...nodeForm, sequence_index: nextIndex })
    if (success) {
      resetNodeForm()
    }
  }

  const handleUpdateNode = async () => {
    if (!selectedNodeId) return
    const success = await updateNode(selectedNodeId, nodeForm)
    if (success) {
      setSelectedNodeId(null)
      resetNodeForm()
    }
  }

  const selectNode = (node: StoryNode) => {
    setSelectedNodeId(node.id)
    setNodeForm({
      theme: node.theme,
      emotion_tone: node.emotion_tone,
      key_event: node.key_event,
      prev_recap: node.prev_recap,
      next_teaser: node.next_teaser,
    })
  }

  const personaNameMap = new Map(personas.map((p) => [p.id, p.name]))

  const sortedNodes = useMemo(() => {
    return [...nodes].sort((a, b) => a.sequence_index - b.sequence_index)
  }, [nodes])

  const handleMoveNode = async (index: number, direction: 'left' | 'right') => {
    if (!editingStory) return
    const newOrder = sortedNodes.map((n) => n.id)
    if (direction === 'left' && index > 0) {
      ;[newOrder[index], newOrder[index - 1]] = [newOrder[index - 1], newOrder[index]]
    } else if (direction === 'right' && index < newOrder.length - 1) {
      ;[newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]]
    } else {
      return
    }
    await reorderNodes(editingStory.id, newOrder)
  }

  const emotionChartData = useMemo(() => {
    return sortedNodes.map((node, idx) => ({
      index: idx + 1,
      theme: node.theme,
      emotion: EMOTION_VALUES[node.emotion_tone],
      emotionLabel: node.emotion_tone,
    }))
  }, [sortedNodes])

  const conflicts = useMemo(() => {
    if (!editingStory) return []
    return detectConflicts(sortedNodes).filter((w) => !dismissedWarnings.has(w.id))
  }, [sortedNodes, editingStory, dismissedWarnings])

  const dismissWarning = (id: string) => {
    setDismissedWarnings((prev) => new Set(prev).add(id))
  }

  // Persona stats helpers
  const getPersonaStoryCount = (personaId: string) => stories.filter((s) => s.persona_id === personaId).length
  const isPersonaActive = (personaId: string) =>
    stories.some((s) => s.persona_id === personaId && s.status === 'active')

  return (
    <div className="space-y-6">
      <PageHeader
        title="人设池"
        subtitle="管理内容生成用的人设与故事剧本"
        action={
          activeTab === 'personas' ? (
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="w-4 h-4" />
              新建人设
            </Button>
          ) : (
            <Button
              onClick={() => {
                setShowStoryForm(true)
                setEditingStory(null)
                resetStoryForm()
              }}
            >
              <Plus className="w-4 h-4" />
              新建剧本
            </Button>
          )
        }
      />

      {error && (
        <AlertBanner
          variant="danger"
          title="错误"
          description={error}
          onDismiss={() => {
            clearStoryError()
          }}
        />
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border">
        <button
          onClick={() => setActiveTab('personas')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'personas'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <UserCircle className="w-4 h-4" />
          人设列表
        </button>
        <button
          onClick={() => setActiveTab('stories')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'stories'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          故事剧本
        </button>
      </div>

      {isLoading && activeTab === 'stories' && (
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">加载中...</p>
        </div>
      )}

      {/* Personas Tab */}
      {activeTab === 'personas' && (
        <div className="space-y-4">
          {showCreate && (
            <Card>
              <CardHeader>
                <h3 className="text-base font-semibold">新建人设</h3>
              </CardHeader>
              <CardContent className="space-y-3">
                <input
                  type="text"
                  placeholder="人设名称"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                />
                <textarea
                  placeholder="Voice风格描述..."
                  value={voiceStyle}
                  onChange={(e) => setVoiceStyle(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
                />
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => setShowCreate(false)}>
                    取消
                  </Button>
                  <Button onClick={handleCreatePersona}>创建</Button>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="flex items-center gap-2">
              <UserCircle className="w-4 h-4 text-primary" />
              <h2 className="text-base font-semibold">人设列表</h2>
            </CardHeader>
            <CardContent>
              {personaLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
              {!personaLoading && personas.length === 0 && (
                <EmptyState icon={UserCircle} title="暂无人设" description="创建你的第一个人设角色" />
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {personas.map((persona) => (
                  <div
                    key={persona.id}
                    className="p-4 rounded-lg border border-border hover:border-primary/30 transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-medium text-foreground">{persona.name}</h3>
                          {isPersonaActive(persona.id) && (
                            <span className="relative flex h-2.5 w-2.5">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-success/150" />
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{persona.voice_style}</p>
                        <div className="flex items-center gap-3 mt-2">
                          <div className="flex gap-1">
                            {persona.target_platforms?.map((p) => (
                              <Badge key={p} variant="default">
                                {p}
                              </Badge>
                            ))}
                          </div>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Users className="w-3 h-3" />
                            <span>{persona.target_platforms?.length || 0} 账号</span>
                          </div>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <FileText className="w-3 h-3" />
                            <span>{getPersonaStoryCount(persona.id)} 剧本</span>
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => deletePersona(persona.id)}
                        className="p-1.5 hover:bg-destructive/10 rounded"
                      >
                        <Trash2 className="w-4 h-4 text-destructive" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Stories Tab */}
      {activeTab === 'stories' && !storyLoading && (
        <div className="flex gap-4 h-[calc(100vh-260px)] min-h-[480px]">
          {/* Left: Story List */}
          <div className="w-80 flex-shrink-0 flex flex-col gap-3 overflow-hidden">
            {/* Filters */}
            <div className="flex flex-wrap items-center gap-2">
              <select
                className="h-9 px-2 rounded-lg border border-border bg-background text-sm"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">全部状态</option>
                <option value="draft">草稿</option>
                <option value="active">活跃</option>
                <option value="completed">已完成</option>
                <option value="archived">已归档</option>
              </select>
              <select
                className="h-9 px-2 rounded-lg border border-border bg-background text-sm"
                value={personaFilter}
                onChange={(e) => setPersonaFilter(e.target.value)}
              >
                <option value="">全部人设</option>
                {personas.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            {/* Story List */}
            <div className="flex-1 overflow-y-auto pr-1 space-y-2">
              {stories.length === 0 ? (
                <EmptyState icon={BookOpen} title="暂无剧本" description="创建你的第一个故事剧本" />
              ) : (
                stories.map((story) => (
                  <div
                    key={story.id}
                    onClick={() => openStoryEditor(story)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      editingStory?.id === story.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/30'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <h3 className="text-sm font-medium text-foreground truncate pr-2">{story.name}</h3>
                      <Badge variant={STATUS_VARIANTS[story.status]}>{STATUS_LABELS[story.status]}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{story.description}</p>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground mb-2">
                      <span>{personaNameMap.get(story.persona_id) ?? '未知人设'}</span>
                      <span>·</span>
                      <span>{story.nodes_count ?? 0}节点</span>
                      <span>·</span>
                      <span>{EMOTION_CURVE_LABELS[story.emotion_curve_template]}</span>
                    </div>
                    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 px-1.5"
                        onClick={async () => {
                          const newName = story.name + ' (复制)'
                          await cloneStory(story.id, newName)
                        }}
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                      {story.status === 'draft' && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 px-1.5"
                          onClick={() => updateStoryStatus(story.id, 'active')}
                        >
                          <Play className="w-3 h-3" />
                        </Button>
                      )}
                      {story.status !== 'archived' && (
                        <button
                          onClick={() => updateStoryStatus(story.id, 'archived')}
                          className="p-1 hover:bg-warning-bg rounded text-warning"
                          title="归档"
                        >
                          <Archive className="w-3 h-3" />
                        </button>
                      )}
                      <button
                        onClick={async () => {
                          await deleteStory(story.id)
                          if (editingStory?.id === story.id) {
                            setEditingStory(null)
                            setShowStoryForm(false)
                            setSelectedNodeId(null)
                          }
                        }}
                        className="p-1 hover:bg-destructive/10 rounded text-destructive ml-auto"
                        title="删除"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Right: Editor */}
          <div className="flex-1 overflow-y-auto min-w-0">
            {showStoryForm || editingStory ? (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-semibold">{editingStory ? '编辑剧本' : '新建剧本'}</h3>
                    <button
                      onClick={() => {
                        setShowStoryForm(false)
                        setEditingStory(null)
                        setSelectedNodeId(null)
                      }}
                      className="p-1 hover:bg-secondary rounded"
                    >
                      <X className="w-4 h-4 text-muted-foreground" />
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Meta form */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-muted-foreground">剧本名</label>
                      <input
                        type="text"
                        className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                        value={storyForm.name || ''}
                        onChange={(e) => setStoryForm({ ...storyForm, name: e.target.value })}
                        placeholder="输入剧本名称"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-muted-foreground">人设</label>
                      <select
                        className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                        value={storyForm.persona_id || ''}
                        onChange={(e) => setStoryForm({ ...storyForm, persona_id: e.target.value })}
                      >
                        <option value="">选择人设</option>
                        {personas.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-muted-foreground">情感曲线</label>
                      <select
                        className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                        value={storyForm.emotion_curve_template || 'gradual_growth'}
                        onChange={(e) =>
                          setStoryForm({
                            ...storyForm,
                            emotion_curve_template: e.target.value as PersonaStory['emotion_curve_template'],
                          })
                        }
                      >
                        <option value="gradual_growth">渐进成长</option>
                        <option value="valley_comeback">低谷逆袭</option>
                        <option value="suspense_reveal">悬疑揭秘</option>
                        <option value="steady_warm">平稳温暖</option>
                      </select>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-muted-foreground">状态</label>
                      <div className="flex gap-4 h-10 items-center">
                        {(['draft', 'active', 'completed', 'archived'] as const).map((s) => (
                          <label key={s} className="flex items-center gap-1.5 text-sm cursor-pointer">
                            <input
                              type="radio"
                              name="story-status"
                              checked={storyForm.status === s}
                              onChange={() => setStoryForm({ ...storyForm, status: s })}
                            />
                            {STATUS_LABELS[s]}
                          </label>
                        ))}
                      </div>
                    </div>
                    <div className="space-y-1 md:col-span-2">
                      <label className="text-xs font-medium text-muted-foreground">描述</label>
                      <textarea
                        rows={2}
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
                        value={storyForm.description || ''}
                        onChange={(e) => setStoryForm({ ...storyForm, description: e.target.value })}
                        placeholder="剧本描述..."
                      />
                    </div>
                  </div>

                  {/* Node timeline */}
                  {editingStory && (
                    <div className="space-y-3">
                      {/* Conflict warnings */}
                      {conflicts.length > 0 && (
                        <div className="space-y-2">
                          {conflicts.map((warning) => (
                            <AlertBanner
                              key={warning.id}
                              variant={warning.type === 'emotion_jump' ? 'warning' : 'warning'}
                              title={warning.title}
                              description={warning.description}
                              icon={<AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />}
                              onDismiss={() => dismissWarning(warning.id)}
                            />
                          ))}
                        </div>
                      )}

                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-foreground">节点时间轴</h4>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedNodeId(null)
                            resetNodeForm()
                          }}
                        >
                          <Plus className="w-3 h-3 mr-1" />
                          添加节点
                        </Button>
                      </div>
                      <div className="flex items-center gap-2 overflow-x-auto pb-2">
                        {sortedNodes.map((node, idx, arr) => (
                          <div key={node.id} className="flex items-center gap-2 shrink-0">
                            <div className="flex flex-col items-center gap-1">
                              <div className="flex items-center gap-0.5">
                                <button
                                  onClick={() => handleMoveNode(idx, 'left')}
                                  disabled={idx === 0}
                                  title="左移"
                                  className="p-0.5 rounded hover:bg-secondary disabled:opacity-30 disabled:cursor-not-allowed"
                                >
                                  <ChevronLeft className="w-3 h-3 text-muted-foreground" />
                                </button>
                                <button
                                  onClick={() => handleMoveNode(idx, 'right')}
                                  disabled={idx === arr.length - 1}
                                  title="右移"
                                  className="p-0.5 rounded hover:bg-secondary disabled:opacity-30 disabled:cursor-not-allowed"
                                >
                                  <ChevronRight className="w-3 h-3 text-muted-foreground" />
                                </button>
                              </div>
                              <button
                                onClick={() => selectNode(node)}
                                className={`flex flex-col items-center justify-center w-16 h-16 rounded-lg border transition-all ${
                                  selectedNodeId === node.id
                                    ? 'border-primary bg-primary/10 text-primary'
                                    : 'border-border bg-card text-foreground hover:border-primary/30'
                                }`}
                              >
                                <span className="text-xs font-medium">{node.sequence_index + 1}</span>
                                <span className="text-[10px] text-muted-foreground truncate max-w-[56px]">
                                  {node.theme}
                                </span>
                              </button>
                            </div>
                            {idx < arr.length - 1 && (
                              <ChevronRight className="w-4 h-4 text-muted-foreground" />
                            )}
                          </div>
                        ))}
                        {nodes.length === 0 && (
                          <div className="text-xs text-muted-foreground py-4">暂无节点，点击上方按钮添加</div>
                        )}
                      </div>

                      {/* Emotion curve chart */}
                      {emotionChartData.length > 0 && (
                        <div className="space-y-2 pt-2">
                          <div className="flex items-center gap-2">
                            <Activity className="w-4 h-4 text-muted-foreground" />
                            <h4 className="text-sm font-semibold text-foreground">情感曲线</h4>
                            <span className="text-xs text-muted-foreground">
                              ({EMOTION_CURVE_LABELS[editingStory.emotion_curve_template]})
                            </span>
                          </div>
                          <div className="h-64 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                              <AreaChart data={emotionChartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                                <defs>
                                  <linearGradient id="emotionGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop
                                      offset="5%"
                                      stopColor={EMOTION_CURVE_COLORS[editingStory.emotion_curve_template]}
                                      stopOpacity={0.3}
                                    />
                                    <stop
                                      offset="95%"
                                      stopColor={EMOTION_CURVE_COLORS[editingStory.emotion_curve_template]}
                                      stopOpacity={0}
                                    />
                                  </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                <XAxis
                                  dataKey="index"
                                  tick={{ fontSize: 12 }}
                                  stroke="var(--muted-foreground)"
                                  label={{ value: '节点序号', position: 'insideBottom', offset: -5, fontSize: 12 }}
                                />
                                <YAxis
                                  domain={[0.5, 4.5]}
                                  ticks={[1, 2, 3, 4]}
                                  tickFormatter={(v: number) => {
                                    const map: Record<number, string> = { 1: '低落', 2: '平稳', 3: '高涨', 4: '爆发' }
                                    return map[v] || ''
                                  }}
                                  tick={{ fontSize: 12 }}
                                  stroke="var(--muted-foreground)"
                                />
                                <Tooltip
                                  contentStyle={{
                                    backgroundColor: 'var(--card)',
                                    border: '1px solid var(--border)',
                                    borderRadius: '0.5rem',
                                    fontSize: '0.875rem',
                                  }}
                                  formatter={(value, _name, props) => {
                                    const p = props?.payload as { theme?: string; emotionLabel?: string } | undefined
                                    return [`${value} (${p?.emotionLabel})`, '情感值']
                                  }}
                                  labelFormatter={(label) => `节点 ${label}：${emotionChartData[Number(label) - 1]?.theme || ''}`}
                                />
                                <Legend
                                  verticalAlign="bottom"
                                  height={24}
                                  formatter={() =>
                                    `情感曲线 — ${EMOTION_CURVE_LABELS[editingStory.emotion_curve_template]}`
                                  }
                                />
                                <Area
                                  type="monotone"
                                  dataKey="emotion"
                                  stroke={EMOTION_CURVE_COLORS[editingStory.emotion_curve_template]}
                                  strokeWidth={2}
                                  fill="url(#emotionGradient)"
                                  dot={{ r: 4, strokeWidth: 2, fill: '#fff' }}
                                  activeDot={{ r: 6 }}
                                />
                              </AreaChart>
                            </ResponsiveContainer>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <span
                                className="inline-block w-3 h-3 rounded-full"
                                style={{ backgroundColor: EMOTION_CURVE_COLORS['gradual_growth'] }}
                              />
                              渐进成长
                            </span>
                            <span className="flex items-center gap-1">
                              <span
                                className="inline-block w-3 h-3 rounded-full"
                                style={{ backgroundColor: EMOTION_CURVE_COLORS['valley_comeback'] }}
                              />
                              低谷逆袭
                            </span>
                            <span className="flex items-center gap-1">
                              <span
                                className="inline-block w-3 h-3 rounded-full"
                                style={{ backgroundColor: EMOTION_CURVE_COLORS['suspense_reveal'] }}
                              />
                              悬疑揭秘
                            </span>
                            <span className="flex items-center gap-1">
                              <span
                                className="inline-block w-3 h-3 rounded-full"
                                style={{ backgroundColor: EMOTION_CURVE_COLORS['steady_warm'] }}
                              />
                              平稳温暖
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Node form */}
                  {editingStory && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-border pt-4">
                      <div className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">主题</label>
                        <input
                          type="text"
                          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                          value={nodeForm.theme || ''}
                          onChange={(e) => setNodeForm({ ...nodeForm, theme: e.target.value })}
                          placeholder="节点主题"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">情绪</label>
                        <select
                          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                          value={nodeForm.emotion_tone || 'medium'}
                          onChange={(e) =>
                            setNodeForm({ ...nodeForm, emotion_tone: e.target.value as StoryNode['emotion_tone'] })
                          }
                        >
                          <option value="low">低落</option>
                          <option value="medium">平稳</option>
                          <option value="high">高涨</option>
                          <option value="burst">爆发</option>
                        </select>
                      </div>
                      <div className="space-y-1 md:col-span-2">
                        <label className="text-xs font-medium text-muted-foreground">关键事件</label>
                        <textarea
                          rows={2}
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
                          value={nodeForm.key_event || ''}
                          onChange={(e) => setNodeForm({ ...nodeForm, key_event: e.target.value })}
                          placeholder="关键事件描述"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">前情回顾</label>
                        <textarea
                          rows={2}
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
                          value={nodeForm.prev_recap || ''}
                          onChange={(e) => setNodeForm({ ...nodeForm, prev_recap: e.target.value })}
                          placeholder="前情回顾..."
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">下期预告</label>
                        <textarea
                          rows={2}
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
                          value={nodeForm.next_teaser || ''}
                          onChange={(e) => setNodeForm({ ...nodeForm, next_teaser: e.target.value })}
                          placeholder="下期预告..."
                        />
                      </div>
                      <div className="flex gap-2 md:col-span-2">
                        <Button size="sm" onClick={selectedNodeId ? handleUpdateNode : handleCreateNode}>
                          <Save className="w-3 h-3 mr-1" />
                          {selectedNodeId ? '保存节点' : '创建节点'}
                        </Button>
                        {selectedNodeId && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setSelectedNodeId(null)
                              resetNodeForm()
                            }}
                          >
                            取消
                          </Button>
                        )}
                        {selectedNodeId && (
                          <Button
                            size="sm"
                            variant="danger"
                            className="ml-auto"
                            onClick={async () => {
                              await deleteNode(selectedNodeId)
                              setSelectedNodeId(null)
                              resetNodeForm()
                            }}
                          >
                            <Trash2 className="w-3 h-3 mr-1" />
                            删除节点
                          </Button>
                        )}
                      </div>
                    </div>
                  )}

                  {storyFormError && (
                    <p className="text-xs text-destructive">{storyFormError}</p>
                  )}
                  <div className="flex gap-2 border-t border-border pt-4">
                    <Button onClick={handleSaveStoryMeta}>
                      <Save className="w-4 h-4 mr-1" />
                      保存剧本
                    </Button>
                    {editingStory && editingStory.status === 'draft' && (
                      <Button
                        variant="outline"
                        onClick={() => updateStoryStatus(editingStory.id, 'active')}
                      >
                        <Play className="w-4 h-4 mr-1" />
                        激活剧本
                      </Button>
                    )}
                    {editingStory && (
                      <Button
                        variant="danger"
                        className="ml-auto"
                        onClick={() => {
                          deleteStory(editingStory.id)
                          setEditingStory(null)
                          setShowStoryForm(false)
                        }}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        删除剧本
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="h-full flex items-center justify-center">
                <EmptyState icon={BookOpen} title="编辑剧本" description="点击左侧剧本进行编辑，或点击右上角「新建剧本」" />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
