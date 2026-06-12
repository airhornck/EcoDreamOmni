import { useInlineAIStore, type SuggestionType } from '../../stores/inlineAIStore'
import { Lightbulb, Plus, Minus, AlertTriangle, Info, Check, X } from 'lucide-react'

interface InlineSuggestionCardProps {
  targetId: string
}

const typeConfig: Record<
  SuggestionType,
  { icon: React.ElementType; color: string; bg: string; label: string }
> = {
  OPTIMIZE: { icon: Lightbulb, color: 'text-info', bg: 'bg-info/10', label: '优化' },
  ADD: { icon: Plus, color: 'text-success', bg: 'bg-success/10', label: '新增' },
  REMOVE: { icon: Minus, color: 'text-destructive', bg: 'bg-destructive/10', label: '删除' },
  WARNING: { icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning/10', label: '警告' },
  INFO: { icon: Info, color: 'text-muted-foreground', bg: 'bg-secondary', label: '提示' },
}

export function InlineSuggestionCard({ targetId }: InlineSuggestionCardProps) {
  const { suggestions, apply, dismiss } = useInlineAIStore()
  const relevant = suggestions.filter((s) => s.targetId === targetId)

  if (relevant.length === 0) return null

  return (
    <div className="absolute z-20 w-64 space-y-2" style={{ top: '-0.5rem', right: '-17rem' }}>
      {relevant.map((sg) => {
        const config = typeConfig[sg.type]
        const Icon = config.icon
        return (
          <div
            key={sg.id}
            className="rounded-lg border border-border bg-card shadow-lg p-3 space-y-2 animate-fade-in"
          >
            <div className="flex items-start gap-2">
              <div className={`w-6 h-6 rounded-full ${config.bg} flex items-center justify-center shrink-0`}>
                <Icon className={`w-3.5 h-3.5 ${config.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className={`text-[10px] font-medium uppercase ${config.color}`}>
                    {config.label}
                  </span>
                </div>
                <p className="text-sm font-medium mt-0.5">{sg.title}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{sg.description}</p>
              </div>
            </div>

            {sg.diff && (
              <div className="space-y-1 text-xs">
                <div className="p-1.5 rounded bg-destructive/10 text-destructive line-through">
                  {sg.diff.before}
                </div>
                <div className="p-1.5 rounded bg-success/10 text-success">
                  {sg.diff.after}
                </div>
              </div>
            )}

            <div className="flex gap-1.5 justify-end pt-1">
              <button
                onClick={() => dismiss(sg.id)}
                className="px-2 py-1 rounded text-xs text-muted-foreground hover:bg-secondary transition-colors flex items-center gap-0.5"
              >
                <X className="w-3 h-3" />
                忽略
              </button>
              {sg.type !== 'INFO' && (
                <button
                  onClick={() => apply(sg.id)}
                  className="px-2 py-1 rounded text-xs bg-primary text-primary-foreground hover:bg-primary/90 transition-colors flex items-center gap-0.5"
                >
                  <Check className="w-3 h-3" />
                  应用
                </button>
              )}
              {sg.type === 'INFO' && (
                <button
                  onClick={() => dismiss(sg.id)}
                  className="px-2 py-1 rounded text-xs bg-secondary hover:bg-primary/10 hover:text-primary transition-colors"
                >
                  知道了
                </button>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
