import { cn } from '../../lib/utils'
import { Sparkles, Check, X, Loader2 } from 'lucide-react'
import type { ReactNode } from 'react'

export type AgentTraceStatus = 'success' | 'running' | 'pending' | 'error'

export interface AgentTraceItem {
  name: string
  duration?: string
  status: AgentTraceStatus
}

export interface ContentCardProps {
  avatar?: string
  accountName: string
  platform?: string
  title: string
  tags?: string[]
  engagement?: string
  complianceScore?: number
  agentTrace?: AgentTraceItem[]
  aiSuggestion?: string
  actions?: ReactNode
  aiGenerating?: boolean
  className?: string
  [key: string]: unknown
}

function StatusDot({ status }: { status: AgentTraceStatus }) {
  const colorMap: Record<AgentTraceStatus, string> = {
    success: 'bg-success',
    running: 'bg-primary animate-pulse-glow',
    pending: 'bg-muted-foreground',
    error: 'bg-destructive',
  }
  return (
    <span className={cn('inline-block w-2 h-2 rounded-full', colorMap[status])} />
  )
}

function StatusIcon({ status }: { status: AgentTraceStatus }) {
  switch (status) {
    case 'success':
      return <Check className="w-3 h-3 text-success" />
    case 'error':
      return <X className="w-3 h-3 text-destructive" />
    case 'running':
      return <Loader2 className="w-3 h-3 text-primary animate-spin" />
    default:
      return <span className="text-muted-foreground text-xs">⏳</span>
  }
}

function ComplianceBar({ score }: { score: number }) {
  let colorClass = 'bg-success'
  if (score < 70) colorClass = 'bg-destructive'
  else if (score < 85) colorClass = 'bg-warning'

  return (
    <div className="mb-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-muted-foreground">合规分数</span>
        <span
          className={cn(
            'text-xs font-semibold',
            score >= 85 && 'text-success',
            score >= 70 && score < 85 && 'text-warning',
            score < 70 && 'text-destructive'
          )}
        >
          {score}分{score < 70 && ' ⚠️'}
        </span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden bg-secondary">
        <div
          className={cn('h-full rounded-full transition-all', colorClass)}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}

export function ContentCard({
  avatar,
  accountName,
  platform,
  title,
  tags,
  engagement,
  complianceScore,
  agentTrace,
  aiSuggestion,
  actions,
  aiGenerating = false,
  className,
  ...props
}: ContentCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl p-4 border bg-card',
        aiGenerating && 'animate-pulse-glow',
        !aiGenerating && 'card-hover',
        className
      )}
      {...props}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 min-w-0">
          {avatar ? (
            <img src={avatar} alt={accountName} className="w-6 h-6 rounded-full" />
          ) : (
            <span className="text-lg">🐱</span>
          )}
          <span className="text-sm font-medium text-foreground truncate">{accountName}</span>
          {platform && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-secondary text-muted-foreground">
              {platform}
            </span>
          )}
        </div>
        {aiGenerating && (
          <span className="text-xs px-2 py-0.5 rounded-full text-white font-medium bg-gradient-to-r from-primary to-purple-400 flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            AI 生成中
          </span>
        )}
      </div>

      {/* Title */}
      <p className="text-sm mb-3 text-muted-foreground line-clamp-2">{title}</p>

      {/* Tags + Engagement */}
      <div className="flex items-center justify-between mb-3">
        {tags && tags.length > 0 && (
          <div className="flex gap-1.5 flex-wrap">
            {tags.map((tag) => (
              <span
                key={tag}
                className="text-[10px] px-2 py-0.5 rounded-full bg-primary/8 text-primary"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        {engagement && <span className="text-xs text-muted-foreground">❤️ {engagement}</span>}
      </div>

      {/* Compliance */}
      {typeof complianceScore === 'number' && <ComplianceBar score={complianceScore} />}

      {/* Agent Trace */}
      {agentTrace && agentTrace.length > 0 && (
        <div className="space-y-1 mb-3">
          {agentTrace.map((item) => (
            <div key={item.name} className="flex items-center gap-2 text-xs text-muted-foreground">
              <StatusDot status={item.status} />
              <span className="flex-1">{item.name}</span>
              {item.duration && <span>{item.duration}</span>}
              <StatusIcon status={item.status} />
            </div>
          ))}
        </div>
      )}

      {/* AI Suggestion */}
      {aiSuggestion && (
        <div className="p-2 rounded-lg mb-3 text-xs bg-destructive/6 text-destructive">
          🤖 {aiSuggestion}
        </div>
      )}

      {/* Actions */}
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  )
}
