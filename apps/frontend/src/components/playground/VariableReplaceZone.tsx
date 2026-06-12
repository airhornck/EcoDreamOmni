import { usePlaygroundStore } from '../../stores/playgroundStore'
import { Pencil } from 'lucide-react'

export function VariableReplaceZone() {
  const { variables, updateVariable } = usePlaygroundStore()

  return (
    <div className="bg-card rounded-xl border border-border p-4 space-y-3 h-full flex flex-col">
      <div className="flex items-center gap-2">
        <Pencil className="w-4 h-4 text-success" />
        <h3 className="text-sm font-semibold">变量替换</h3>
      </div>

      {variables.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-muted-foreground">选择模板后可修改变量</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {variables.map((v) => (
            <div key={v.key}>
              <label className="text-xs text-muted-foreground block mb-0.5">{v.label}</label>
              <input
                type="text"
                value={v.current_value}
                onChange={(e) => updateVariable(v.key, e.target.value)}
                placeholder={v.default_value}
                className="w-full px-2.5 py-1.5 rounded-lg bg-secondary text-sm outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
