import { User, BookOpen, GitBranch } from 'lucide-react'
import type { PersonaOption, PersonaStoryOption } from '../../../../stores/taskHubStore'

interface BaseAssociationsProps {
  personaId: string
  storyId: string
  nodeId: string
  personas: PersonaOption[]
  personaStories: PersonaStoryOption[]
  storyNodes: Array<{ id: string; theme: string; label?: string }>
  onUpdateField: (key: string, value: unknown) => void
}

export function BaseAssociations({
  personaId,
  storyId,
  nodeId,
  personas,
  personaStories,
  storyNodes,
  onUpdateField,
}: BaseAssociationsProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-primary/10 text-primary text-xs">🔗</span>
        基础关联（可选）
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Persona */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <User className="w-3.5 h-3.5" />
            人设
          </label>
          <select
            value={personaId}
            onChange={(e) => {
              onUpdateField('personaId', e.target.value)
              onUpdateField('storyId', '')
              onUpdateField('nodeId', '')
            }}
            className="w-full h-9 px-2.5 rounded-md border border-border bg-background text-sm"
          >
            <option value="">不限</option>
            {personas.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Story */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <BookOpen className="w-3.5 h-3.5" />
            故事线
          </label>
          <select
            value={storyId}
            onChange={(e) => {
              onUpdateField('storyId', e.target.value)
              onUpdateField('nodeId', '')
            }}
            disabled={!personaId || personaStories.length === 0}
            className="w-full h-9 px-2.5 rounded-md border border-border bg-background text-sm disabled:opacity-50"
          >
            <option value="">不限</option>
            {personaStories.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        {/* Node */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <GitBranch className="w-3.5 h-3.5" />
            当前节点
          </label>
          <select
            value={nodeId}
            onChange={(e) => onUpdateField('nodeId', e.target.value)}
            disabled={!storyId || storyNodes.length === 0}
            className="w-full h-9 px-2.5 rounded-md border border-border bg-background text-sm disabled:opacity-50"
          >
            <option value="">不限</option>
            {storyNodes.map((n) => (
              <option key={n.id} value={n.id}>
                {n.label || n.theme}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
