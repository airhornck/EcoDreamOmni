import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader } from '../ui/Card'
import { EmptyState } from '../ui/EmptyState'
import { Sparkles, Lightbulb } from 'lucide-react'
import { authHeaders } from '../../lib/api'

interface PredictionResult {
  content_preview: string
  likes: { lower: number; median: number; upper: number }
  comments: { lower: number; median: number; upper: number }
  saves: { lower: number; median: number; upper: number }
  confidence: number
  interval_mode: 'prior' | 'fitted'
  suggestions: string[]
}

export function PredictionPanel() {
  const [prediction, setPrediction] = useState<PredictionResult | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchPrediction() {
      try {
        const res = await fetch('/api/predictions/latest', { headers: authHeaders() })
        if (res.ok) {
          const data = await res.json()
          setPrediction(data)
        }
      } catch {
        // silent fail
      } finally {
        setLoading(false)
      }
    }
    fetchPrediction()
  }, [])

  if (loading) {
    return (
      <Card>
        <div className="h-48 animate-pulse bg-secondary/50 rounded-xl" />
      </Card>
    )
  }

  if (!prediction) {
    return (
      <Card>
        <EmptyState
          icon={Sparkles}
          title="流量预演"
          description="互动量区间预演功能开发中。预演结果将展示 likes/comments/saves 的预测区间及优化建议。"
        />
      </Card>
    )
  }

  const intervals = [
    { label: '点赞', data: prediction.likes },
    { label: '评论', data: prediction.comments },
    { label: '收藏', data: prediction.saves },
  ]

  return (
    <Card>
      <CardHeader className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-primary" />
        <h2 className="text-base font-semibold text-foreground">流量预演</h2>
        {prediction.interval_mode === 'prior' && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-info-bg text-info ml-auto">参考区间</span>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground line-clamp-2">{prediction.content_preview}</p>

        <div className="grid grid-cols-3 gap-3">
          {intervals.map(({ label, data }) => (
            <div key={label} className="text-center p-3 bg-secondary/50 rounded-lg">
              <div className="text-xs text-muted-foreground mb-1">{label}</div>
              <div className="text-lg font-bold text-foreground">{data.median}</div>
              <div className="text-[10px] text-muted-foreground mt-0.5">
                {data.lower} ~ {data.upper}
              </div>
            </div>
          ))}
        </div>

        {prediction.suggestions.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-foreground flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-warning" />
              优化建议
            </h4>
            <ul className="space-y-1.5">
              {prediction.suggestions.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                  <span className="mt-0.5 w-1 h-1 rounded-full bg-primary shrink-0" />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
