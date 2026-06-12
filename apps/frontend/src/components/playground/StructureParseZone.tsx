import { usePlaygroundStore } from '../../stores/playgroundStore'
import { GitBranch, Tag } from 'lucide-react'

export function StructureParseZone() {
  const { parsed } = usePlaygroundStore()

  return (
    <div className="bg-card rounded-xl border border-border p-4 space-y-4 h-full flex flex-col">
      <div className="flex items-center gap-2">
        <GitBranch className="w-4 h-4 text-info" />
        <h3 className="text-sm font-semibold">结构解析</h3>
      </div>

      {!parsed ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-muted-foreground">先输入爆款内容，点击「AI 结构解析」</p>
        </div>
      ) : (
        <div className="space-y-4">
          <ParseItem label="Hook 模式" value={parsed.hook_pattern} />
          <ParseItem label="正文结构" value={parsed.body_structure} />
          <ParseItem label="CTA 模式" value={parsed.cta_pattern} />
          <ParseItem label="语气风格" value={parsed.tone} />

          <div>
            <span className="text-xs text-muted-foreground mb-1.5 block">关键词</span>
            <div className="flex flex-wrap gap-1">
              {parsed.keywords.map((kw) => (
                <span key={kw} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-info/10 text-info text-xs">
                  <Tag className="w-3 h-3" />
                  {kw}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ParseItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-xs text-muted-foreground block mb-0.5">{label}</span>
      <p className="text-sm font-medium">{value}</p>
    </div>
  )
}
