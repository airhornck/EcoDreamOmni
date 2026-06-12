import { useEffect, useMemo, useState } from 'react'
import { usePredictionsStore } from '../stores/predictionsStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import {
  BarChart3,
  Sparkles,
  Activity,
  History,
  Layers,
  Target,
  TrendingUp,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from 'recharts'

type Tab = 'single' | 'batch' | 'history'

const tabs: { key: Tab; label: string }[] = [
  { key: 'single', label: '单条预测' },
  { key: 'batch', label: '批量预测' },
  { key: 'history', label: '预测历史' },
]

function StatCard({ label, value, icon: Icon }: { label: string; value: string; icon: React.ElementType }) {
  return (
    <Card className="flex items-center gap-4 p-4">
      <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
        <Icon className="w-5 h-5 text-primary" />
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-lg font-bold text-foreground">{value}</p>
      </div>
    </Card>
  )
}

function ConfidenceBar({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
        <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs font-medium w-10 text-right">{value}%</span>
    </div>
  )
}

export function PredictionsPage() {
  const {
    current,
    predictions,
    batchResults,
    stats,
    accuracyData,
    accounts,
    isLoading,
    error,
    createPrediction,
    createBatchPredictions,
    fetchPredictions,
    fetchStats,
    fetchAccuracy,
    fetchAccounts,
  } = usePredictionsStore()

  const [activeTab, setActiveTab] = useState<Tab>('single')
  const [contentText, setContentText] = useState('')
  const [tags, setTags] = useState('')
  const [accountId, setAccountId] = useState('')
  const [batchText, setBatchText] = useState('')
  const [expandedHistory, setExpandedHistory] = useState<string | null>(null)

  useEffect(() => {
    fetchStats()
    fetchAccuracy()
    fetchAccounts()
  }, [fetchStats, fetchAccuracy, fetchAccounts])

  useEffect(() => {
    if (activeTab === 'history') {
      fetchPredictions()
    }
  }, [activeTab, fetchPredictions])

  const handlePredict = async () => {
    if (!contentText.trim()) return
    await createPrediction(contentText, tags.split(',').map((t) => t.trim()).filter(Boolean), accountId || undefined)
  }

  const handleBatchPredict = async () => {
    const items = batchText.split('\n').map((t) => t.trim()).filter(Boolean)
    if (items.length === 0) return
    await createBatchPredictions(items, tags.split(',').map((t) => t.trim()).filter(Boolean), accountId || undefined)
  }

  const formatNumber = (n: number) => n.toLocaleString('zh-CN')

  const accuracyLineData = useMemo(() => accuracyData?.daily ?? [], [accuracyData])
  const accuracyBarData = useMemo(() => {
    const platform = (accuracyData?.byPlatform ?? []).map((d) => ({ name: d.platform, value: d.accuracy }))
    const type = (accuracyData?.byContentType ?? []).map((d) => ({ name: d.type, value: d.accuracy }))
    if (platform.length > 0) return platform
    return type
  }, [accuracyData])

  const accuracyBarKeys = useMemo(() => {
    if ((accuracyData?.byPlatform ?? []).length > 0) return ['value']
    return ['value']
  }, [accuracyData])

  return (
    <div className="space-y-6">
      <PageHeader
        title="互动预演"
        subtitle="基于内容与账号特征预测互动量区间（点赞/评论/收藏）"
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {/* 顶部统计栏 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="总预测次数" value={String(stats?.total ?? 0)} icon={BarChart3} />
        <StatCard label="今日预测数" value={String(stats?.today ?? 0)} icon={Activity} />
        <StatCard label="平均置信度" value={`${Math.round(stats?.avgConfidence ?? 0)}%`} icon={Target} />
        <StatCard label="近7日命中率" value={`${(stats?.weekAccuracy ?? 0).toFixed(1)}%`} icon={TrendingUp} />
      </div>

      {/* Tab 切换 */}
      <div className="flex items-center gap-1 p-1 rounded-lg bg-secondary/50 w-fit">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === t.key ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* 单条预测 */}
      {activeTab === 'single' && (
        <>
          <Card>
            <CardHeader className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              <h3 className="text-base font-semibold">内容互动预测</h3>
            </CardHeader>
            <CardContent className="space-y-3">
              <textarea
                placeholder="粘贴内容正文..."
                value={contentText}
                onChange={(e) => setContentText(e.target.value)}
                rows={5}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
              />
              <input
                type="text"
                placeholder="标签（逗号分隔，可选）"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
              {accounts.length > 0 && (
                <select
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                >
                  <option value="">选择账号（可选）</option>
                  {accounts.map((acc) => (
                    <option key={acc.id} value={acc.id}>
                      {acc.name} ({acc.platform})
                    </option>
                  ))}
                </select>
              )}
              <div className="flex justify-end">
                <Button onClick={handlePredict} isLoading={isLoading}>
                  <BarChart3 className="w-4 h-4" />
                  开始预测
                </Button>
              </div>
            </CardContent>
          </Card>

          {current && (
            <Card>
              <CardHeader className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                <h3 className="text-base font-semibold">预测结果</h3>
                <Badge variant="info">{current.interval_mode === 'prior' ? '参考区间' : '拟合区间'}</Badge>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg border border-border bg-secondary/20 text-center">
                    <p className="text-xs text-muted-foreground mb-1">点赞</p>
                    <p className="text-2xl font-bold text-foreground">
                      {formatNumber(current.likes?.lower ?? 0)}–{formatNumber(current.likes?.upper ?? 0)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">中位数 {formatNumber(current.likes?.median ?? 0)}</p>
                  </div>
                  <div className="p-4 rounded-lg border border-border bg-secondary/20 text-center">
                    <p className="text-xs text-muted-foreground mb-1">评论</p>
                    <p className="text-2xl font-bold text-foreground">
                      {formatNumber(current.comments?.lower ?? 0)}–{formatNumber(current.comments?.upper ?? 0)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">中位数 {formatNumber(current.comments?.median ?? 0)}</p>
                  </div>
                  <div className="p-4 rounded-lg border border-border bg-secondary/20 text-center">
                    <p className="text-xs text-muted-foreground mb-1">收藏</p>
                    <p className="text-2xl font-bold text-foreground">
                      {formatNumber(current.saves?.lower ?? 0)}–{formatNumber(current.saves?.upper ?? 0)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">中位数 {formatNumber(current.saves?.median ?? 0)}</p>
                  </div>
                </div>
                {current.confidence !== undefined && (
                  <div className="mt-4">
                    <span className="text-xs text-muted-foreground mb-1 block">置信度</span>
                    <ConfidenceBar value={current.confidence} />
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {!current && !isLoading && (
            <EmptyState icon={BarChart3} title="暂无预测结果" description="输入内容后点击「开始预测」获取互动量区间" />
          )}
        </>
      )}

      {/* 批量预测 */}
      {activeTab === 'batch' && (
        <>
          <Card>
            <CardHeader className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-primary" />
              <h3 className="text-base font-semibold">批量内容预测</h3>
            </CardHeader>
            <CardContent className="space-y-3">
              <textarea
                placeholder="每行输入一个内容主题..."
                value={batchText}
                onChange={(e) => setBatchText(e.target.value)}
                rows={8}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-none"
              />
              <input
                type="text"
                placeholder="标签（逗号分隔，可选）"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
              />
              {accounts.length > 0 && (
                <select
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
                >
                  <option value="">选择账号（可选）</option>
                  {accounts.map((acc) => (
                    <option key={acc.id} value={acc.id}>
                      {acc.name} ({acc.platform})
                    </option>
                  ))}
                </select>
              )}
              <div className="flex justify-end">
                <Button onClick={handleBatchPredict} isLoading={isLoading}>
                  <BarChart3 className="w-4 h-4" />
                  批量预测
                </Button>
              </div>
            </CardContent>
          </Card>

          {batchResults.length > 0 && (
            <Card>
              <CardHeader className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                <h3 className="text-base font-semibold">批量预测结果</h3>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th className="text-left py-2 px-2 font-medium">内容摘要</th>
                        <th className="text-left py-2 px-2 font-medium">点赞区间</th>
                        <th className="text-left py-2 px-2 font-medium">置信度</th>
                      </tr>
                    </thead>
                    <tbody>
                      {batchResults.map((item) => (
                        <tr key={item.id} className="border-b border-border/50 hover:bg-secondary/20">
                          <td className="py-2 px-2 max-w-xs truncate">{item.content_summary}</td>
                          <td className="py-2 px-2 whitespace-nowrap">
                            {formatNumber(item.likes?.lower ?? 0)}–{formatNumber(item.likes?.upper ?? 0)}
                          </td>
                          <td className="py-2 px-2 w-40">
                            <ConfidenceBar value={item.confidence} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {batchResults.length === 0 && !isLoading && (
            <EmptyState icon={Layers} title="暂无批量预测结果" description="输入多个内容主题后点击「批量预测」" />
          )}
        </>
      )}

      {/* 预测历史 */}
      {activeTab === 'history' && (
        <>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && predictions.length === 0 && (
            <EmptyState icon={History} title="暂无预测历史" description="进行预测后将在此展示历史记录" />
          )}
          <div className="space-y-3">
            {predictions.map((p) => (
              <Card key={p.id} className="overflow-hidden">
                <div
                  className="p-4 flex items-center justify-between cursor-pointer hover:bg-secondary/20 transition-colors"
                  onClick={() => setExpandedHistory(expandedHistory === p.id ? null : p.id)}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <History className="w-4 h-4 text-muted-foreground shrink-0" />
                    <span className="text-sm font-medium truncate">
                      {p.content_summary || contentText.slice(0, 40) || '未命名内容'}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs text-muted-foreground">
                      {new Date(p.created_at).toLocaleString('zh-CN')}
                    </span>
                    <Badge variant="info">{Math.round(p.confidence)}%</Badge>
                    {expandedHistory === p.id ? (
                      <ChevronUp className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    )}
                  </div>
                </div>
                {expandedHistory === p.id && (
                  <div className="px-4 pb-4 border-t border-border">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                      <div className="p-3 rounded-lg border border-border bg-secondary/20 text-center">
                        <p className="text-xs text-muted-foreground mb-1">点赞</p>
                        <p className="text-lg font-bold">
                          {formatNumber(p.likes?.lower ?? 0)}–{formatNumber(p.likes?.upper ?? 0)}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">中位数 {formatNumber(p.likes?.median ?? 0)}</p>
                      </div>
                      <div className="p-3 rounded-lg border border-border bg-secondary/20 text-center">
                        <p className="text-xs text-muted-foreground mb-1">评论</p>
                        <p className="text-lg font-bold">
                          {formatNumber(p.comments?.lower ?? 0)}–{formatNumber(p.comments?.upper ?? 0)}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          中位数 {formatNumber(p.comments?.median ?? 0)}
                        </p>
                      </div>
                      <div className="p-3 rounded-lg border border-border bg-secondary/20 text-center">
                        <p className="text-xs text-muted-foreground mb-1">收藏</p>
                        <p className="text-lg font-bold">
                          {formatNumber(p.saves?.lower ?? 0)}–{formatNumber(p.saves?.upper ?? 0)}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">中位数 {formatNumber(p.saves?.median ?? 0)}</p>
                      </div>
                    </div>
                    <div className="mt-3">
                      <ConfidenceBar value={p.confidence} />
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </>
      )}

      {/* 命中率追踪 */}
      <div className="space-y-4 pt-2">
        <h3 className="text-base font-semibold flex items-center gap-2">
          <Target className="w-4 h-4 text-primary" />
          命中率追踪
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <h4 className="text-sm font-medium">近30日命中率趋势</h4>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={accuracyLineData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} unit="%" />
                    <Tooltip formatter={(v: unknown) => [`${v}%`, '命中率']} />
                    <Line
                      type="monotone"
                      dataKey="accuracy"
                      stroke="#8884d8"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      name="命中率"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <h4 className="text-sm font-medium">命中率对比</h4>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={accuracyBarData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} unit="%" />
                    <Tooltip formatter={(v: unknown) => [`${v}%`, '命中率']} />
                    <Legend />
                    {accuracyBarKeys.map((key, idx) => (
                      <Bar key={key} dataKey={key} fill={idx === 0 ? '#82ca9d' : '#8884d8'} name={key} radius={[4, 4, 0, 0]} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
