import type { PersonaOption, PersonaStoryOption } from '../../../stores/taskHubStore'

interface StepPersonaStoryProps {
  personaId: string
  storyId: string
  nodeId: string
  errors: Record<string, string>
  personas: PersonaOption[]
  personaStories: PersonaStoryOption[]
  storyNodes: Array<{ id: string; theme: string; label?: string }>
  onUpdateField: (key: string, value: unknown) => void
}

export function StepPersonaStory({
  personaId,
  storyId,
  nodeId,
  errors,
  personas,
  personaStories,
  storyNodes,
  onUpdateField,
}: StepPersonaStoryProps) {
  return (
    <div className="space-y-5 max-w-2xl mx-auto">
      <h3 className="text-base font-semibold">人设与故事</h3>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">
          Persona <span className="text-destructive">*</span>
        </label>
        <select
          value={personaId}
          onChange={(e) => {
            onUpdateField('personaId', e.target.value)
            onUpdateField('storyId', '')
            onUpdateField('nodeId', '')
          }}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm"
        >
          <option value="">选择人设</option>
          {personas.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        {errors.personaId && <p className="text-xs text-destructive">{errors.personaId}</p>}
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">PersonaStory</label>
        <select
          value={storyId}
          onChange={(e) => {
            onUpdateField('storyId', e.target.value)
            onUpdateField('nodeId', '')
          }}
          disabled={!personaId || personaStories.length === 0}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm disabled:opacity-50"
        >
          <option value="">选择故事线</option>
          {personaStories.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-medium">当前节点</label>
        <select
          value={nodeId}
          onChange={(e) => onUpdateField('nodeId', e.target.value)}
          disabled={!storyId || storyNodes.length === 0}
          className="w-full h-10 px-3 rounded-lg border border-border bg-background text-sm disabled:opacity-50"
        >
          <option value="">选择节点</option>
          {storyNodes.map((n) => (
            <option key={n.id} value={n.id}>
              {n.label || n.theme}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
