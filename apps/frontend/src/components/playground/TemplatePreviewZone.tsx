import type { ViralTemplate } from './types'

interface TemplatePreviewZoneProps {
  template: ViralTemplate | null
}

export function TemplatePreviewZone({ template }: TemplatePreviewZoneProps) {
  if (!template) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center text-muted-foreground">
        <p className="text-sm">暂无模板数据</p>
        <p className="text-xs mt-1">请先完成分析并生成模板</p>
      </div>
    )
  }

  const { prompt_template, variables, constraints, structure_type } = template

  // Parse formula from prompt_template: replace {{var}} with colored badges
  const renderFormula = (text: string) => {
    const parts = text.split(/(\{\{[^}]+\}\})/g)
    return parts.map((part, i) => {
      const match = part.match(/^\{\{(.+)\}\}$/)
      if (match) {
        const colors = ['bg-blue-100 text-blue-700', 'bg-amber-100 text-amber-700', 'bg-rose-100 text-rose-700', 'bg-emerald-100 text-emerald-700', 'bg-violet-100 text-violet-700']
        const color = colors[i % colors.length]
        return (
          <span key={i} className={`px-1.5 py-0.5 rounded text-xs font-medium ${color}`}>
            {match[1]}
          </span>
        )
      }
      return <span key={i} className="text-sm">{part}</span>
    })
  }

  return (
    <div className="space-y-4 max-w-3xl mx-auto">
      {/* Formula Visualization */}
      <div className="bg-card rounded-xl border border-border p-4">
        <h3 className="text-sm font-semibold mb-3">Prompt 模板</h3>
        <div className="bg-secondary/30 rounded-lg p-3 text-sm leading-relaxed space-y-1">
          {renderFormula(prompt_template)}
        </div>
      </div>

      {/* Variables Table */}
      <div className="bg-card rounded-xl border border-border p-4">
        <h3 className="text-sm font-semibold mb-3">变量列表（{variables.length}个）</h3>
        <div className="space-y-2">
          {variables.map((v) => (
            <div key={v.name} className="flex items-center gap-3 text-xs py-2 px-3 rounded-lg bg-secondary/30">
              <span className="w-2 h-2 rounded-full bg-destructive" />
              <span className="w-20 font-medium truncate">{v.label}</span>
              <span className="text-muted-foreground">{v.type}</span>
              <span className="text-muted-foreground">默认: {v.default_value}</span>
              <span className="ml-auto px-1.5 py-0.5 rounded bg-destructive/10 text-destructive text-[10px]">必填</span>
            </div>
          ))}
        </div>
      </div>

      {/* Constraints */}
      <div className="bg-card rounded-xl border border-border p-4">
        <h3 className="text-sm font-semibold mb-3">约束条件</h3>
        <div className="grid grid-cols-2 gap-2">
          <ConstraintItem label="标题字数" value={`${constraints.title_length[0]}-${constraints.title_length[1]} 字`} />
          <ConstraintItem label="最少段落" value={`${constraints.body_section_min} 段`} />
          <ConstraintItem label="Emoji 密度" value={constraints.emoji_density} />
          <ConstraintItem label="钩子长度" value={`${constraints.hook_length[0]}-${constraints.hook_length[1]} 字`} />
        </div>
      </div>

      {/* Structure Type */}
      <div className="bg-card rounded-xl border border-border p-4">
        <h3 className="text-sm font-semibold mb-2">结构类型</h3>
        <span className="px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium">{structure_type}</span>
      </div>
    </div>
  )
}

function ConstraintItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-xs py-2 px-3 rounded-lg bg-secondary/30">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}
