import { useAICopilotStore } from '../../stores/aiCopilotStore'
import { Zap } from 'lucide-react'

interface QuickActionBarProps {
  onActionClick?: (action: string) => void
}

export function QuickActionBar({ onActionClick }: QuickActionBarProps) {
  const { quickActions } = useAICopilotStore()

  if (quickActions.length === 0) return null

  return (
    <div className="px-3 py-2.5 border-t border-border bg-muted/30">
      <div className="flex items-center gap-1.5 mb-2">
        <Zap className="w-3.5 h-3.5 text-primary" />
        <span className="text-[11px] uppercase tracking-wider text-foreground font-semibold">
          快捷动作
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {quickActions.map((action) => {
          // 根据动作类型分配不同颜色
          const isPrimary = action === '下一步' || action === '确认部署'
          const isDanger = action === '取消'
          return (
            <button
              key={action}
              onClick={() => onActionClick?.(action)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all shadow-sm active:scale-95 truncate max-w-full ${
                isPrimary
                  ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                  : isDanger
                  ? 'bg-destructive/10 text-destructive border border-destructive/20 hover:bg-destructive/20'
                  : 'bg-background text-foreground border border-border hover:bg-muted hover:border-muted-foreground/30'
              }`}
            >
              {action}
            </button>
          )
        })}
      </div>
    </div>
  )
}
