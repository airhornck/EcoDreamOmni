import { useAICopilotStore, type ActionCard } from '../../stores/aiCopilotStore'
import { Check, X, GitCompare, Info, ListChecks } from 'lucide-react'

export function ActionCardStack() {
  const { messages, applyActionCard } = useAICopilotStore()

  const cards = messages
    .filter((m) => m.actionCard)
    .map((m) => ({ messageId: m.id, card: m.actionCard! }))

  if (cards.length === 0) return null

  return (
    <div className="px-3 py-2 border-t border-border space-y-2 max-h-48 overflow-y-auto">
      {cards.map(({ messageId, card }) => (
        <ActionCardItem
          key={card.id}
          card={card}
          onApply={(action, payload) => applyActionCard(messageId, action, payload)}
        />
      ))}
    </div>
  )
}

function ActionCardItem({
  card,
  onApply,
}: {
  card: ActionCard
  onApply: (action: string, payload?: unknown) => void
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 space-y-2">
      <div className="flex items-center gap-2">
        {card.type === 'DIFF' && <GitCompare className="w-4 h-4 text-info" />}
        {card.type === 'CONFIRM' && <Check className="w-4 h-4 text-success" />}
        {card.type === 'MULTI_SELECT' && <ListChecks className="w-4 h-4 text-warning" />}
        {card.type === 'INFO' && <Info className="w-4 h-4 text-muted-foreground" />}
        <span className="text-sm font-medium">{card.title}</span>
      </div>

      {card.description && (
        <p className="text-xs text-muted-foreground">{card.description}</p>
      )}

      {card.diff && (
        <div className="space-y-1 text-xs">
          <div className="p-1.5 rounded bg-destructive/10 text-destructive line-through">
            {card.diff.before}
          </div>
          <div className="p-1.5 rounded bg-success/10 text-success">
            {card.diff.after}
          </div>
        </div>
      )}

      {card.options && (
        <div className="flex flex-wrap gap-1">
          {card.options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onApply('select', opt.value)}
              className="px-2 py-1 rounded bg-secondary text-xs hover:bg-primary/10 hover:text-primary transition-colors"
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}

      <div className="flex gap-2 justify-end">
        {card.type !== 'INFO' && (
          <>
            <button
              onClick={() => onApply('dismiss')}
              className="px-2 py-1 rounded text-xs text-muted-foreground hover:bg-secondary transition-colors"
            >
              <X className="w-3 h-3 inline mr-0.5" />
              忽略
            </button>
            <button
              onClick={() => onApply('apply')}
              className="px-2 py-1 rounded text-xs bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Check className="w-3 h-3 inline mr-0.5" />
              应用
            </button>
          </>
        )}
        {card.type === 'INFO' && (
          <button
            onClick={() => onApply('ack')}
            className="px-2 py-1 rounded text-xs bg-secondary hover:bg-primary/10 hover:text-primary transition-colors"
          >
            知道了
          </button>
        )}
      </div>
    </div>
  )
}
