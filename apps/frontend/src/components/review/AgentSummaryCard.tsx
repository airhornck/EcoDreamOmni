import { Card, CardContent, CardHeader } from '../ui/Card'
import { Badge } from '../ui/Badge'
import {
  Shield,
  BarChart3,
  Award,
  ThumbsUp,
  MessageCircle,
  Star,
  TrendingUp,
  Clock,
} from 'lucide-react'
import type { ReviewDetail } from '../../stores/reviewPublishStore'

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? 'bg-success' : value >= 60 ? 'bg-warning' : 'bg-destructive'
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{value}</span>
      </div>
      <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

function _resolveInterval(val: unknown): { min: number; max: number } {
  if (Array.isArray(val)) {
    return { min: (val[0] as number | undefined) ?? 0, max: (val[1] as number | undefined) ?? 0 }
  }
  if (val && typeof val === 'object') {
    const obj = val as Record<string, unknown>
    return {
      min: typeof obj.min === 'number' ? obj.min : 0,
      max: typeof obj.max === 'number' ? obj.max : 0,
    }
  }
  return { min: 0, max: 0 }
}

function EngagementCard({
  icon: Icon,
  label,
  min,
  max,
}: {
  icon: React.ElementType
  label: string
  min: number
  max: number
}) {
  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-secondary/50">
      <Icon className="w-4 h-4 text-muted-foreground" />
      <div className="text-xs">
        <div className="text-muted-foreground">{label}</div>
        <div className="font-medium">
          {min} - {max}
        </div>
      </div>
    </div>
  )
}

export function AgentSummaryCard({ detail }: { detail: ReviewDetail | null }) {
  if (!detail) return null

  const compliance = detail.compliance_result || {}
  const prediction = detail.prediction_result || {}
  const quality = detail.quality_score || {}
  const engagement = prediction.engagement_interval as Record<
    string,
    { min: number; max: number; confidence: string }
  > | undefined

  const complianceLevel = (compliance.level as string) || 'unknown'
  const violations = (compliance.violations as unknown[]) || []

  return (
    <Card>
      <CardHeader className="text-sm font-medium flex items-center gap-2 py-3">
        <Award className="w-4 h-4 text-primary" />
        Agent 摘要
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        {/* Compliance */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-medium">
            <Shield className="w-3.5 h-3.5" />
            <span>合规审核</span>
          </div>
          {complianceLevel === 'pass' ? (
            <div className="p-2 rounded-lg bg-success/10 text-success text-xs flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5" />
              <span>✅ L1-L4 全部通过</span>
            </div>
          ) : complianceLevel === 'warning' ? (
            <div className="p-2 rounded-lg bg-warning/10 text-warning text-xs">
              <div className="flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5" />
                <span>⚠️ 存在警告</span>
              </div>
              {violations.length > 0 && (
                <ul className="mt-1 ml-5 list-disc">
                  {violations.map((v: unknown, i: number) => {
                    const text = typeof v === 'string' ? v : String((v as Record<string, unknown>).message || JSON.stringify(v))
                    return <li key={i}>{text}</li>
                  })}
                </ul>
              )}
            </div>
          ) : (
            <div className="p-2 rounded-lg bg-secondary/50 text-muted-foreground text-xs">
              暂无合规数据
            </div>
          )}
        </div>

        {/* Prediction */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-medium">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>互动预演</span>
            <span className="text-[10px] text-muted-foreground">（参考区间）</span>
          </div>
          {engagement ? (
            <div className="space-y-2">
              <div className="grid grid-cols-3 gap-2">
                {engagement.likes && (
                  <EngagementCard icon={ThumbsUp} label="点赞" min={_resolveInterval(engagement.likes).min} max={_resolveInterval(engagement.likes).max} />
                )}
                {engagement.comments && (
                  <EngagementCard icon={MessageCircle} label="评论" min={_resolveInterval(engagement.comments).min} max={_resolveInterval(engagement.comments).max} />
                )}
                {engagement.collects && (
                  <EngagementCard icon={Star} label="收藏" min={_resolveInterval(engagement.collects).min} max={_resolveInterval(engagement.collects).max} />
                )}
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                {prediction.viral_probability !== undefined && (
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    爆文概率: {(prediction.viral_probability as number) * 100}%
                  </span>
                )}
                {(prediction.best_publish_time as string | undefined) && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    最佳: {prediction.best_publish_time as string}
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="p-2 rounded-lg bg-secondary/50 text-muted-foreground text-xs">
              暂无预演数据
            </div>
          )}
        </div>

        {/* Quality Score */}
        {Object.keys(quality).length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-medium">
              <Award className="w-3.5 h-3.5" />
              <span>质量分</span>
              {quality.overall !== undefined && (
                <Badge variant={(quality.overall as number) >= 80 ? 'success' : 'warning'} className="text-[10px]">
                  {quality.overall as number}
                </Badge>
              )}
            </div>
            <div className="space-y-2">
              {quality.title_attractiveness !== undefined && (
                <ScoreBar label="标题吸引力" value={quality.title_attractiveness as number} />
              )}
              {quality.body_completeness !== undefined && (
                <ScoreBar label="正文完整性" value={quality.body_completeness as number} />
              )}
              {quality.tag_relevance !== undefined && (
                <ScoreBar label="标签相关度" value={quality.tag_relevance as number} />
              )}
              {quality.readability !== undefined && (
                <ScoreBar label="可读性" value={quality.readability as number} />
              )}
              {quality.engagement_potential !== undefined && (
                <ScoreBar label="互动潜力" value={quality.engagement_potential as number} />
              )}
              {quality.compliance_score !== undefined && (
                <ScoreBar label="合规分" value={quality.compliance_score as number} />
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
