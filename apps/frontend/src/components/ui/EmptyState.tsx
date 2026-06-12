import { cn } from '../../lib/utils'
import { Sparkles } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon?: LucideIcon
  emoji?: string
  title: string
  description?: string
  action?: React.ReactNode
  aiSuggestion?: string
  className?: string
  [key: string]: unknown
}

export function EmptyState({
  icon: Icon,
  emoji,
  title,
  description,
  action,
  aiSuggestion,
  className,
  ...props
}: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center text-center py-10 px-4', className)} {...props}>
      {emoji ? (
        <span className="text-4xl mb-3">{emoji}</span>
      ) : Icon ? (
        <Icon className="h-10 w-10 text-muted-foreground mb-3" />
      ) : null}
      <h3 className="text-sm font-medium text-foreground">{title}</h3>
      {description && <p className="text-xs text-muted-foreground mt-1 max-w-xs">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
      {aiSuggestion && (
        <p className="text-[10px] mt-3 flex items-center gap-1 text-primary">
          <Sparkles className="w-3 h-3" />
          <span>AI 建议：{aiSuggestion}</span>
        </p>
      )}
    </div>
  )
}
