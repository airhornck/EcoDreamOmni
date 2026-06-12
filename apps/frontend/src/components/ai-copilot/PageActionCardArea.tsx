/**
 * Copilot-Driven 页面级 Action Cards 渲染器 — v4.0 Step 3
 *
 * 由页面组件通过 aiCopilotStore.setPageActionCards() 注入 Action Cards，
 * 本组件读取并渲染在 Copilot Panel 的 InputBox 上方。
 *
 * 支持的 Card 类型:
 *   - decision:  审核决策（通过/打回/驳回）
 *   - generation: AI 生成（封面生成等）
 *   - suggestion: 建议（批量审核等）
 *   - info:      信息展示（AI 分析等）
 */

import { useState } from 'react'
import { useAICopilotStore, type PageActionCard } from '../../stores/aiCopilotStore'
import { Check, Sparkles, Lightbulb, Info, Loader2 } from 'lucide-react'

interface PageActionCardAreaProps {
  onAction?: (cardId: string, actionId: string, payload?: Record<string, unknown>) => void
}

export function PageActionCardArea({ onAction }: PageActionCardAreaProps) {
  const { pageActionCards } = useAICopilotStore()

  if (pageActionCards.length === 0) return null

  return (
    <div className="px-3 py-2 border-t border-border space-y-2 max-h-64 overflow-y-auto">
      {pageActionCards.map((card) => (
        <PageActionCardItem key={card.id} card={card} onAction={onAction} />
      ))}
    </div>
  )
}

function PageActionCardItem({
  card,
  onAction,
}: {
  card: PageActionCard
  onAction?: (cardId: string, actionId: string, payload?: Record<string, unknown>) => void
}) {
  const [reason, setReason] = useState('')
  const [executing, setExecuting] = useState(false)
  const [inputValues, setInputValues] = useState<Record<string, string>>({})

  const handleAction = async (actionId: string, needsReason?: boolean) => {
    if (executing) return
    setExecuting(true)

    const payload: Record<string, unknown> = { ...inputValues }
    if (needsReason && reason) {
      payload.reason = reason
    }

    try {
      await onAction?.(card.id, actionId, payload)
    } finally {
      setExecuting(false)
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card p-3 space-y-2.5">
      {/* Card Header */}
      <div className="flex items-center gap-2">
        {card.type === 'decision' && <Check className="w-4 h-4 text-primary" />}
        {card.type === 'generation' && <Sparkles className="w-4 h-4 text-primary" />}
        {card.type === 'suggestion' && <Lightbulb className="w-4 h-4 text-warning" />}
        {card.type === 'info' && <Info className="w-4 h-4 text-muted-foreground" />}
        <span className="text-sm font-medium">{card.title}</span>
      </div>

      {/* Description */}
      {card.description && (
        <p className="text-xs text-muted-foreground leading-relaxed">{card.description}</p>
      )}

      {/* Inputs */}
      {card.inputs && card.inputs.length > 0 && (
        <div className="space-y-2">
          {card.inputs.map((input) => (
            <div key={input.name} className="space-y-1">
              {input.label && (
                <label className="text-xs text-muted-foreground">{input.label}</label>
              )}
              {input.type === 'textarea' ? (
                <textarea
                  className="w-full text-xs bg-secondary rounded-md px-2.5 py-2 border border-border focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none resize-none"
                  rows={2}
                  placeholder={input.placeholder}
                  value={inputValues[input.name] || ''}
                  onChange={(e) =>
                    setInputValues((prev) => ({ ...prev, [input.name]: e.target.value }))
                  }
                />
              ) : (
                <input
                  type="text"
                  className="w-full text-xs bg-secondary rounded-md px-2.5 py-2 border border-border focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none"
                  placeholder={input.placeholder}
                  value={inputValues[input.name] || ''}
                  onChange={(e) =>
                    setInputValues((prev) => ({ ...prev, [input.name]: e.target.value }))
                  }
                />
              )}
            </div>
          ))}
        </div>
      )}

      {/* Reason Input (for needs_reason actions) */}
      {card.actions?.some((a) => a.needs_reason) && (
        <textarea
          className="w-full text-xs bg-secondary rounded-md px-2.5 py-2 border border-border focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none resize-none"
          rows={2}
          placeholder="请输入原因（可选）..."
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
      )}

      {/* Actions */}
      {card.actions && card.actions.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {card.actions.map((action) => {
            const isPrimary = action.variant === 'primary'
            const isSecondary = action.variant === 'secondary'
            const isGhost = action.variant === 'ghost'

            return (
              <button
                key={action.id}
                disabled={executing}
                onClick={() => handleAction(action.id, action.needs_reason)}
                className={`
                  px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors disabled:opacity-50
                  ${isPrimary ? 'bg-primary text-primary-foreground hover:bg-primary/90' : ''}
                  ${isSecondary ? 'bg-secondary text-secondary-foreground hover:bg-secondary/80' : ''}
                  ${isGhost ? 'bg-transparent text-muted-foreground hover:bg-muted border border-border' : ''}
                `}
              >
                {executing ? (
                  <Loader2 className="w-3 h-3 animate-spin inline mr-1" />
                ) : null}
                {action.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
