import { useEffect, useState, useRef, useCallback } from 'react'
import { useDataAnalystStore } from '../stores/dataAnalystStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import {
  BarChart3,
  Upload,
  RefreshCw,
  TrendingUp,
  Target,
  Activity,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon,
  AreaChart as AreaChartIcon,
  Award,
  Users,
  FileText,
  Download,
  Eye,
  ChevronUp,
  ChevronDown,
  CheckCircle2,

  XCircle,
  Clock,
  Filter,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  BarChart,
  Bar,
  AreaChart,
  Area,
} from 'recharts'

const PLATFORM_COLORS: Record<string, string> = {
  xiaohongshu: '#ff2442',
  douyin: '#1c1c1c',
  videoChannel: '#07c160',
  total: '#3b82f6',
}

const PLATFORM_LABELS: Record<string, string> = {
  xiaohongshu: '小红书',
  douyin: '抖音',
  videoChannel: '视频号',
  total: '全部',
}

function StatChange({ value }: { value: number }) {
  const isPositive = value >= 0
  return (
    <div className={`flex items-center gap-0.5 text-xs font-medium ${isPositive ? 'text-success' : 'text-red-600'}`}>
      {isPositive ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      {isPositive ? '+' : ''}{value.toFixed(1)}%
    </div>
  )
}

function CalibrationBadge({ status }: { status: string }) {
  if (status === 'success')
    return <Badge variant="success"><CheckCircle2 className="w-3 h-3 mr-1" />成功</Badge>
  if (status === 'running')
    return <Badge variant="info"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />运行中</Badge>
  if (status === 'failed')
    return <Badge variant="danger"><XCircle className="w-3 h-3 mr-1" />失败</Badge>
  return <Badge variant="default"><Clock className="w-3 h-3 mr-1" />未校准</Badge>
}

function ImportStatusBadge({ status }: { status: string }) {
  if (status === 'success')
    return <Badge variant="success">成功</Badge>
  if (status === 'partial')
    return <Badge variant="warning">部分</Badge>
  return <Badge variant="danger">失败</Badge>
}

function formatDate(v: string) {
  return new Date(v).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function formatDateTime(v: string) {
  return new Date(v).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function DataAnalystPage() {
  const {
    dashboard,
    publishTrend,
    platformDistribution,
    engagementDistribution,
    mapeTrend,
    contentRanking,
    accountComparison,
    reportList,
    calibrationStatus,
    importHistory,
    isLoading,
    error,
    fetchDashboard,
    fetchPublishTrend,
    fetchPlatformDistribution,
    fetchEngagementDistribution,
    fetchMapeTrend,
    fetchContentRanking,
    fetchAccountComparison,
    fetchReportList,
    fetchCalibrationStatus,
    fetchImportHistory,
    createReport,
    triggerCalibrate,
    clearError,
  } = useDataAnalystStore()

  const [contentId, setContentId] = useState('')
  const [uploading, setUploading] = useState(false)
  const [selectedPlatform, setSelectedPlatform] = useState<string>('total')
  const fileRef = useRef<HTMLInputElement>(null)

  const loadAll = useCallback(() => {
    fetchDashboard()
    fetchPublishTrend()
    fetchPlatformDistribution()
    fetchEngagementDistribution()
    fetchMapeTrend()
    fetchContentRanking()
    fetchAccountComparison()
    fetchReportList()
    fetchCalibrationStatus()
    fetchImportHistory()
  }, [
    fetchDashboard,
    fetchPublishTrend,
    fetchPlatformDistribution,
    fetchEngagementDistribution,
    fetchMapeTrend,
    fetchContentRanking,
    fetchAccountComparison,
    fetchReportList,
    fetchCalibrationStatus,
    fetchImportHistory,
  ])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const handleCsvUpload = async () => {
    if (!fileRef.current?.files?.length) return
    setUploading(true)
    const formData = new FormData()
    formData.append('file', fileRef.current.files[0])
    if (contentId) formData.append('content_id', contentId)
    await createReport(contentId, formData)
    setUploading(false)
    if (fileRef.current) fileRef.current.value = ''
  }

  const trendData = publishTrend.map((d) => ({
    ...d,
    value: selectedPlatform === 'total' ? d.total : (d as unknown as Record<string, number>)[selectedPlatform] ?? 0,
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="数据报表"
        subtitle="24h 战报分析、归因分析与模型校准"
        action={
          <Button variant="secondary" onClick={() => loadAll()}>
            <RefreshCw className="w-4 h-4" />
            刷新
          </Button>
        }
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={clearError} className="text-sm hover:underline">清除</button>
        </div>
      )}

      {/* ─── 1. 顶部核心指标 ─── */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">总发布</span>
              </div>
              <p className="text-2xl font-bold text-foreground">{dashboard.totalPublished}</p>
              {dashboard.totalPublishedChange !== undefined && (
                <StatChange value={dashboard.totalPublishedChange} />
              )}
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-success" />
                <span className="text-xs text-muted-foreground">平均覆盖率</span>
              </div>
              <p className="text-2xl font-bold text-foreground">{((dashboard.avgCoverage ?? 0) * 100).toFixed(1)}%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-warning" />
                <span className="text-xs text-muted-foreground">平均MAPE</span>
              </div>
              <p className="text-2xl font-bold text-foreground">{((dashboard.avgMape ?? 0) * 100).toFixed(1)}%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4 text-info" />
                <span className="text-xs text-muted-foreground">平均点赞</span>
              </div>
              <p className="text-2xl font-bold text-foreground">{(dashboard.avgLikes ?? 0).toFixed(0)}</p>
              {dashboard.avgLikesChange !== undefined && (
                <StatChange value={dashboard.avgLikesChange} />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ─── 2. 数据可视化图表区（双栏） ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左栏 */}
        <div className="space-y-6">
          {/* 近30日发布趋势 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <LineChartIcon className="w-4 h-4 text-primary" />
                  <h3 className="text-base font-semibold text-foreground">近30日发布趋势</h3>
                </div>
                <div className="flex items-center gap-1">
                  <Filter className="w-3 h-3 text-muted-foreground" />
                  {(['total', 'xiaohongshu', 'douyin', 'videoChannel'] as const).map((p) => (
                    <button
                      key={p}
                      onClick={() => setSelectedPlatform(p)}
                      className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                        selectedPlatform === p
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                      }`}
                    >
                      {PLATFORM_LABELS[p]}
                    </button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {publishTrend.length === 0 ? (
                <EmptyState icon={LineChartIcon} title="暂无趋势数据" description="数据导入后将展示发布趋势" />
              ) : (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                        tickFormatter={formatDate}
                      />
                      <YAxis tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="value"
                        name="发布量"
                        stroke={PLATFORM_COLORS[selectedPlatform]}
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 平台分布饼图 */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <PieChartIcon className="w-4 h-4 text-primary" />
                <h3 className="text-base font-semibold text-foreground">平台分布</h3>
              </div>
            </CardHeader>
            <CardContent>
              {platformDistribution.length === 0 ? (
                <EmptyState icon={PieChartIcon} title="暂无平台数据" description="数据导入后将展示平台分布" />
              ) : (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={platformDistribution}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={4}
                        dataKey="value"
                        nameKey="name"
                      >
                        {platformDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                        formatter={(value: unknown, name: unknown) => [`${value}`, String(name)]}
                      />
                      <Legend wrapperStyle={{ fontSize: '12px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 右栏 */}
        <div className="space-y-6">
          {/* 互动量分布 */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                <h3 className="text-base font-semibold text-foreground">互动量分布</h3>
              </div>
            </CardHeader>
            <CardContent>
              {engagementDistribution.length === 0 ? (
                <EmptyState icon={BarChart3} title="暂无互动数据" description="数据导入后将展示互动量分布" />
              ) : (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={engagementDistribution} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis
                        dataKey="type"
                        tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                      />
                      <YAxis tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '12px' }} />
                      <Bar dataKey="likes" name="点赞" fill="#22c55e" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="comments" name="评论" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="saves" name="收藏" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>

          {/* MAPE趋势 */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <AreaChartIcon className="w-4 h-4 text-primary" />
                <h3 className="text-base font-semibold text-foreground">MAPE趋势</h3>
              </div>
            </CardHeader>
            <CardContent>
              {mapeTrend.length === 0 ? (
                <EmptyState icon={AreaChartIcon} title="暂无MAPE数据" description="预测模型运行后将展示MAPE趋势" />
              ) : (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={mapeTrend} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                      <defs>
                        <linearGradient id="mapeGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                        tickFormatter={formatDate}
                      />
                      <YAxis
                        tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                        tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                        formatter={(value: unknown) => [`${(Number(value) * 100).toFixed(1)}%`, 'MAPE']}
                      />
                      <Area
                        type="monotone"
                        dataKey="mape"
                        name="MAPE"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        fill="url(#mapeGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* ─── 3. 内容表现排行榜 ─── */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Award className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold text-foreground">内容表现排行榜</h3>
          </div>
        </CardHeader>
        <CardContent>
          {contentRanking.length === 0 ? (
            <EmptyState icon={Award} title="暂无排行数据" description="数据导入后将展示内容表现排行榜" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="text-left font-medium px-3 py-2 w-12">排名</th>
                    <th className="text-left font-medium px-3 py-2">内容标题</th>
                    <th className="text-left font-medium px-3 py-2">平台</th>
                    <th className="text-right font-medium px-3 py-2">点赞</th>
                    <th className="text-right font-medium px-3 py-2">评论</th>
                    <th className="text-right font-medium px-3 py-2">收藏</th>
                    <th className="text-right font-medium px-3 py-2">覆盖率</th>
                    <th className="text-right font-medium px-3 py-2">MAPE</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {contentRanking.map((item) => (
                    <tr key={item.id} className="hover:bg-muted/30 transition-colors cursor-pointer">
                      <td className="px-3 py-2">
                        {item.rank <= 3 ? (
                          <Badge variant={item.rank === 1 ? 'warning' : item.rank === 2 ? 'primary' : 'info'}>
                            {item.rank}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground px-2">{item.rank}</span>
                        )}
                      </td>
                      <td className="px-3 py-2 font-medium text-foreground truncate max-w-[200px]">{item.title}</td>
                      <td className="px-3 py-2">
                        <span className="text-xs text-muted-foreground">
                          {PLATFORM_LABELS[item.platform] || item.platform}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-right">{(item.likes ?? 0).toLocaleString()}</td>
                      <td className="px-3 py-2 text-right">{(item.comments ?? 0).toLocaleString()}</td>
                      <td className="px-3 py-2 text-right">{(item.saves ?? 0).toLocaleString()}</td>
                      <td className="px-3 py-2 text-right">{((item.coverage ?? 0) * 100).toFixed(1)}%</td>
                      <td className="px-3 py-2 text-right">{((item.mape ?? 0) * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ─── 4. 账号表现对比 ─── */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold text-foreground">账号表现对比</h3>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {accountComparison.length === 0 ? (
            <EmptyState icon={Users} title="暂无账号数据" description="数据导入后将展示账号表现对比" />
          ) : (
            <>
              {/* 横向柱状图 */}
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={accountComparison}
                    layout="vertical"
                    margin={{ top: 5, right: 10, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
                    <XAxis
                      type="number"
                      tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                      width={80}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="avgLikes" name="平均点赞" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* 账号对比表格 */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-muted-foreground">
                      <th className="text-left font-medium px-3 py-2">账号</th>
                      <th className="text-left font-medium px-3 py-2">平台</th>
                      <th className="text-right font-medium px-3 py-2">发布数</th>
                      <th className="text-right font-medium px-3 py-2">平均点赞</th>
                      <th className="text-right font-medium px-3 py-2">健康分</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {accountComparison.map((item) => (
                      <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                        <td className="px-3 py-2 font-medium text-foreground">{item.name}</td>
                        <td className="px-3 py-2 text-xs text-muted-foreground">
                          {PLATFORM_LABELS[item.platform] || item.platform}
                        </td>
                        <td className="px-3 py-2 text-right">{item.publishCount}</td>
                        <td className="px-3 py-2 text-right">{(item.avgLikes ?? 0).toLocaleString()}</td>
                        <td className="px-3 py-2 text-right">
                          <span
                            className={`font-medium ${
                              item.healthScore >= 80
                                ? 'text-success'
                                : item.healthScore >= 60
                                ? 'text-warning'
                                : 'text-red-600'
                            }`}
                          >
                            {item.healthScore}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* ─── 5. CSV导入 + 导入历史 ─── */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Upload className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold text-foreground">导入实际互动数据</h3>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-xs text-muted-foreground">
            上传 CSV 文件（含 content_id, likes, comments, saves 列），系统将自动计算区间覆盖率与 MAPE。
          </p>
          <div className="flex gap-3 flex-wrap">
            <input
              type="text"
              placeholder="内容ID（可选）"
              value={contentId}
              onChange={(e) => setContentId(e.target.value)}
              className="h-10 px-3 rounded-lg border border-border bg-background text-sm w-48"
            />
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              className="flex-1 min-w-[200px] h-10 px-3 rounded-lg border border-border bg-background text-sm file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-primary file:text-primary-foreground file:text-xs"
            />
            <Button onClick={handleCsvUpload} isLoading={uploading}>
              <Upload className="w-4 h-4" />
              导入
            </Button>
          </div>

          {/* 导入历史 */}
          {importHistory.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-foreground mb-2">导入历史</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-muted-foreground">
                      <th className="text-left font-medium px-3 py-2">文件名</th>
                      <th className="text-right font-medium px-3 py-2">行数</th>
                      <th className="text-left font-medium px-3 py-2">状态</th>
                      <th className="text-right font-medium px-3 py-2">导入时间</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {importHistory.map((item) => (
                      <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                        <td className="px-3 py-2 font-medium text-foreground">{item.filename}</td>
                        <td className="px-3 py-2 text-right">{item.rows}</td>
                        <td className="px-3 py-2">
                          <ImportStatusBadge status={item.status} />
                        </td>
                        <td className="px-3 py-2 text-right text-xs text-muted-foreground">
                          {formatDateTime(item.importedAt)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ─── 6. 模型校准 ─── */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold text-foreground">模型校准</h3>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 rounded-lg border border-border bg-secondary/20 flex-wrap gap-3">
            <div>
              <p className="text-sm font-medium text-foreground">触发模型校准检查</p>
              <p className="text-xs text-muted-foreground mt-1">
                系统将检查 MAPE/漂移，超阈值则写入「待重训」队列（异步 Celery 任务）
              </p>
              {calibrationStatus && (
                <div className="flex items-center gap-3 mt-2 flex-wrap">
                  <CalibrationBadge status={calibrationStatus.status} />
                  {calibrationStatus.lastCalibratedAt && (
                    <span className="text-xs text-muted-foreground">
                      上次校准：{formatDateTime(calibrationStatus.lastCalibratedAt)}
                    </span>
                  )}
                  {calibrationStatus.message && (
                    <span className="text-xs text-muted-foreground">{calibrationStatus.message}</span>
                  )}
                </div>
              )}
            </div>
            <Button variant="secondary" onClick={() => triggerCalibrate()}>
              <RefreshCw className="w-4 h-4" />
              触发校准
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ─── 7. 报表列表 ─── */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary" />
            <h3 className="text-base font-semibold text-foreground">报表列表</h3>
          </div>
        </CardHeader>
        <CardContent>
          {reportList.length === 0 ? (
            <EmptyState icon={FileText} title="暂无报表" description="生成或导入数据后将展示报表列表" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="text-left font-medium px-3 py-2">报告名称</th>
                    <th className="text-left font-medium px-3 py-2">数据周期</th>
                    <th className="text-right font-medium px-3 py-2">生成时间</th>
                    <th className="text-right font-medium px-3 py-2">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {reportList.map((item) => (
                    <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-3 py-2 font-medium text-foreground">{item.name}</td>
                      <td className="px-3 py-2 text-xs text-muted-foreground">{item.period}</td>
                      <td className="px-3 py-2 text-right text-xs text-muted-foreground">
                        {formatDateTime(item.createdAt)}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button size="sm" variant="outline">
                            <Eye className="w-3 h-3" />
                            查看
                          </Button>
                          <Button size="sm" variant="outline">
                            <Download className="w-3 h-3" />
                            下载
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {!dashboard && !isLoading && (
        <EmptyState icon={BarChart3} title="暂无数据" description="导入数据后将展示分析报表" />
      )}
    </div>
  )
}
