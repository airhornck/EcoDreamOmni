import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader } from '../ui/Card'
import { EmptyState } from '../ui/EmptyState'
import { Badge } from '../ui/Badge'
import { TrendingUp, Zap } from 'lucide-react'
import { authHeaders } from '../../lib/api'

interface TrendTopic {
  id: string
  rank: number
  title: string
  heat: number
  risk_level: 'low' | 'medium' | 'high'
  source: string
}

export function TrendScoutPanel() {
  const navigate = useNavigate()
  const [topics, setTopics] = useState<TrendTopic[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchTrends() {
      try {
        const res = await fetch('/api/trend-scout/reports?limit=5', { headers: authHeaders() })
        if (res.ok) {
          const data = await res.json()
          setTopics(data.topics || [])
        }
      } catch {
        // silent fail
      } finally {
        setLoading(false)
      }
    }
    fetchTrends()
  }, [])

  if (loading) {
    return (
      <Card>
        <div className="h-48 animate-pulse bg-secondary/50 rounded-xl" />
      </Card>
    )
  }

  if (topics.length === 0) {
    return (
      <Card>
        <EmptyState
          icon={TrendingUp}
          title="智能选题"
          description="TrendScout 热点推荐功能开发中。系统将每日更新宠物健康领域热门话题。"
        />
      </Card>
    )
  }

  const riskVariant = (risk: string) => {
    switch (risk) {
      case 'low': return 'success'
      case 'medium': return 'warning'
      case 'high': return 'danger'
      default: return 'default'
    }
  }

  const riskLabel = (risk: string) => {
    switch (risk) {
      case 'low': return '低风险'
      case 'medium': return '中风险'
      case 'high': return '高风险'
      default: return risk
    }
  }

  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-primary" />
          <h2 className="text-base font-semibold text-foreground">智能选题</h2>
        </div>
        <Badge variant="primary">每日更新</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        {topics.map((topic) => (
          <div
            key={topic.id}
            className="flex items-center gap-3 p-3 bg-secondary/30 rounded-lg hover:bg-secondary/50 transition-colors group"
          >
            <span className="text-sm font-bold text-muted-foreground w-5 text-center">{topic.rank}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">{topic.title}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] text-muted-foreground">{topic.source}</span>
                <Badge variant={riskVariant(topic.risk_level)}>{riskLabel(topic.risk_level)}</Badge>
              </div>
            </div>
            <button 
              onClick={() => navigate(`/content-forge?topic=${encodeURIComponent(topic.title)}`)}
              className="opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <Zap className="w-3 h-3" />
              生成
            </button>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
