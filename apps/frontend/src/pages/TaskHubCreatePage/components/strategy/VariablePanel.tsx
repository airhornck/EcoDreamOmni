import { useMemo } from 'react'
import { Variable, Info } from 'lucide-react'
import type { StrategyElement, StrategyElementRef } from '../../../../types/strategy'

interface VariablePanelProps {
  elements: StrategyElement[]
  composition: StrategyElementRef[]
  variables: Record<string, string>
  onVariableChange: (key: string, value: string) => void
}

interface MergedVariable {
  name: string
  label: string
  type: string
  defaultValue?: string | null
  sourceElementIds: string[]
  sourceNames: string[]
}

export function VariablePanel({
  elements,
  composition,
  variables,
  onVariableChange,
}: VariablePanelProps) {
  const mergedVars = useMemo(() => {
    const map = new Map<string, MergedVariable>()
    for (const ref of composition) {
      const el = elements.find((e) => e.element_id === ref.element_id)
      if (!el || !el.variables) continue
      for (const v of el.variables) {
        const existing = map.get(v.name)
        if (existing) {
          existing.sourceElementIds.push(ref.element_id)
          existing.sourceNames.push(el.name)
        } else {
          map.set(v.name, {
            name: v.name,
            label: v.label,
            type: v.type ?? 'text',
            defaultValue: v.default_value,
            sourceElementIds: [ref.element_id],
            sourceNames: [el.name],
          })
        }
      }
    }
    return Array.from(map.values())
  }, [elements, composition])

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-primary/10 text-primary text-xs">🔧</span>
        变量推导 ({mergedVars.length})
      </div>

      {mergedVars.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-4 text-center flex items-center justify-center gap-2">
          <Info className="w-4 h-4 text-muted-foreground" />
          <p className="text-xs text-muted-foreground">添加策略元素后将自动推导变量</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {mergedVars.map((v) => (
            <div key={v.name} className="space-y-1">
              <label className="flex items-center gap-1.5 text-xs font-medium">
                <Variable className="w-3 h-3 text-muted-foreground" />
                {v.label || v.name}
                {v.sourceNames.length > 1 && (
                  <span className="text-[10px] text-muted-foreground bg-muted px-1 rounded">
                    {v.sourceNames.length} 个来源
                  </span>
                )}
              </label>
              <input
                type={v.type === 'number' ? 'number' : 'text'}
                value={variables[v.name] ?? v.defaultValue ?? ''}
                onChange={(e) => onVariableChange(v.name, e.target.value)}
                placeholder={v.defaultValue ?? ''}
                className="w-full h-8 px-2.5 rounded-md border border-border bg-background text-sm placeholder:text-muted-foreground"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
