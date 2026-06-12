import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTrendScoutStore } from '../stores/trendScoutStore'
import { PageHeader } from '../components/common/PageHeader'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import {
  TrendingUp,
  Search,
  Wand2,
  FileText,
  Lightbulb,
  Flame,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
  XCircle,
  CheckCircle2,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  ExternalLink,
  Tag,
} from 'lucide-react'

type Tab = 'reports' | 'topics' | 'hot'

const tabs: { key: Tab; label: string }[] = [
  { key: 'reports', label: '趋势报告' },
  { key: 'topics', label: '选题库' },
  { key: 'hot', label: '热搜监控' },
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

function TrendIcon({ trend }: { trend: 'up' | 'down' | 'stable' }) {
  if (trend === 'up') return <ArrowUpRight className="w-3 h-3 text-red-500" />
  if (trend === 'down') return <ArrowDownRight className="w-3 h-3 text-green-500" />
  return <Minus className="w-3 h-3 text-muted-foreground" />
}

function HotTag({ keyword, onClick }: { keyword: { word: string; heat: number; trend: 'up' | 'down' | 'stable' }; onClick: () => void }) {
  const sizeClass =
    keyword.heat >= 90 ? 'text-2xl font-bold' :
    keyword.heat >= 70 ? 'text-xl font-semibold' :
    keyword.heat >= 50 ? 'text-lg font-medium' :
    keyword.heat >= 30 ? 'text-base' :
    'text-sm'

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full border border-border hover:border-primary hover:bg-primary/5 transition-colors ${sizeClass}`}
    >
      <span>{keyword.word}</span>
      <TrendIcon trend={keyword.trend} />
      <span className="text-xs text-muted-foreground">{keyword.heat}</span>
    </button>
  )
}

export function TrendScoutPage() {
  const navigate = useNavigate()
  const {
    reports,
    topics,
    hotKeywords,
    stats,
    isLoading,
    error,
    fetchReports,
    createReport,
    fetchTopics,
    updateTopic,
    deleteTopic,
    fetchHotKeywords,
    createTopicFromReport,
    fetchStats,
  } = useTrendScoutStore()

  const [activeTab, setActiveTab] = useState<Tab>('reports')
  const [query, setQuery] = useState('')
  const [stageFilter, setStageFilter] = useState('')
  const [creating, setCreating] = useState(false)
  const [expandedReport, setExpandedReport] = useState<string | null>(null)
  useEffect(() => {
    fetchReports()
    fetchStats()
  }, [fetchReports, fetchStats])

  useEffect(() => {
    if (activeTab === 'topics') fetchTopics()
    if (activeTab === 'hot') fetchHotKeywords()
  }, [activeTab, fetchTopics, fetchHotKeywords])

  const handleCreate = async () => {
    if (!query.trim()) return
    setCreating(true)
    await createReport(query, stageFilter || undefined)
    setCreating(false)
    setQuery('')
  }

  const handleCreateFromHot = async (word: string) => {
    setActiveTab('reports')
    setQuery(word)
    await createReport(word)
  }

  const handleCreateTopicFromReport = async (reportId: string, title: string) => {
    await createTopicFromReport(reportId, title)
  }

  const statusBadge = (status: string) => {
    switch (status) {
      case 'adopted':
        return <Badge variant="success">已采用</Badge>
      case 'abandoned':
        return <Badge variant="default">已放弃</Badge>
      default:
        return <Badge variant="warning">待采用</Badge>
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="趋势侦察"
        subtitle="热点情报洞察与选题库管理"
        action={
          <Button onClick={() => fetchReports()}>
            <RefreshCw className="w-4 h-4" />
            刷新
          </Button>
        }
      />

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
      )}

      {/* 顶部统计栏 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="总报告数" value={String(stats?.totalReports ?? 0)} icon={FileText} />
        <StatCard label="本周新增报告" value={String(stats?.weekReports ?? 0)} icon={TrendingUp} />
        <StatCard label="热门话题数" value={String(stats?.hotTopics ?? 0)} icon={Flame} />
        <StatCard label="已采纳选题" value={String(stats?.adoptedTopics ?? 0)} icon={CheckCircle2} />
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

      {/* 趋势报告 */}
      {activeTab === 'reports' && (
        <>
          <Card>
            <CardHeader className="flex items-center gap-2">
              <Search className="w-4 h-4 text-primary" />
              <h3 className="text-base font-semibold">创建趋势报告</h3>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-3 flex-wrap">
                <input
                  type="text"
                  placeholder="输入关键词或话题..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="flex-1 min-w-[200px] h-10 px-3 rounded-lg border border-border bg-background text-sm"
                />
                <select
                  value={stageFilter}
                  onChange={(e) => setStageFilter(e.target.value)}
                  className="h-10 px-3 rounded-lg border border-border bg-background text-sm"
                >
                  <option value="">全部阶段</option>
                  <option value="AWARENESS">认知期</option>
                  <option value="INTEREST">兴趣期</option>
                  <option value="PURCHASE">购买期</option>
                  <option value="LOYALTY">忠诚期</option>
                </select>
                <Button onClick={handleCreate} isLoading={creating}>
                  <Wand2 className="w-4 h-4" />
                  生成报告
                </Button>
              </div>
            </CardContent>
          </Card>

          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && reports.length === 0 && (
            <EmptyState icon={TrendingUp} title="暂无趋势报告" description="输入关键词生成你的第一份趋势报告" />
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reports.map((report) => (
              <Card key={report.id} className="overflow-hidden">
                <div className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="text-sm font-medium text-foreground truncate">{report.query}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        {report.stage_filter && <Badge variant="info">{report.stage_filter}</Badge>}
                        <span className="text-xs text-muted-foreground">
                          {new Date(report.crawl_time).toLocaleString('zh-CN')}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant="default">{report.results?.length ?? 0} 条</Badge>
                      <button
                        onClick={() => setExpandedReport(expandedReport === report.id ? null : report.id)}
                        className="p-1 rounded hover:bg-secondary"
                      >
                        {expandedReport === report.id ? (
                          <ChevronUp className="w-4 h-4 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-muted-foreground" />
                        )}
                      </button>
                    </div>
                  </div>

                  {expandedReport === report.id && (
                    <div className="mt-4 border-t border-border pt-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-medium text-muted-foreground">TOP10 结果</h4>
                      </div>
                      {report.results && report.results.length > 0 ? (
                        <div className="space-y-2">
                          {report.results.slice(0, 10).map((item) => (
                            <div
                              key={item.rank}
                              className="flex items-center gap-3 p-2 rounded bg-secondary/20 text-sm"
                            >
                              <span className="text-xs font-bold text-muted-foreground w-5 shrink-0">{item.rank}</span>
                              <span className="flex-1 truncate">{item.title}</span>
                              {item.engagement_hint && (
                                <Badge variant="default">{item.engagement_hint}</Badge>
                              )}
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleCreateTopicFromReport(report.id, item.title)}
                                title="加入选题库"
                              >
                                <Plus className="w-3 h-3" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <EmptyState icon={Search} title="暂无结果" description="该报告未返回任何结果" />
                      )}
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* 选题库 */}
      {activeTab === 'topics' && (
        <>
          {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
          {!isLoading && topics.length === 0 && (
            <EmptyState icon={Lightbulb} title="暂无选题" description="从趋势报告中生成选题，或手动添加" />
          )}
          <div className="space-y-3">
            {topics.map((topic) => (
              <Card key={topic.id} className="overflow-hidden">
                <div className="p-4 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium truncate">{topic.title}</span>
                      {statusBadge(topic.status)}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      {topic.source_report_query && (
                        <span className="flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          来源: {topic.source_report_query}
                        </span>
                      )}
                      {topic.estimated_engagement !== undefined && (
                        <span className="flex items-center gap-1">
                          <TrendingUp className="w-3 h-3" />
                          预估互动: {topic.estimated_engagement}
                        </span>
                      )}
                      {topic.tags && topic.tags.length > 0 && (
                        <span className="flex items-center gap-1">
                          <Tag className="w-3 h-3" />
                          {topic.tags.join(', ')}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {topic.status === 'pending' && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => navigate('/content-forge', { state: { topicId: topic.id, title: topic.title } })}
                        >
                          <ExternalLink className="w-3 h-3" />
                          采用
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => updateTopic(topic.id, 'abandoned')}>
                          <XCircle className="w-3 h-3" />
                          放弃
                        </Button>
                      </>
                    )}
                    {topic.status === 'abandoned' && (
                      <Button size="sm" variant="outline" onClick={() => updateTopic(topic.id, 'pending')}>
                        <RefreshCw className="w-3 h-3" />
                        恢复
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" onClick={() => deleteTopic(topic.id)}>
                      <Trash2 className="w-3 h-3 text-danger" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* 热搜监控 */}
      {activeTab === 'hot' && (
        <>
          <Card>
            <CardHeader className="flex items-center gap-2">
              <Flame className="w-4 h-4 text-primary" />
              <h3 className="text-base font-semibold">实时热搜词云</h3>
            </CardHeader>
            <CardContent>
              {isLoading && <div className="h-32 animate-pulse bg-secondary/50 rounded-lg" />}
              {!isLoading && hotKeywords.length === 0 && (
                <EmptyState icon={Flame} title="暂无热搜数据" description="稍后再试或手动创建趋势报告" />
              )}
              <div className="flex flex-wrap gap-3">
                {hotKeywords.map((kw) => (
                  <HotTag key={kw.word} keyword={kw} onClick={() => handleCreateFromHot(kw.word)} />
                ))}
              </div>
            </CardContent>
          </Card>

          {hotKeywords.length > 0 && (
            <Card>
              <CardHeader className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-primary" />
                <h3 className="text-base font-semibold">热搜榜单</h3>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th className="text-left py-2 px-2 font-medium">排名</th>
                        <th className="text-left py-2 px-2 font-medium">热词</th>
                        <th className="text-left py-2 px-2 font-medium">热度指数</th>
                        <th className="text-left py-2 px-2 font-medium">趋势</th>
                        <th className="text-right py-2 px-2 font-medium">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {hotKeywords.map((kw, idx) => (
                        <tr key={kw.word} className="border-b border-border/50 hover:bg-secondary/20">
                          <td className="py-2 px-2 font-medium">{idx + 1}</td>
                          <td className="py-2 px-2">{kw.word}</td>
                          <td className="py-2 px-2">{kw.heat}</td>
                          <td className="py-2 px-2">
                            <span className="inline-flex items-center gap-1">
                              <TrendIcon trend={kw.trend} />
                              {kw.trend === 'up' ? '上升' : kw.trend === 'down' ? '下降' : '平稳'}
                            </span>
                          </td>
                          <td className="py-2 px-2 text-right">
                            <Button size="sm" variant="ghost" onClick={() => handleCreateFromHot(kw.word)}>
                              <Wand2 className="w-3 h-3" />
                              创建报告
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
