import { useAICopilotStore } from '../../stores/aiCopilotStore'
import { MapPin, X } from 'lucide-react'

export function ContextBar() {
  const { context, setContext } = useAICopilotStore()

  if (!context.page && !context.selectedItems?.length && !context.activeTask) {
    return null
  }

  return (
    <div className="px-3 py-2 border-b border-border bg-secondary/30">
      <div className="flex items-center gap-1.5 flex-wrap">
        <MapPin className="w-3 h-3 text-muted-foreground shrink-0" />
        <span className="text-xs text-muted-foreground">上下文:</span>
        {context.page && (
          <ContextTag
            label={context.page}
            onRemove={() => setContext({ page: undefined })}
          />
        )}
        {context.selectedItems?.[0] && (
          <ContextTag
            label={`内容 #${context.selectedItems[0].slice(0, 8)}`}
            onRemove={() => setContext({ selectedItems: [] })}
          />
        )}
        {context.activeTask && (
          <ContextTag
            label={`任务 #${context.activeTask.slice(0, 8)}`}
            onRemove={() => setContext({ activeTask: undefined })}
          />
        )}
      </div>
    </div>
  )
}

function ContextTag({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-primary/10 text-primary text-xs">
      {label}
      <button onClick={onRemove} className="hover:bg-primary/20 rounded p-0.5" aria-label="移除上下文">
        <X className="w-2.5 h-2.5" />
      </button>
    </span>
  )
}
