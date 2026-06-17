import { useEffect, useMemo, useRef } from 'react'
import { useStrategyStore } from '../../../stores/strategyStore'
import { useStrategyElements } from '../../../hooks/useStrategyQueries'
import type { PersonaOption, PersonaStoryOption } from '../../../stores/taskHubStore'
import { BaseAssociations } from './strategy/BaseAssociations'
import { ElementBrowser } from './strategy/ElementBrowser'
import { StrategyCompositionPanel } from './strategy/StrategyCompositionPanel'
import { VariablePanel } from './strategy/VariablePanel'
import { Card } from '../../../components/ui/Card'
import { showToast } from '../../../lib/toast'

interface StepThemeStrategyProps {
  personaId: string
  storyId: string
  nodeId: string
  platform: string
  topic: string
  personas: PersonaOption[]
  personaStories: PersonaStoryOption[]
  storyNodes: Array<{ id: string; theme: string; label?: string }>
  onUpdateField: (key: string, value: unknown) => void
  onSave?: () => void
  onCancel?: () => void
  onClear?: () => void
}

export function StepThemeStrategy({
  personaId,
  storyId,
  nodeId,
  platform,
  topic,
  personas,
  personaStories,
  storyNodes,
  onUpdateField,
  onSave,
  onCancel,
  onClear,
}: StepThemeStrategyProps) {
  const {
    elements: cachedElements,
    setElements,
    currentStrategy,
    addElementToStrategy,
    removeElementFromStrategy,
    moveElement,
    setElementPriority,
    setStrategyVariable,
  } = useStrategyStore()

  // Fetch strategy elements on mount
  const { data: fetchedElements, isSuccess } = useStrategyElements(
    { platform, status: 'active', limit: 200 },
    { staleTime: 5 * 60 * 1000 }
  )

  useEffect(() => {
    if (isSuccess && fetchedElements) {
      setElements(fetchedElements)
    }
  }, [isSuccess, fetchedElements, setElements])

  // Sync strategy composition back to formData as JSON
  const strategyJson = useMemo(
    () => JSON.stringify(currentStrategy),
    [currentStrategy]
  )

  const onUpdateFieldRef = useRef(onUpdateField)
  useEffect(() => {
    onUpdateFieldRef.current = onUpdateField
  }, [onUpdateField])

  useEffect(() => {
    onUpdateFieldRef.current('contentStrategy', strategyJson)
  }, [strategyJson])

  const selectedIds = useMemo(
    () => currentStrategy.elements.map((el) => el.element_id),
    [currentStrategy.elements]
  )

  const activeElements = cachedElements.length > 0 ? cachedElements : (fetchedElements ?? [])

  return (
    <div className="space-y-4">
      <h3 className="text-base font-semibold">主题与策略</h3>

      {/* Section: Base Associations */}
      <BaseAssociations
        personaId={personaId}
        storyId={storyId}
        nodeId={nodeId}
        personas={personas}
        personaStories={personaStories}
        storyNodes={storyNodes}
        onUpdateField={onUpdateField}
      />

      {/* Section: Variable Panel */}
      <VariablePanel
        elements={activeElements}
        composition={currentStrategy.elements}
        variables={currentStrategy.variables}
        onVariableChange={setStrategyVariable}
      />

      {/* Section: Element Browser + Composition (2-column) */}
      <div>
        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground mb-3">
          <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-primary/10 text-primary text-xs">🎯</span>
          策略元素组合
        </div>
        <div className="grid grid-cols-1 gap-4">
          <Card className="p-3 min-h-[200px]">
            <ElementBrowser
              elements={activeElements}
              selectedIds={selectedIds}
              platform={platform}
              topic={topic}
              onAdd={addElementToStrategy}
              onRecommend={() => {
                showToast.info('智能推荐已就绪', '请在右侧 Copilot 面板中点击「获取推荐」')
              }}
            />
          </Card>
          <Card className="p-3 min-h-[200px]">
            <StrategyCompositionPanel
              elements={activeElements}
              composition={currentStrategy.elements}
              onMove={moveElement}
              onRemove={removeElementFromStrategy}
              onPriorityChange={setElementPriority}
            />
          </Card>
        </div>
      </div>

      {(onSave || onCancel || onClear) && (
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-3 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              取消
            </button>
          )}
          {onClear && (
            <button
              type="button"
              onClick={onClear}
              className="px-3 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              清除
            </button>
          )}
          {onSave && (
            <button
              type="button"
              onClick={onSave}
              className="px-3 py-1.5 rounded-md text-xs font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              暂存节点
            </button>
          )}
        </div>
      )}
    </div>
  )
}
