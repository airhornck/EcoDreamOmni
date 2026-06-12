import { useEffect, useMemo, useState } from 'react'
import { useAccountPoolStore, type AccountEntry } from '../stores/accountPoolStore'
import { useProxyStore } from '../stores/proxyStore'
import { useTaskHubStore } from '../stores/taskHubStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge, type BadgeVariant } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { cn } from '../lib/utils'
import {
  Users,
  Plus,
  Trash2,
  X,
  Eye,
  Pencil,
  Pause,
  Play,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  UserCheck,
  BarChart3,
  Clock,
  Smartphone,
  Video,
  Tv,
  Globe,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

/* ── helpers ── */

const platformConfig: Record<string, { icon: LucideIcon; color: string; label: string }> = {
  xhs: { icon: Smartphone, color: 'bg-destructive/150 text-white', label: '小红书' },
  xiaohongshu: { icon: Smartphone, color: 'bg-destructive/150 text-white', label: '小红书' },
  douyin: { icon: Video, color: 'bg-slate-800 text-white', label: '抖音' },
  wechat_channels: { icon: Tv, color: 'bg-green-600 text-white', label: '视频号' },
}

const statusLabels: Record<string, string> = {
  active: '活跃',
  paused: '已暂停',
  suspended: '已封禁',
}

const statusVariants: Record<string, BadgeVariant> = {
  active: 'success',
  paused: 'warning',
  suspended: 'danger',
}

const riskLabels: Record<string, string> = {
  safe: '安全',
  warning: '警告',
  danger: '危险',
}

const riskVariants: Record<string, BadgeVariant> = {
  safe: 'success',
  warning: 'warning',
  danger: 'danger',
}

function PlatformIcon({ platform }: { platform: string }) {
  const c = platformConfig[platform] || platformConfig.xhs
  const Icon = c.icon
  return (
    <div
      className={cn('w-10 h-10 rounded-xl flex items-center justify-center shrink-0', c.color)}
      title={c.label}
    >
      <Icon className="w-5 h-5" />
    </div>
  )
}

function RingScore({ value = 0, size = 48, stroke = 4 }: { value?: number; size?: number; stroke?: number }) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const offset = c - (Math.min(value, 100) / 100) * c
  const color = value >= 80 ? 'text-success' : value >= 60 ? 'text-warning' : 'text-destructive'
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="currentColor"
          strokeWidth={stroke}
          fill="none"
          className="text-secondary"
        />
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
      <span className="absolute text-[10px] font-bold">{value}</span>
    </div>
  )
}

function ScoreBar({ label, value = 0 }: { label: string; value?: number }) {
  const v = Math.min(Math.max(Math.round(value), 0), 100)
  const color = v >= 80 ? 'bg-success' : v >= 60 ? 'bg-warning' : 'bg-destructive'
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-muted-foreground w-16 shrink-0 truncate">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-secondary overflow-hidden">
        <div
          className={cn('h-full rounded-full', color)}
          style={{ width: `${v}%`, transition: 'width 0.6s ease-out' }}
        />
      </div>
      <span className="text-[10px] w-6 text-right">{v}</span>
    </div>
  )
}

function WeeklyPostsChart({ data }: { data?: number[] }) {
  const values = data?.length ? data : [0, 0, 0, 0, 0, 0, 0]
  const max = Math.max(...values, 1)
  const labels = ['一', '二', '三', '四', '五', '六', '日']
  return (
    <div className="flex items-end gap-1 h-16">
      {values.map((v, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-1">
          <div
            className="w-full bg-primary rounded-sm"
            style={{ height: `${(v / max) * 100}%`, minHeight: v > 0 ? 2 : 0 }}
          />
          <span className="text-[10px] text-muted-foreground">{labels[i]}</span>
        </div>
      ))}
    </div>
  )
}

function StatCard({ label, value, icon: Icon }: { label: string; value: string | number; icon: LucideIcon }) {
  return (
    <Card className="flex items-center gap-3 p-4">
      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
        <Icon className="w-5 h-5 text-primary" />
      </div>
      <div>
        <div className="text-2xl font-bold text-foreground">{value}</div>
        <div className="text-xs text-muted-foreground">{label}</div>
      </div>
    </Card>
  )
}

/* ── page ── */

export function AccountPoolPage() {
  const {
    accounts,
    personas,
    stats,
    isLoading,
    isFormLoading,
    error,
    fetchAccounts,
    fetchPersonas,
    createAccount,
    updateAccount,
    deleteAccount,
    updateAccountStatus,
    bindPersona,
  } = useAccountPoolStore()

  const { platformSchemas, fetchPlatformSchemas } = useTaskHubStore()

  const [detailAccountId, setDetailAccountId] = useState<string | null>(null)
  const [formDrawerOpen, setFormDrawerOpen] = useState(false)
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create')
  const [editingAccountId, setEditingAccountId] = useState<string | null>(null)

  /* form state */
  const [accountId, setAccountId] = useState('')
  const [nickname, setNickname] = useState('')
  const [platform, setPlatform] = useState<string>('xiaohongshu')
  const [personaId, setPersonaId] = useState('')
  const [status, setStatus] = useState<'active' | 'paused'>('active')
  const [cookie, setCookie] = useState('')
  const [contentVertical, setContentVertical] = useState('宠物健康')
  const [lifecyclePhase, setLifecyclePhase] = useState('cold_start')
  const [proxyId, setProxyId] = useState('')
  const [autoEngagementFetch, setAutoEngagementFetch] = useState(false)

  const { proxies, fetchProxies } = useProxyStore()

  useEffect(() => {
    fetchAccounts()
    fetchProxies()
    fetchPlatformSchemas()
  }, [fetchAccounts, fetchProxies, fetchPlatformSchemas])

  useEffect(() => {
    if (formDrawerOpen) {
      fetchPersonas()
      fetchProxies()
    }
  }, [formDrawerOpen, fetchPersonas, fetchProxies])

  const detailAccount = useMemo(
    () => accounts.find((a) => a.id === detailAccountId) || null,
    [accounts, detailAccountId]
  )

  const openCreateDrawer = () => {
    setFormMode('create')
    setEditingAccountId(null)
    setAccountId('')
    setNickname('')
    setPlatform('xiaohongshu')
    setPersonaId('')
    setStatus('active')
    setCookie('')
    setContentVertical('宠物健康')
    setLifecyclePhase('cold_start')
    setProxyId('')
    setAutoEngagementFetch(false)
    setFormDrawerOpen(true)
  }

  const openEditDrawer = (account: AccountEntry) => {
    setFormMode('edit')
    setEditingAccountId(account.id)
    setAccountId(account.account_id || account.username || '')
    setNickname(account.nickname || '')
    setPlatform(account.platform)
    setPersonaId(account.persona || account.persona_id || '')
    setStatus(account.status === 'suspended' ? 'active' : (account.status as 'active' | 'paused'))
    setCookie(account.cookie || '')
    setContentVertical(account.content_vertical || '宠物健康')
    setLifecyclePhase(account.lifecycle_phase || 'cold_start')
    setProxyId(account.proxy_config?.proxy_id || '')
    setAutoEngagementFetch(account.auto_engagement_fetch || false)
    setFormDrawerOpen(true)
  }

  const closeFormDrawer = () => {
    setFormDrawerOpen(false)
    setEditingAccountId(null)
  }

  const handleFormSubmit = async () => {
    if (!accountId.trim() || !nickname.trim()) return
    const payload: Record<string, unknown> = {
      account_id: accountId.trim(),
      nickname: nickname.trim(),
      platform,
      persona: personaId || '',
      status,
      cookie: cookie || '',
      content_vertical: contentVertical || '宠物健康',
      lifecycle_phase: lifecyclePhase || 'cold_start',
      auto_engagement_fetch: autoEngagementFetch,
    }
    if (proxyId) {
      const selectedProxy = proxies.find((p) => p.id === proxyId)
      payload.proxy_config = {
        proxy_id: proxyId,
        type: selectedProxy?.protocol || 'http',
        region: selectedProxy?.region || '',
      }
    } else {
      payload.proxy_config = null
    }
    if (formMode === 'create') {
      const success = await createAccount(payload)
      if (success) closeFormDrawer()
    } else if (formMode === 'edit' && editingAccountId) {
      const success = await updateAccount(editingAccountId, payload)
      if (success) {
        closeFormDrawer()
        setDetailAccountId(null)
      }
    }
  }

  const handleToggleStatus = async (account: AccountEntry) => {
    const next = account.status === 'active' ? 'paused' : 'active'
    await updateAccountStatus(account.id, next)
  }

  const handleDelete = async (id: string) => {
    if (confirm('确定删除该账号？此操作不可撤销。')) {
      await deleteAccount(id)
      if (detailAccountId === id) setDetailAccountId(null)
    }
  }

  const handleBindPersona = async (accountId: string, pid: string) => {
    await bindPersona(accountId, pid || null)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="账号池"
        subtitle="素人矩阵管理与健康监控"
        action={
          <Button onClick={openCreateDrawer}>
            <Plus className="w-4 h-4" />
            添加账号
          </Button>
        }
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="总账号数" value={stats.total} icon={Users} />
        <StatCard label="活跃账号" value={stats.active} icon={ShieldCheck} />
        <StatCard label="平均健康分" value={stats.avg_health_score} icon={BarChart3} />
        <StatCard label="今日发布" value={`${stats.today_posts}${stats.total_quota ? '/' + stats.total_quota : ''}`} icon={Clock} />
      </div>
      {stats.quota_exceeded_count ? (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {stats.quota_exceeded_count} 个账号今日配额已用尽
        </div>
      ) : null}

      {/* Account Grid */}
      <Card>
        <CardHeader className="flex items-center gap-2">
          <Users className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold">账号列表</h2>
          <Badge variant="default">{accounts.length}</Badge>
        </CardHeader>
        <CardContent>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && accounts.length === 0 && (
            <EmptyState icon={Users} title="暂无账号" description="添加你的第一个平台账号" />
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {accounts.map((account) => (
              <div
                key={account.id}
                className="rounded-xl border border-border bg-card p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setDetailAccountId(account.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <PlatformIcon platform={account.platform} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-foreground truncate">
                          {account.username}
                        </span>
                        <Badge variant={(statusVariants[account.status] as BadgeVariant) || 'default'}>
                          {statusLabels[account.status] || account.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <Badge variant={(riskVariants[account.risk_level || 'safe'] as BadgeVariant) || 'default'}>
                          {riskLabels[account.risk_level || 'safe'] || account.risk_level}
                        </Badge>
                        {account.persona_name && (
                          <span className="text-xs text-muted-foreground flex items-center gap-1">
                            <UserCheck className="w-3 h-3" />
                            {account.persona_name}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <RingScore value={account.health_score} size={44} stroke={4} />
                </div>

                <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-lg bg-secondary/40 p-2">
                    <div className="text-sm font-semibold text-foreground">
                      {account.followers_count ?? 0}
                    </div>
                    <div className="text-[10px] text-muted-foreground">粉丝</div>
                  </div>
                  <div className="rounded-lg bg-secondary/40 p-2">
                    <div className="text-sm font-semibold text-foreground">
                      {account.posts_last_7d ?? 0}
                    </div>
                    <div className="text-[10px] text-muted-foreground">近7日</div>
                  </div>
                  <div className="rounded-lg bg-secondary/40 p-2">
                    <div className={cn('text-sm font-semibold truncate', account.quota_exceeded ? 'text-destructive' : 'text-foreground')}>
                      {account.posts_today ?? 0}/{account.daily_quota ?? '-'}
                    </div>
                    <div className="text-[10px] text-muted-foreground">今日配额</div>
                  </div>
                </div>

                <div className="mt-3 flex items-center justify-end gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setDetailAccountId(account.id)
                    }}
                    className="p-1.5 hover:bg-primary/10 rounded"
                    title="查看详情"
                  >
                    <Eye className="w-4 h-4 text-primary" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      openEditDrawer(account)
                    }}
                    className="p-1.5 hover:bg-primary/10 rounded"
                    title="编辑"
                  >
                    <Pencil className="w-4 h-4 text-primary" />
                  </button>
                  {account.status !== 'suspended' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleToggleStatus(account)
                      }}
                      className="p-1.5 hover:bg-warning/10 rounded"
                      title={account.status === 'active' ? '暂停' : '恢复'}
                    >
                      {account.status === 'active' ? (
                        <Pause className="w-4 h-4 text-warning" />
                      ) : (
                        <Play className="w-4 h-4 text-success" />
                      )}
                    </button>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(account.id)
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

      {/* Detail Drawer Backdrop */}
      {detailAccountId && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setDetailAccountId(null)}
        />
      )}

      {/* Detail Drawer */}
      <div
        className={cn(
          'fixed right-0 top-0 h-full w-96 bg-card border-l border-border shadow-xl z-50 transform transition-transform duration-300 flex flex-col',
          detailAccountId ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="text-base font-semibold">账号详情</h3>
          <button onClick={() => setDetailAccountId(null)} className="p-1 hover:bg-secondary rounded">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {detailAccount && (
            <>
              {/* Basic Info */}
              <div className="flex items-center gap-3">
                <PlatformIcon platform={detailAccount.platform} />
                <div>
                  <div className="text-sm font-semibold text-foreground">{detailAccount.username}</div>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <Badge variant={(statusVariants[detailAccount.status] as BadgeVariant) || 'default'}>
                      {statusLabels[detailAccount.status] || detailAccount.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      创建于 {new Date(detailAccount.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Health Detail */}
              <div className="rounded-lg border border-border p-4 space-y-3">
                <div className="flex items-center gap-3">
                  <RingScore value={detailAccount.health_score} size={56} stroke={5} />
                  <div className="flex-1 space-y-1.5">
                    <ScoreBar label="活跃度" value={detailAccount.health_detail?.activity_score ?? 0} />
                    <ScoreBar
                      label="内容质量"
                      value={detailAccount.health_detail?.content_quality_score ?? 0}
                    />
                    <ScoreBar
                      label="互动率"
                      value={detailAccount.health_detail?.engagement_rate ?? 0}
                    />
                    <ScoreBar
                      label="合规记录"
                      value={detailAccount.health_detail?.compliance_score ?? 0}
                    />
                  </div>
                </div>
              </div>

              {/* Daily Quota */}
              {(detailAccount.daily_quota ?? 0) > 0 && (
                <div className="rounded-lg border border-border p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">今日配额</span>
                    <Badge variant={detailAccount.quota_exceeded ? 'danger' : detailAccount.quota_utilization && detailAccount.quota_utilization >= 80 ? 'warning' : 'success'}>
                      {detailAccount.posts_today ?? 0}/{detailAccount.daily_quota} 篇
                    </Badge>
                  </div>
                  <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full transition-all',
                        detailAccount.quota_exceeded ? 'bg-destructive' : (detailAccount.quota_utilization ?? 0) >= 80 ? 'bg-warning' : 'bg-success'
                      )}
                      style={{ width: `${Math.min(detailAccount.quota_utilization ?? 0, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>已用 {detailAccount.quota_utilization ?? 0}%</span>
                    <span>剩余 {detailAccount.quota_remaining ?? 0} 篇</span>
                  </div>
                  {detailAccount.quota_exceeded && (
                    <div className="text-xs text-destructive flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      今日配额已用尽，建议切换账号或明日再发
                    </div>
                  )}
                </div>
              )}

              {/* Engagement Data Recovery */}
              <div className="rounded-lg border border-border p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium flex items-center gap-1">
                    <BarChart3 className="w-4 h-4 text-muted-foreground" />
                    自动数据回收
                  </span>
                  <Badge variant={detailAccount.auto_engagement_fetch ? 'success' : 'default'}>
                    {detailAccount.auto_engagement_fetch ? '已开启' : '已关闭'}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  {detailAccount.auto_engagement_fetch
                    ? '发布24小时后将自动抓取笔记互动数据（点赞/评论/收藏）'
                    : '默认关闭。开启后，系统将在笔记发布24小时后自动抓取互动数据用于MAPE计算。'}
                </p>
              </div>

              {/* Persona Binding */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium flex items-center gap-1">
                  <UserCheck className="w-4 h-4 text-muted-foreground" />
                  绑定 Persona
                </label>
                <select
                  value={detailAccount.persona_id || ''}
                  onChange={(e) => handleBindPersona(detailAccount.id, e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                >
                  <option value="">不绑定</option>
                  {personas.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Proxy Binding */}
              {detailAccount.proxy_config?.proxy_id && (
                <div className="space-y-1.5">
                  <label className="text-sm font-medium flex items-center gap-1">
                    <Globe className="w-4 h-4 text-muted-foreground" />
                    绑定代理
                  </label>
                  <div className="rounded-lg border border-border bg-secondary/30 p-3 text-sm">
                    {(() => {
                      const p = proxies.find((px) => px.id === detailAccount.proxy_config?.proxy_id)
                      return p ? (
                        <div className="space-y-1">
                          <div className="font-medium">{p.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {p.host}:{p.port} · {p.protocol.toUpperCase()}
                            {p.region && ` · ${p.region.toUpperCase()}`}
                          </div>
                          <Badge variant={p.health_status === 'healthy' ? 'success' : p.health_status === 'unhealthy' ? 'danger' : 'warning'}>
                            {p.health_status === 'healthy' ? '健康' : p.health_status === 'unhealthy' ? '异常' : '未知'}
                          </Badge>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">代理配置 ID: {detailAccount.proxy_config.proxy_id}</span>
                      )
                    })()}
                  </div>
                </div>
              )}

              {/* Weekly Posts */}
              <div className="space-y-2">
                <div className="text-sm font-medium flex items-center gap-1">
                  <BarChart3 className="w-4 h-4 text-muted-foreground" />
                  近7日发布趋势
                </div>
                <WeeklyPostsChart data={detailAccount.weekly_posts} />
              </div>

              {/* Violations */}
              {detailAccount.violations && detailAccount.violations.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium flex items-center gap-1 text-destructive">
                    <AlertTriangle className="w-4 h-4" />
                    违规历史
                  </div>
                  <div className="space-y-2">
                    {detailAccount.violations.map((v) => (
                      <div
                        key={v.id}
                        className="rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-xs space-y-1"
                      >
                        <div className="font-medium text-destructive">{v.rule}</div>
                        <div className="text-muted-foreground">
                          {new Date(v.occurred_at).toLocaleString()}
                        </div>
                        <Badge
                          variant={
                            v.severity === 'high'
                              ? 'danger'
                              : v.severity === 'medium'
                                ? 'warning'
                                : 'default'
                          }
                        >
                          {v.severity === 'high' ? '严重' : v.severity === 'medium' ? '中等' : '轻微'}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggestions */}
              {detailAccount.suggestions && detailAccount.suggestions.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium flex items-center gap-1 text-warning">
                    <ShieldAlert className="w-4 h-4" />
                    建议操作
                  </div>
                  <ul className="space-y-1.5">
                    {detailAccount.suggestions.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                        <span className="text-warning mt-0.5">•</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Quick Actions */}
              <div className="flex gap-2 pt-2 border-t border-border">
                <Button
                  variant="secondary"
                  className="flex-1"
                  onClick={() => {
                    setDetailAccountId(null)
                    openEditDrawer(detailAccount)
                  }}
                >
                  <Pencil className="w-4 h-4" />
                  编辑
                </Button>
                {detailAccount.status !== 'suspended' && (
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => handleToggleStatus(detailAccount)}
                  >
                    {detailAccount.status === 'active' ? (
                      <>
                        <Pause className="w-4 h-4" />
                        暂停
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        恢复
                      </>
                    )}
                  </Button>
                )}
                <Button
                  variant="danger"
                  className="flex-1"
                  onClick={() => handleDelete(detailAccount.id)}
                >
                  <Trash2 className="w-4 h-4" />
                  删除
                </Button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Form Drawer Backdrop */}
      {formDrawerOpen && (
        <div className="fixed inset-0 bg-black/50 z-40" onClick={closeFormDrawer} />
      )}

      {/* Form Drawer */}
      <div
        className={cn(
          'fixed right-0 top-0 h-full w-96 bg-card border-l border-border shadow-xl z-50 transform transition-transform duration-300 flex flex-col',
          formDrawerOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="text-base font-semibold">
            {formMode === 'create' ? '添加账号' : '编辑账号'}
          </h3>
          <button onClick={closeFormDrawer} className="p-1 hover:bg-secondary rounded">
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">平台</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            >
              <option value="">选择平台</option>
              {platformSchemas.map((s) => (
                <option key={s.platform_id} value={s.platform_id}>
                  {s.display_name || s.platform_id}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">账号 ID</label>
            <input
              type="text"
              placeholder="输入平台账号 ID（如小红书号）"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">昵称</label>
            <input
              type="text"
              placeholder="输入账号昵称"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">绑定 Persona</label>
            <select
              value={personaId}
              onChange={(e) => setPersonaId(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            >
              <option value="">不绑定</option>
              {personas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">内容垂类</label>
            <input
              type="text"
              placeholder="如：宠物健康、宠物日常"
              value={contentVertical}
              onChange={(e) => setContentVertical(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">生命周期阶段</label>
            <select
              value={lifecyclePhase}
              onChange={(e) => setLifecyclePhase(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            >
              <option value="cold_start">冷启动</option>
              <option value="growth">成长期</option>
              <option value="mature">成熟期</option>
              <option value="dormant">休眠期</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">初始状态</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as typeof status)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            >
              <option value="active">活跃</option>
              <option value="paused">已暂停</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium flex items-center gap-1">
              <Globe className="w-4 h-4 text-muted-foreground" />
              绑定代理
            </label>
            <select
              value={proxyId}
              onChange={(e) => setProxyId(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
            >
              <option value="">不绑定</option>
              {proxies.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.host}:{p.port})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium flex items-center gap-2">
              <span>自动数据回收</span>
              <span className="text-xs text-muted-foreground">(24h后自动抓取笔记互动数据)</span>
            </label>
            <div className="flex items-center gap-3 h-10 px-3 rounded-lg border border-border bg-background">
              <button
                type="button"
                onClick={() => setAutoEngagementFetch(!autoEngagementFetch)}
                className={cn(
                  'relative inline-flex h-5 w-9 items-center rounded-full transition-colors',
                  autoEngagementFetch ? 'bg-primary' : 'bg-muted-foreground/30'
                )}
              >
                <span
                  className={cn(
                    'inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform',
                    autoEngagementFetch ? 'translate-x-4.5' : 'translate-x-0.5'
                  )}
                />
              </button>
              <span className="text-sm text-muted-foreground">
                {autoEngagementFetch ? '已开启' : '已关闭（默认）'}
              </span>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Cookie</label>
            <textarea
              placeholder="粘贴完整的 Cookie 字符串"
              value={cookie}
              onChange={(e) => setCookie(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-y"
            />
          </div>
        </div>
        <div className="px-5 py-4 border-t border-border flex justify-end gap-2">
          <Button variant="ghost" onClick={closeFormDrawer}>
            取消
          </Button>
          <Button onClick={handleFormSubmit} isLoading={isFormLoading} disabled={!accountId.trim() || !nickname.trim()}>
            {formMode === 'create' ? '添加' : '保存'}
          </Button>
        </div>
      </div>
    </div>
  )
}
