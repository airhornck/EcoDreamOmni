import { useEffect, useMemo, useState } from 'react'
import { usePlatformRulesStore, type PlatformRule, type EvaluateResult } from '../stores/platformRulesStore'
import { usePageCopilot } from '../hooks/usePageCopilot'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge, type BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { cn } from '../lib/utils'
import {
  Scale, Plus, Trash2, ToggleLeft, ToggleRight, Eye, X, Pencil,
  History, Play, AlertTriangle, ShieldCheck, ShieldAlert, Info,
  Smartphone, Video, Tv, Globe,
} from 'lucide-react'

/* ── config ── */

const layerShortLabels: Record<string, string> = {
  l1_static: 'L1',
  l2_keyword: 'L2',
  l3_account_state: 'L3',
  l3_dynamic_risk: 'L3',
  l4_dynamic_risk: 'L4',
}

const layerVariants: Record<string, BadgeVariant> = {
  l1_static: 'danger',
  l2_keyword: 'warning',
  l3_account_state: 'info',
  l3_dynamic_risk: 'info',
  l4_dynamic_risk: 'default',
}

const actionLabels: Record<string, string> = {
  block: '拦截',
  warn: '警告',
  suggest: '建议',
  flag_for_review: '复核',
}

const actionVariants: Record<string, BadgeVariant> = {
  block: 'danger',
  warn: 'warning',
  suggest: 'info',
  flag_for_review: 'default',
}

const platforms = [
  { key: 'all', label: '全部', icon: Globe },
  { key: 'xiaohongshu', label: '小红书', icon: Smartphone },
  { key: 'douyin', label: '抖音', icon: Video },
  { key: 'wechat_channels', label: '视频号', icon: Tv },
]

const conditionTypes = [
  { value: 'keyword', label: '关键词匹配' },
  { value: 'keyword_regex', label: '正则匹配' },
  { value: 'keyword_pair', label: '关键词对（触发+必需）' },
  { value: 'frequency', label: '频率限制' },
  { value: 'schedule', label: '时间窗口' },
]

interface ConditionJson {
  type?: string
  keywords?: string[]
  pattern?: string
  trigger_keywords?: string[]
  required_keywords?: string[]
  condition?: string
  case_sensitive?: boolean
}

/* ── helpers ── */

function formatConditionPreview(rule: PlatformRule): string {
  const c = (rule.condition_json || {}) as ConditionJson
  switch (c.type) {
    case 'keyword':
      return `关键词: ${(c.keywords || []).slice(0, 3).join(', ')}${(c.keywords || []).length > 3 ? '...' : ''}`
    case 'keyword_regex':
      return `正则: ${c.pattern || ''}`.slice(0, 40)
    case 'keyword_pair':
      return `触发: ${(c.trigger_keywords || []).slice(0, 2).join(', ')}...`
    case 'frequency':
      return `频率: ${c.condition || ''}`
    case 'schedule':
      return `时间: ${c.condition || ''}`
    default:
      return '条件: 未配置'
  }
}

/* ── Condition Builder ── */

function ConditionBuilder({ value, onChange }: { value: ConditionJson; onChange: (v: ConditionJson) => void }) {
  const type = value.type || 'keyword'

  const update = (patch: Partial<ConditionJson>) => onChange({ ...value, ...patch })

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <label className="text-sm font-medium">条件类型</label>
        <select
          value={type}
          onChange={(e) => onChange({ type: e.target.value })}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
        >
          {conditionTypes.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
      </div>

      {type === 'keyword' && (
        <>
          <div className="space-y-1">
            <label className="text-sm font-medium">关键词列表（每行一个）</label>
            <textarea
              value={(value.keywords || []).join('\n')}
              onChange={(e) => update({ keywords: e.target.value.split('\n').filter(Boolean) })}
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-y"
              placeholder="阿莫西林&#10;处方药"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox" checked={!!value.case_sensitive}
              onChange={(e) => update({ case_sensitive: e.target.checked })}
              className="rounded"
            />
            区分大小写
          </label>
        </>
      )}

      {type === 'keyword_regex' && (
        <>
          <div className="space-y-1">
            <label className="text-sm font-medium">正则表达式</label>
            <input
              type="text" value={value.pattern || ''}
              onChange={(e) => update({ pattern: e.target.value })}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              placeholder="(驱虫药|处方)"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox" checked={!!value.case_sensitive}
              onChange={(e) => update({ case_sensitive: e.target.checked })}
              className="rounded"
            />
            区分大小写
          </label>
        </>
      )}

      {type === 'keyword_pair' && (
        <>
          <div className="space-y-1">
            <label className="text-sm font-medium">触发关键词（命中即触发检查）</label>
            <textarea
              value={(value.trigger_keywords || []).join('\n')}
              onChange={(e) => update({ trigger_keywords: e.target.value.split('\n').filter(Boolean) })}
              rows={2}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-y"
              placeholder="下单&#10;购买链接"
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium">必需关键词（必须同时存在才不触发）</label>
            <textarea
              value={(value.required_keywords || []).join('\n')}
              onChange={(e) => update({ required_keywords: e.target.value.split('\n').filter(Boolean) })}
              rows={2}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-y"
              placeholder="合作&#10;广告"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox" checked={!!value.case_sensitive}
              onChange={(e) => update({ case_sensitive: e.target.checked })}
              className="rounded"
            />
            区分大小写
          </label>
        </>
      )}

      {type === 'frequency' && (
        <div className="space-y-1">
          <label className="text-sm font-medium">频率条件表达式</label>
          <input
            type="text" value={value.condition || ''}
            onChange={(e) => update({ condition: e.target.value })}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            placeholder="daily_post_count>=3"
          />
          <p className="text-xs text-muted-foreground">示例: daily_post_count&gt;=3, account_age_days&lt;7</p>
        </div>
      )}

      {type === 'schedule' && (
        <div className="space-y-1">
          <label className="text-sm font-medium">时间窗口条件</label>
          <input
            type="text" value={value.condition || ''}
            onChange={(e) => update({ condition: e.target.value })}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            placeholder="month=6 AND day IN [1-18]"
          />
          <p className="text-xs text-muted-foreground">示例: month=6 AND day IN [1-18] AND content_type=commercial</p>
        </div>
      )}
    </div>
  )
}

/* ── TestRunPanel ── */

function TestRunPanel() {
  const { evaluateContent, evaluateResult, evaluateLoading, clearEvaluate } = usePlatformRulesStore()
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [tags, setTags] = useState('')
  const [platform, setPlatform] = useState('xiaohongshu')

  const handleRun = () => {
    evaluateContent({
      title,
      body,
      tags: tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean),
      platform,
    })
  }

  return (
    <Card className="min-w-0 overflow-hidden">
      <CardHeader className="flex items-center gap-2">
        <Play className="w-4 h-4 text-primary" />
        <h3 className="text-base font-semibold">规则试跑</h3>
        <span className="text-xs text-muted-foreground">输入内容即时测试规则命中</span>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-3">
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="h-10 px-3 rounded-lg border border-border bg-background text-sm"
          >
            <option value="xiaohongshu">小红书</option>
            <option value="douyin">抖音</option>
            <option value="wechat_channels">视频号</option>
          </select>
          <input
            type="text" placeholder="标题" value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="flex-1 h-10 px-3 rounded-lg border border-border bg-background text-sm"
          />
        </div>
        <textarea
          placeholder="正文内容..." value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-y"
        />
        <input
          type="text" placeholder="标签，用逗号分隔" value={tags}
          onChange={(e) => setTags(e.target.value)}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
        />
        <div className="flex gap-2">
          <Button onClick={handleRun} isLoading={evaluateLoading} disabled={!body.trim()}>
            <Play className="w-4 h-4" />
            运行评估
          </Button>
          {evaluateResult && (
            <Button variant="ghost" onClick={clearEvaluate}>清除结果</Button>
          )}
        </div>

        {evaluateResult && <EvaluateResultView result={evaluateResult} />}
      </CardContent>
    </Card>
  )
}

function EvaluateResultView({ result }: { result: EvaluateResult }) {
  const allIssues = [...result.violations, ...result.warnings, ...result.suggestions]
  return (
    <div className="space-y-2 mt-2">
      <div className="flex items-center gap-2">
        {result.pass ? (
          <>
            <ShieldCheck className="w-5 h-5 text-success" />
            <span className="text-sm font-medium text-success">通过 — 未触发任何规则</span>
          </>
        ) : (
          <>
            <ShieldAlert className="w-5 h-5 text-warning" />
            <span className="text-sm font-medium text-warning">
              命中 {result.violation_count} 拦截 / {result.warning_count} 警告 / {result.suggestion_count} 建议
            </span>
          </>
        )}
      </div>
      {allIssues.length > 0 && (
        <div className="space-y-1.5">
          {allIssues.map((item, i) => (
            <div
              key={i}
              className={cn(
                'p-2 rounded-lg text-xs space-y-0.5',
                item.action === 'block' ? 'bg-destructive/10 text-destructive' :
                item.action === 'warn' ? 'bg-warning/10 text-warning' :
                'bg-info/10 text-info'
              )}
            >
              <div className="font-medium flex items-center gap-1">
                {item.action === 'block' && <AlertTriangle className="w-3 h-3" />}
                {item.action === 'warn' && <Info className="w-3 h-3" />}
                {item.name}
                <Badge variant={(actionVariants[item.action] as BadgeVariant) || 'default'} className="text-[10px] px-1 py-0">
                  {actionLabels[item.action] || item.action}
                </Badge>
              </div>
              {item.matched && <div className="opacity-80">匹配: {item.matched}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ── Rule Form ── */

function RuleForm({
  mode, initial, onSubmit, onCancel,
}: {
  mode: 'create' | 'edit'
  initial?: PlatformRule
  onSubmit: (data: Record<string, unknown>) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(initial?.name || '')
  const [layer, setLayer] = useState(initial?.layer || 'l2_keyword')
  const [platform, setPlatform] = useState(initial?.platform || 'xiaohongshu')
  const [action, setAction] = useState(initial?.action || 'warn')
  const [priority, setPriority] = useState(initial?.priority ?? 50)
  const [description, setDescription] = useState(initial?.description || '')
  const [conditionJson, setConditionJson] = useState<ConditionJson>((initial?.condition_json as ConditionJson | undefined) || { type: 'keyword' })
  const [enabled, setEnabled] = useState(initial?.enabled ?? true)

  const handleSubmit = () => {
    if (!name.trim()) return
    onSubmit({
      name: name.trim(),
      layer,
      platform,
      action,
      priority,
      description: description.trim(),
      condition_json: conditionJson as Record<string, unknown>,
      enabled,
    })
  }

  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <label className="text-sm font-medium">规则名称</label>
        <input
          type="text" placeholder="规则名称" value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-sm font-medium">平台</label>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm">
            <option value="xiaohongshu">小红书</option>
            <option value="douyin">抖音</option>
            <option value="wechat_channels">视频号</option>
            <option value="universal">通用</option>
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium">层级</label>
          <select value={layer} onChange={(e) => setLayer(e.target.value)}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm">
            <option value="l1_static">L1 法律红线</option>
            <option value="l2_keyword">L2 平台规则</option>
            <option value="l3_account_state">L3 账号策略</option>
            <option value="l4_dynamic_risk">L4 动态风控</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-sm font-medium">动作</label>
          <select value={action} onChange={(e) => setAction(e.target.value)}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm">
            <option value="block">拦截</option>
            <option value="warn">警告</option>
            <option value="suggest">建议</option>
            <option value="flag_for_review">复核</option>
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium">优先级</label>
          <input
            type="number" min={0} max={1000} value={priority}
            onChange={(e) => setPriority(Number(e.target.value))}
            className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
          />
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium">规则描述</label>
        <textarea
          value={description} onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
          placeholder="规则用途描述..."
        />
      </div>

      <div className="rounded-lg border border-border p-3 space-y-3">
        <div className="text-sm font-medium">条件配置</div>
        <ConditionBuilder value={conditionJson} onChange={setConditionJson} />
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
          className="rounded"
        />
        启用规则
      </label>

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="ghost" onClick={onCancel}>取消</Button>
        <Button onClick={handleSubmit} disabled={!name.trim()}>
          {mode === 'create' ? '创建' : '保存'}
        </Button>
      </div>
    </div>
  )
}

/* ── Detail Drawer ── */

function DetailDrawer({
  rule, onClose,
}: {
  rule: PlatformRule
  onClose: () => void
}) {
  const { fetchRuleHistory, ruleHistory, historyLoading } = usePlatformRulesStore()
  const [activeTab, setActiveTab] = useState<'info' | 'history'>('info')

  useEffect(() => {
    fetchRuleHistory(rule.id)
  }, [rule.id, fetchRuleHistory])

  return (
    <aside className="w-80 xl:w-[28rem] flex-shrink-0 border-l border-border bg-card shadow-xl flex flex-col sticky top-0 max-h-full overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="text-base font-semibold">规则详情</h3>
          <button onClick={onClose} className="p-1 hover:bg-secondary rounded">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('info')}
            className={cn('flex-1 py-2 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'info' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground')}
          >
            基本信息
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={cn('flex-1 py-2 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'history' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground')}
          >
            版本历史
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {activeTab === 'info' && (
            <>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">{rule.name}</span>
                  <Badge variant={(layerVariants[rule.layer] as BadgeVariant) || 'default'}>
                    {layerShortLabels[rule.layer] || rule.layer}
                  </Badge>
                  <Badge variant={(actionVariants[rule.action] as BadgeVariant) || 'default'}>
                    {actionLabels[rule.action] || rule.action}
                  </Badge>
                  <Badge variant={rule.enabled ? 'success' : 'default'}>
                    {rule.enabled ? '启用' : '禁用'}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">{rule.description || '无描述'}</p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg bg-secondary/30 p-3 space-y-1">
                  <div className="text-xs text-muted-foreground">平台</div>
                  <div className="font-medium">{rule.platform}</div>
                </div>
                <div className="rounded-lg bg-secondary/30 p-3 space-y-1">
                  <div className="text-xs text-muted-foreground">优先级</div>
                  <div className="font-medium">{rule.priority}</div>
                </div>
                <div className="rounded-lg bg-secondary/30 p-3 space-y-1">
                  <div className="text-xs text-muted-foreground">版本</div>
                  <div className="font-medium">v{rule.version}</div>
                </div>
                <div className="rounded-lg bg-secondary/30 p-3 space-y-1">
                  <div className="text-xs text-muted-foreground">创建者</div>
                  <div className="font-medium">{rule.created_by || '—'}</div>
                </div>
              </div>

              <div className="rounded-lg border border-border p-3 space-y-2">
                <div className="text-sm font-medium">条件配置</div>
                <pre className="text-xs bg-secondary/30 rounded p-2 overflow-auto">
                  {JSON.stringify(rule.condition_json, null, 2)}
                </pre>
              </div>

            </>
          )}

          {activeTab === 'history' && (
            <div className="space-y-2">
              {historyLoading && <div className="h-20 animate-pulse bg-secondary/50 rounded-lg" />}
              {!historyLoading && ruleHistory.length === 0 && (
                <EmptyState icon={History} title="暂无历史版本" description="规则修改后会自动保存历史" />
              )}
              {ruleHistory.map((h) => (
                <div key={h.id} className="rounded-lg border border-border p-3 space-y-1 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">v{h.version}</span>
                    <span className="text-xs text-muted-foreground">{h.changed_by || '—'}</span>
                  </div>
                  <div className="text-xs text-muted-foreground">{h.change_reason || '规则更新'}</div>
                  <div className="text-xs text-muted-foreground">
                    {h.created_at ? new Date(h.created_at).toLocaleString() : '—'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
    </aside>
  )
}

/* ── Main Page ── */

export function PlatformRulesPage() {
  const {
    rules, isLoading, error, selectedPlatform, fetchRules, createRule, updateRule, deleteRule,
  } = usePlatformRulesStore()

  const [detailRuleId, setDetailRuleId] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create')
  const [editingRule, setEditingRule] = useState<PlatformRule | undefined>()

  useEffect(() => {
    fetchRules(selectedPlatform)
  }, [selectedPlatform, fetchRules])

  usePageCopilot(
    [
      {
        id: 'rule-create',
        type: 'decision',
        title: '➕ 新建平台规则',
        description: '创建一条新的 L1-L4 风控规则',
        priority: 1,
        actions: [{ id: 'create_rule', label: '新建', variant: 'primary' }],
      },
      {
        id: 'rule-test',
        type: 'decision',
        title: '🧪 规则试跑',
        description: '输入内容并测试当前平台规则命中情况',
        priority: 2,
        actions: [{ id: 'test_rule', label: '试跑', variant: 'secondary' }],
      },
      {
        id: 'rule-toggle',
        type: 'decision',
        title: '🔁 切换首条规则',
        description: '启用/禁用列表中的第一条规则',
        priority: 3,
        actions: [{ id: 'toggle_rule', label: '切换', variant: 'secondary' }],
      },
    ],
    async (_cardId, actionId) => {
      if (actionId === 'create_rule') {
        setFormMode('create')
        setEditingRule(undefined)
        setShowForm(true)
      } else if (actionId === 'test_rule') {
        document.getElementById('rule-test-panel')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      } else if (actionId === 'toggle_rule') {
        const first = rules[0]
        if (first) {
          await updateRule(first.id, { enabled: !first.enabled })
        } else {
          alert('当前没有可切换的规则')
        }
      }
    }
  )

  const detailRule = useMemo(
    () => rules.find((r) => r.id === detailRuleId) || null,
    [rules, detailRuleId]
  )

  const openCreate = () => {
    setFormMode('create')
    setEditingRule(undefined)
    setShowForm(true)
  }

  const openEdit = (rule: PlatformRule) => {
    setFormMode('edit')
    setEditingRule(rule)
    setShowForm(true)
  }

  const handleSubmit = async (data: Record<string, unknown>) => {
    if (formMode === 'create') {
      const ok = await createRule(data)
      if (ok) setShowForm(false)
    } else if (editingRule) {
      const ok = await updateRule(editingRule.id, data)
      if (ok) {
        setShowForm(false)
        setDetailRuleId(null)
      }
    }
  }

  const toggleEnabled = async (rule: PlatformRule) => {
    await updateRule(rule.id, { enabled: !rule.enabled })
  }

  const filteredRules = useMemo(() => {
    return rules
  }, [rules])

  return (
    <div className="space-y-6">
      <PageHeader
        title="平台规则"
        subtitle="L1-L4 四层风控规则配置与管理"
        action={
          <Button onClick={openCreate}>
            <Plus className="w-4 h-4" />
            新建规则
          </Button>
        }
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {/* Main content + side panel layout */}
      <div className="flex gap-6 items-start">
        <div className="flex-1 min-w-0 space-y-6">
          {/* Platform Filter */}
          <div className="flex gap-2">
        {platforms.map((p) => {
          const Icon = p.icon
          const active = selectedPlatform === p.key
          return (
            <button
              key={p.key}
              onClick={() => usePlatformRulesStore.setState({ selectedPlatform: p.key })}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                active
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              )}
            >
              <Icon className="w-4 h-4" />
              {p.label}
            </button>
          )
        })}
      </div>

      {/* Test Run Panel */}
      <TestRunPanel />

      {/* Rule Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <h3 className="text-base font-semibold">{formMode === 'create' ? '新建规则' : '编辑规则'}</h3>
          </CardHeader>
          <CardContent>
            <RuleForm
              mode={formMode}
              initial={editingRule}
              onSubmit={handleSubmit}
              onCancel={() => setShowForm(false)}
            />
          </CardContent>
        </Card>
      )}

      {/* Rule List */}
      <Card className="min-w-0 overflow-hidden">
        <CardHeader className="flex items-center gap-2">
          <Scale className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold">规则列表</h2>
          <Badge variant="default">{filteredRules.length}</Badge>
        </CardHeader>
        <CardContent>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && filteredRules.length === 0 && (
            <EmptyState icon={Scale} title="暂无规则" description="系统将自动加载默认规则，或手动创建" />
          )}
          <div className="space-y-2">
            {filteredRules.map((rule) => (
              <div
                key={rule.id}
                className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-secondary/30 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-foreground">{rule.name}</span>
                    <Badge variant={(layerVariants[rule.layer] as BadgeVariant) || 'default'}>
                      {layerShortLabels[rule.layer] || rule.layer}
                    </Badge>
                    <Badge variant={(actionVariants[rule.action] as BadgeVariant) || 'default'}>
                      {actionLabels[rule.action] || rule.action}
                    </Badge>
                    <Badge variant={rule.enabled ? 'success' : 'default'}>
                      {rule.enabled ? '启用' : '禁用'}
                    </Badge>
                    <span className="text-xs text-muted-foreground">v{rule.version}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{formatConditionPreview(rule)}</p>
                </div>
                <div className="flex items-center gap-1 ml-3 shrink-0">
                  <button
                    onClick={() => setDetailRuleId(rule.id)}
                    className="p-1.5 hover:bg-primary/10 rounded"
                    title="详情"
                  >
                    <Eye className="w-4 h-4 text-primary" />
                  </button>
                  <button
                    onClick={() => openEdit(rule)}
                    className="p-1.5 hover:bg-primary/10 rounded"
                    title="编辑"
                  >
                    <Pencil className="w-4 h-4 text-primary" />
                  </button>
                  <button
                    onClick={() => toggleEnabled(rule)}
                    className="p-1.5 hover:bg-secondary rounded"
                    title={rule.enabled ? '禁用' : '启用'}
                  >
                    {rule.enabled ? (
                      <ToggleRight className="w-5 h-5 text-success" />
                    ) : (
                      <ToggleLeft className="w-5 h-5 text-muted-foreground" />
                    )}
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('确定删除该规则？')) deleteRule(rule.id)
                    }}
                    className="p-1.5 hover:bg-destructive/10 rounded"
                    title="删除"
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

      {/* Detail Drawer -- inline layout to avoid overlap with Copilot panel */}
      {detailRule && (
        <DetailDrawer
          rule={detailRule}
          onClose={() => setDetailRuleId(null)}
        />
      )}
    </div>
  </div>
  )
}
