import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader } from '../ui/Card'
import { EmptyState } from '../ui/EmptyState'
import { BarChart3, TrendingUp, TrendingDown, Target, Heart, MessageCircle, Bookmark } from 'lucide-react'
import { authHeaders } from '../../lib/api'

interface DailyReport {
  published_count: number
  coverage_rate: number
  avg_likes: number
  avg_comments: number
  avg_saves: number
  likes_delta: number
  comments_delta: number
  saves_delta: number
}

export function DailyReportPanel() {
  const [report, setReport] = useState<DailyReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchReport() {
      try {
        const res = await fetch('/api/data-analyst/dashboard', { headers: authHeaders() })
        if (res.ok) {
          const data = await res.json()
          setReport(data)
        }
      } catch {
        // silent fail
      } finally {
        setLoading(false)
      }
    }
    fetchReport()
  }, [])

  if (loading) {
    return (
      <Card>
        <div className="h-48 animate-pulse bg-secondary/50 rounded-xl" />
      </Card>
    )
  }

  if (!report) {
    return (
      <Card>
        <EmptyState
          icon={BarChart3}
          title="昨日战报"
          description="DataAnalyst 24h 数据聚合功能开发中。战报将展示发布篇数、预测命中率、平均互动等指标。"
        />
      </Card>
    )
  }

  const metrics = [
    { label: '发布篇数', value: report.published_count, icon: Target, delta: null },
    { label: '命中率', value: `${(report.coverage_rate * 100).toFixed(1)}%`, icon: Target, delta: null },
    { label: '平均点赞', value: report.avg_likes, icon: Heart, delta: report.likes_delta },
    { label: '平均评论', value: report.avg_comments, icon: MessageCircle, delta: report.comments_delta },
    { label: '平均收藏', value: report.avg_saves, icon: Bookmark, delta: report.saves_delta },
  ]

  return (
    <Card>
      <CardHeader className="flex items-center gap-2">
        <BarChart3 className="w-4 h-4 text-primary" />
        <h2 className="text-base font-semibold text-foreground">昨日战报</h2>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
          {metrics.map(({ label, value, icon: Icon, delta }) => (
            <div key={label} className="text-center p-3 bg-secondary/30 rounded-lg">
              <Icon className="w-4 h-4 text-muted-foreground mx-auto mb-1.5" />
              <div className="text-lg font-bold text-foreground">{value}</div>
              <div className="text-[10px] text-muted-foreground mt-0.5">{label}</div>
              {delta !== null && (
                <div className={`flex items-center justify-center gap-0.5 text-[10px] mt-1 ${delta >= 0 ? 'text-success' : 'text-red-500'}`}>
                  {delta >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  {Math.abs(delta)}%
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
