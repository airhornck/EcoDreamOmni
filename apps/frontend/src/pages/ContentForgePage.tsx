import { useEffect, useMemo, useState } from 'react'
import { useSearchParams, useParams } from 'react-router-dom'
import { authHeaders } from '../lib/api'
import { useContentForgeStore } from '../stores/contentForgeStore'
import { useAssetPoolStore } from '../stores/assetPoolStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge, type BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { cn } from '../lib/utils'
import {
  Hammer,
  FileText,
  X,
  ChevronDown,
  ChevronRight,
  Clock,
  Coins,
  Sparkles,
  BookOpen,
  User,
  Film,
  Layers,
  BrainCircuit,
  Thermometer,
  ImageOff,
  Image,
  Tag,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

/* ── helpers ── */

const statusLabels: Record<string, string> = {
  draft: '草稿',
  reviewing: '审核中',
  approved: '已通过',
  published: '已发布',
  rejected: '已驳回',
}

const statusVariants: Record<string, BadgeVariant> = {
  draft: 'default',
  reviewing: 'warning',
  approved: 'info',
  published: 'success',
  rejected: 'danger',
}

import { simpleMarkdown } from '../lib/markdown'
import { highlightCompliance } from '../lib/compliance'
import { SixLayerPrompt, type PromptLayer } from '../components/content-forge/SixLayerPrompt'

/* ── ring score component (SVG) ── */

function RingScore({ value = 0, size = 64, stroke = 6 }: { value?: number; size?: number; stroke?: number }) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const offset = c - (Math.min(value, 100) / 100) * c
  const color = value >= 80 ? 'text-success' : value >= 60 ? 'text-warning' : 'text-destructive'
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="currentColor" strokeWidth={stroke} fill="none" className="text-secondary" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="currentColor"
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={color}
          style={{ transition: 'stroke-dashoffset 0.6s ease-out' }}
        />
      </svg>
      <span className="absolute text-xs font-bold">{value}</span>
    </div>
  )
}

/* ── collapsible panel ── */

function CollapsibleSection({ title, icon: Icon, children, defaultOpen = false }: { title: string; icon?: LucideIcon; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 bg-secondary/40 hover:bg-secondary/60 transition-colors text-sm font-medium"
      >
        <span className="flex items-center gap-2">
          {Icon && <Icon className="w-4 h-4 text-muted-foreground" />}
          {title}
        </span>
        {open ? <ChevronDown className="w-4 h-4 text-muted-foreground" /> : <ChevronRight className="w-4 h-4 text-muted-foreground" />}
      </button>
      {open && <div className="px-3 py-3 text-xs space-y-2">{children}</div>}
    </div>
  )
}

/* ── page ── */

export function ContentForgePage() {
  const { taskId } = useParams<{ taskId?: string }>()
  const [searchParams] = useSearchParams()
  const prefillTopic = searchParams.get('topic') || ''
  const [taskContextLoading, setTaskContextLoading] = useState(false)
  const [taskContextError, setTaskContextError] = useState<string | null>(null)
  const [promptLayers, setPromptLayers] = useState<PromptLayer[]>([])
  const [promptLayersLoading, setPromptLayersLoading] = useState(false)

  const {
    drafts,
    generated,
    isLoading,
    error,
    personas,
    stories,
    storyNodes,
    contentSeries,
    llmModels,
    fetchDrafts,
    fetchPersonas,
    fetchStories,
    fetchStoryNodes,
    fetchContentSeries,
    fetchLLMModels,
    clearError,
  } = useContentForgeStore()

  /* local form state */
  const [showCreate, setShowCreate] = useState(false)

  const [topic, setTopic] = useState(prefillTopic)
  const [platform, setPlatform] = useState('xhs')
  const [tone, setTone] = useState('温馨')
  const [length, setLength] = useState('中')

  const [personaId, setPersonaId] = useState('')
  const [storyId, setStoryId] = useState('')
  const [nodeId, setNodeId] = useState('')

  const [seriesId, setSeriesId] = useState('')
  const [modelId, setModelId] = useState('')
  const [temperature, setTemperature] = useState(0.7)

  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [tagInput, setTagInput] = useState('')
  const [coverImageUrl, setCoverImageUrl] = useState('')

  // draftId state removed in Mode C refactor — drafts managed by Copilot Action Cards

  /* task context mode: preload config from TaskHub */
  useEffect(() => {
    if (!taskId) return
    let cancelled = false
    const run = async () => {
      setTaskContextLoading(true)
      setTaskContextError(null)
      try {
        const res = await fetch(`/api/task-hub/tasks/${taskId}`, { headers: authHeaders() })
        if (!res.ok) throw new Error(`获取任务配置失败: ${res.status}`)
        const task = await res.json()
        if (cancelled) return
        // Pre-fill form from task config
        if (task.name) setTopic(task.name)
        if (task.platform) setPlatform(task.platform)
        const vars = task.prompt_variables || {}
        if (vars.topic) setTopic(vars.topic)
        if (vars.platform) setPlatform(vars.platform)
        if (vars.tone) setTone(vars.tone)
        if (vars.length) setLength(vars.length)
        if (task.persona_id) setPersonaId(task.persona_id)
        if (task.persona_story_id) setStoryId(task.persona_story_id)
        if (task.current_node_id) setNodeId(task.current_node_id)
        if (task.content_series_id) setSeriesId(task.content_series_id)
        if (vars.model_id) setModelId(vars.model_id)
        if (vars.temperature !== undefined) setTemperature(Number(vars.temperature))
        setTaskContextLoading(false)
      } catch (err) {
        if (cancelled) return
        setTaskContextError(err instanceof Error ? err.message : '加载失败')
        setTaskContextLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [taskId])

  /* asset picker */
  const [showAssetPicker, setShowAssetPicker] = useState(false)
  const { assets: assetPoolAssets, fetchAssets: fetchAssetPoolAssets } = useAssetPoolStore()

  /* derived */
  const selectedPersona = useMemo(() => personas.find((p) => p.id === personaId), [personas, personaId])
  const selectedNode = useMemo(() => storyNodes.find((n) => n.id === nodeId), [storyNodes, nodeId])

  const { html: bodyHtml, hits: complianceHits } = useMemo(() => highlightCompliance(body), [body])
  const bodyPreview = useMemo(() => simpleMarkdown(bodyHtml), [bodyHtml])

  /* init data */
  useEffect(() => {
    fetchDrafts()
    fetchPersonas()
    fetchStories()
    fetchContentSeries()
    fetchLLMModels()
  }, [fetchDrafts, fetchPersonas, fetchStories, fetchContentSeries, fetchLLMModels])

  /* story change -> fetch nodes */
  useEffect(() => {
    if (storyId) {
      fetchStoryNodes(storyId)
    } else {
      const id = requestAnimationFrame(() => setNodeId(''))
      return () => cancelAnimationFrame(id)
    }
  }, [storyId, fetchStoryNodes])

  /* fetch six-layer prompt decomposition */
  const fetchPromptLayers = async () => {
    if (!topic) return
    setPromptLayersLoading(true)
    try {
      const res = await fetch('/api/content-forge/content-prompt-decompose', {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, platform, persona_id: personaId || undefined }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setPromptLayers(data.layers || [])
    } catch (err) {
      console.warn('Prompt decomposition failed:', err)
      setPromptLayers([])
    } finally {
      setPromptLayersLoading(false)
    }
  }

  /* fetch six-layer prompt when config changes */
  useEffect(() => {
    const timer = setTimeout(() => {
      if (showCreate && topic) {
        fetchPromptLayers()
      }
    }, 500)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topic, platform, personaId, showCreate])

  /* fill generated into form */
  useEffect(() => {
    if (generated) {
      const g = generated
      requestAnimationFrame(() => {
        setTitle(g.title || '')
        setBody(g.body || '')
        setTags(g.tags || [])
        setCoverImageUrl(g.cover_image_url || '')
      })
    }
  }, [generated])

  const handleAddTag = () => {
    const t = tagInput.trim()
    if (t && !tags.includes(t)) {
      setTags((prev) => [...prev, t])
      setTagInput('')
    }
  }

  const handleRemoveTag = (t: string) => {
    setTags((prev) => prev.filter((x) => x !== t))
  }

  const loadDraft = (draft: typeof drafts[number]) => {
    setTitle(draft.title)
    setBody(draft.body)
    setTags(draft.tags || [])
    setCoverImageUrl(draft.cover_image_url || '')
    setPlatform(draft.platform)
    // draftId no longer needed in Mode C — Copilot handles save/submit
    setShowCreate(true)
  }

  return (
    <div className="space-y-6">
      {taskContextLoading && (
        <div className="p-3 rounded-lg bg-info/10 text-info text-sm flex items-center gap-2">
          <Clock className="w-4 h-4 animate-spin" />
          正在加载任务配置...
        </div>
      )}
      {taskContextError && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center justify-between">
          <span>{taskContextError}</span>
          <button onClick={() => setTaskContextError(null)} className="text-xs hover:underline">清除</button>
        </div>
      )}
      {taskId && !taskContextLoading && !taskContextError && (
        <div className="p-3 rounded-lg bg-success/10 text-success text-sm flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          任务上下文模式：已加载任务 #{taskId.slice(0, 8)} 的配置
        </div>
      )}
      {/* Mode C: 工作区禁止新建按钮，操作走 Copilot Action Card */}
      <PageHeader
        title={taskId ? `内容锻造 — 任务 #${taskId.slice(0, 8)}` : '内容锻造'}
        subtitle={taskId ? '基于任务配置进行内容生成与干预' : 'AI 辅助内容生成与草稿管理'}
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={clearError} className="hover:opacity-70">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ── Editor (3 columns) ── */}
      {showCreate && (
        <div className="flex gap-4 items-start">
          {/* ═════ Left: Config ═════ */}
          <div className="w-72 shrink-0 space-y-4">
            <Card>
              <CardHeader className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-semibold">生成配置</h3>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Topic */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">Topic / 主题</label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="输入内容主题..."
                    className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm"
                  />
                </div>

                {/* Platform */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">平台</label>
                  <select
                    value={platform}
                    onChange={(e) => setPlatform(e.target.value)}
                    className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm"
                  >
                    <option value="xhs">小红书</option>
                    <option value="douyin">抖音</option>
                    <option value="wechat_channels">视频号</option>
                  </select>
                </div>

                {/* Tone */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">语气风格</label>
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm"
                  >
                    <option value="温馨">温馨</option>
                    <option value="专业">专业</option>
                    <option value="幽默">幽默</option>
                  </select>
                </div>

                {/* Length */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">篇幅</label>
                  <select
                    value={length}
                    onChange={(e) => setLength(e.target.value)}
                    className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm"
                  >
                    <option value="短">短</option>
                    <option value="中">中</option>
                    <option value="长">长</option>
                  </select>
                </div>

                {/* Persona */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">选择 Persona</label>
                  <select
                    value={personaId}
                    onChange={(e) => setPersonaId(e.target.value)}
                    className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm"
                  >
                    <option value="">— 请选择 —</option>
                    {personas.map((p) => (
                      <option key={p.id} value={p.id}>{p.nickname} ({p.pet_type})</option>
                    ))}
                  </select>
                  {selectedPersona && (
                    <div className="mt-1.5 text-xs text-muted-foreground flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {selectedPersona.nickname} · {selectedPersona.pet_type}
                    </div>
                  )}
                </div>

                {/* Story + Node */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">PersonaStory</label>
                  <select
                    value={storyId}
                    onChange={(e) => setStoryId(e.target.value)}
                    className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm mb-2"
                  >
                    <option value="">— 请选择剧本 —</option>
                    {stories.map((s) => (
                      <option key={s.id} value={s.id}>{s.title}</option>
                    ))}
                  </select>
                  {storyId && (
                    <select
                      value={nodeId}
                      onChange={(e) => setNodeId(e.target.value)}
                      className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm"
                    >
                      <option value="">— 请选择节点 —</option>
                      {storyNodes.map((n) => (
                        <option key={n.id} value={n.id}>{n.title}</option>
                      ))}
                    </select>
                  )}
                  {selectedNode && (
                    <div className="mt-1.5 text-xs text-muted-foreground space-y-0.5">
                      <div>主题：{selectedNode.theme}</div>
                      <div>情感：{selectedNode.mood}</div>
                    </div>
                  )}
                </div>

                {/* Content Series */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">Content Series</label>
                  <select
                    value={seriesId}
                    onChange={(e) => setSeriesId(e.target.value)}
                    className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm"
                  >
                    <option value="">— 不绑定系列 —</option>
                    {contentSeries.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>

                {/* LLM Model */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">LLM 模型</label>
                  <select
                    value={modelId}
                    onChange={(e) => setModelId(e.target.value)}
                    className="w-full h-9 px-3 rounded-lg border border-border bg-background text-sm"
                  >
                    <option value="">— 使用默认 —</option>
                    {llmModels.map((m) => (
                      <option key={m.id} value={m.id}>{m.name} ({m.provider})</option>
                    ))}
                  </select>
                </div>

                {/* Temperature */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 flex items-center gap-1">
                    <Thermometer className="w-3 h-3" />
                    温度参数：{temperature.toFixed(1)}
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.1}
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full mt-1"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground mt-0.5">
                    <span>精确</span>
                    <span>创意</span>
                  </div>
                </div>

                {/* Mode C: 工作区禁止 AI 生成/重新生成按钮，操作走 Copilot Action Card */}
              </CardContent>
            </Card>
          </div>

          {/* ═════ Center: Preview ═════ */}
          <div className="flex-1 min-w-0 space-y-4">
            <Card>
              <CardHeader className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-semibold">内容预览</h3>
                {complianceHits > 0 && (
                  <Badge variant="warning" className="ml-auto">
                    <AlertTriangle className="w-3 h-3 mr-1" />
                    敏感词 {complianceHits} 处
                  </Badge>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Title */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">标题</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="生成后标题显示在这里..."
                    className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm font-medium"
                  />
                </div>

                {/* Body */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">正文</label>
                  <div className="relative">
                    <textarea
                      value={body}
                      onChange={(e) => setBody(e.target.value)}
                      placeholder="生成后正文显示在这里..."
                      rows={10}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
                    />
                  </div>
                  {body && (
                    <div className="mt-2 p-3 rounded-lg border border-border bg-secondary/30 text-sm leading-relaxed">
                      <div dangerouslySetInnerHTML={{ __html: bodyPreview }} />
                    </div>
                  )}
                </div>

                {/* Cover image */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 block">封面图</label>
                  {coverImageUrl ? (
                    <div className="relative rounded-lg overflow-hidden border border-border w-full h-48">
                      <img src={coverImageUrl} alt="cover" className="w-full h-full object-cover" />
                      <button
                        onClick={() => setCoverImageUrl('')}
                        className="absolute top-2 right-2 p-1 bg-black/50 text-white rounded-md hover:bg-black/70"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center w-full h-48 rounded-lg border border-dashed border-border bg-secondary/30 text-muted-foreground gap-2">
                      <ImageOff className="w-8 h-8" />
                      <span className="text-xs">暂无封面图</span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => { setShowAssetPicker(true); fetchAssetPoolAssets() }}
                      >
                        <Image className="w-3 h-3 mr-1" />
                        从素材库选择
                      </Button>
                    </div>
                  )}
                  {coverImageUrl && (
                    <div className="mt-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="w-full"
                        onClick={() => { setShowAssetPicker(true); fetchAssetPoolAssets() }}
                      >
                        <Image className="w-3 h-3 mr-1" />
                        更换封面图
                      </Button>
                    </div>
                  )}
                </div>

                {/* Tags */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1 flex items-center gap-1">
                    <Tag className="w-3 h-3" />
                    标签
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {tags.map((t) => (
                      <Badge key={t} variant="primary" className="pl-2 pr-1 py-0.5">
                        {t}
                        <button
                          onClick={() => handleRemoveTag(t)}
                          className="ml-1 p-0.5 hover:bg-primary/20 rounded"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddTag(); } }}
                      placeholder="输入标签回车添加"
                      className="flex-1 h-9 px-3 rounded-lg border border-border bg-background text-sm"
                    />
                    {/* Mode C: 工作区禁止添加按钮，操作走 Copilot Action Card */}
                  </div>
                </div>

                {/* Mode C: 工作区禁止保存/提交/丢弃按钮，操作走 Copilot Action Card */}
              </CardContent>
            </Card>
          </div>

          {/* ═════ Right: Agent Summary + Six-Layer Prompt ═════ */}
          <div className="w-72 shrink-0 space-y-4">
            <Card>
              <CardHeader className="flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-semibold">Agent 摘要</h3>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* Quality Score */}
                <div className="flex items-center gap-4">
                  <RingScore value={generated?.scores?.overall ?? 0} size={64} stroke={6} />
                  <div className="flex-1 space-y-1.5">
                    {generated?.scores ? (
                      <>
                        <ScoreBar label="标题吸引力" value={generated.scores.title_attractiveness} />
                        <ScoreBar label="正文完整性" value={generated.scores.body_completeness} />
                        <ScoreBar label="标签相关性" value={generated.scores.tag_relevance} />
                        <ScoreBar label="封面质量" value={generated.scores.cover_quality} />
                      </>
                    ) : (
                      <p className="text-xs text-muted-foreground">生成后将显示结构质量评分</p>
                    )}
                  </div>
                </div>

                {/* Token usage */}
                <div className="rounded-lg border border-border p-3 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-medium text-foreground">
                    <Coins className="w-4 h-4 text-muted-foreground" />
                    Token 消耗
                  </div>
                  {generated?.tokens ? (
                    <div className="space-y-1 text-xs text-muted-foreground">
                      <div className="flex justify-between">
                        <span>Prompt</span>
                        <span>{generated.tokens.prompt_tokens.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Completion</span>
                        <span>{generated.tokens.completion_tokens.toLocaleString()}</span>
                      </div>
                      <div className="border-t border-border pt-1 flex justify-between font-medium text-foreground">
                        <span>Total</span>
                        <span>{generated.tokens.total_tokens.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-success">
                        <span>估算成本</span>
                        <span>¥ {generated.tokens.estimated_cost_cny.toFixed(4)}</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">生成后将显示 Token 消耗</p>
                  )}
                </div>

                {/* Duration */}
                <div className="rounded-lg border border-border p-3 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-medium text-foreground">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    生成耗时
                  </div>
                  <span className="text-xs font-mono">
                    {generated?.duration_ms ? `${generated.duration_ms} ms` : '—'}
                  </span>
                </div>

                {/* Injection context */}
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">注入上下文</h4>
                  <CollapsibleSection title="BrandKnowledge RAG" icon={BookOpen}>
                    {generated?.injection_context?.brand_knowledge?.length ? (
                      <ul className="space-y-1">
                        {generated.injection_context.brand_knowledge.map((bk, idx) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span className="text-muted-foreground">·</span>
                            <span>{bk.title}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-muted-foreground">无引用</span>
                    )}
                  </CollapsibleSection>

                  <CollapsibleSection title="PersonaStory 上下文" icon={Film}>
                    {generated?.injection_context?.persona_story ? (
                      <div className="space-y-1.5">
                        <div><span className="text-muted-foreground">当前节点：</span>{generated.injection_context.persona_story.current_node_theme}</div>
                        <div><span className="text-muted-foreground">前情回顾：</span>{generated.injection_context.persona_story.previous_recap}</div>
                        <div><span className="text-muted-foreground">情感基调：</span>{generated.injection_context.persona_story.mood}</div>
                        <div><span className="text-muted-foreground">下集预告：</span>{generated.injection_context.persona_story.next_preview}</div>
                      </div>
                    ) : (
                      <span className="text-muted-foreground">无剧本上下文</span>
                    )}
                  </CollapsibleSection>

                  <CollapsibleSection title="PlatformRule 约束" icon={Layers}>
                    {generated?.injection_context?.platform_rules?.length ? (
                      <ul className="space-y-1">
                        {generated.injection_context.platform_rules.map((rule, idx) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span className="text-muted-foreground">·</span>
                            <span>{rule}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-muted-foreground">无平台规则约束</span>
                    )}
                  </CollapsibleSection>
                </div>
              </CardContent>
            </Card>

            {/* Six-Layer Prompt Visualization */}
            <SixLayerPrompt layers={promptLayers} isLoading={promptLayersLoading} />
          </div>
        </div>
      )}

      {/* ── Asset Picker Modal ── */}
      {showAssetPicker && (
        <>
          <div className="fixed inset-0 bg-black/50 z-40" onClick={() => setShowAssetPicker(false)} />
          <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[640px] max-w-[90vw] max-h-[80vh] bg-card border border-border rounded-xl shadow-xl z-50 flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <h3 className="text-base font-semibold">从素材库选择封面图</h3>
              <button onClick={() => setShowAssetPicker(false)} className="p-1 hover:bg-secondary rounded">
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-5">
              {assetPoolAssets.length === 0 ? (
                <div className="text-center text-sm text-muted-foreground py-10">
                  素材库为空，请先前往「素材库」页面添加图片
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-3">
                  {assetPoolAssets
                    .filter((a) => a.type === 'image' || a.type === 'OPERATOR_UPLOAD' || a.type === 'AI_GENERATED')
                    .map((asset) => (
                      <button
                        key={asset.id}
                        onClick={() => {
                          setCoverImageUrl(asset.url)
                          setShowAssetPicker(false)
                        }}
                        className="group relative rounded-lg border border-border overflow-hidden hover:border-primary transition-all text-left"
                      >
                        <div className="w-full h-32 bg-secondary/50">
                          <img
                            src={asset.thumbnail_url || asset.url}
                            alt={asset.name}
                            className="w-full h-full object-cover"
                            loading="lazy"
                            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                          />
                        </div>
                        <div className="p-2">
                          <p className="text-xs font-medium truncate">{asset.name}</p>
                          <p className="text-[10px] text-muted-foreground truncate">{asset.url}</p>
                        </div>
                      </button>
                    ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* ── Drafts list ── */}
      <Card>
        <CardHeader className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold">内容草稿列表</h2>
        </CardHeader>
        <CardContent>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && drafts.length === 0 && (
            <EmptyState
              icon={Hammer}
              title="暂无内容草稿"
              description="点击新建内容开始创建，或通过右侧 Copilot 面板操作"
              action={
                <Button size="sm" onClick={() => setShowCreate(true)} aria-label="新建内容">
                  <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                  新建内容
                </Button>
              }
            />
          )}
          <div className="space-y-3">
            {drafts.map((draft) => (
              <div
                key={draft.id}
                onClick={() => loadDraft(draft)}
                className="flex items-start justify-between p-4 rounded-lg border border-border hover:border-primary/30 transition-all cursor-pointer"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-foreground">{draft.title}</h3>
                    <Badge variant={(statusVariants[draft.status] as BadgeVariant) || 'default'}>
                      {statusLabels[draft.status] || draft.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{draft.body}</p>
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="default">{draft.platform}</Badge>
                    {draft.tags?.map((tag) => (
                      <Badge key={tag} variant="default">{tag}</Badge>
                    ))}
                  </div>
                </div>
                {/* Mode C: 工作区禁止删除按钮，操作走 Copilot Action Card */}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

/* ── sub-components ── */

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? 'bg-success' : value >= 60 ? 'bg-warning' : 'bg-destructive'
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-muted-foreground w-16 shrink-0 truncate">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-secondary overflow-hidden">
        <div className={cn('h-full rounded-full', color)} style={{ width: `${value}%`, transition: 'width 0.6s ease-out' }} />
      </div>
      <span className="text-[10px] w-6 text-right">{value}</span>
    </div>
  )
}


