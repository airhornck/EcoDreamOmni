import { useCallback } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, X, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { Badge } from '../../../../components/ui/Badge'
import { EmptyState } from '../../../../components/ui/EmptyState'
import type { StrategyElement, StrategyElementRef } from '../../../../types/strategy'
import { ELEMENT_TYPE_ICONS, ELEMENT_TYPE_LABELS } from '../../../../types/strategy'

interface StrategyCompositionPanelProps {
  elements: StrategyElement[]
  composition: StrategyElementRef[]
  onMove: (oldIndex: number, newIndex: number) => void
  onRemove: (elementId: string) => void
  onPriorityChange?: (elementId: string, priority: number) => void
}

function SortableItem({
  element,
  refItem,
  index,
  onRemove,
  onPriorityChange,
}: {
  element: StrategyElement
  refItem: StrategyElementRef
  index: number
  onRemove: (id: string) => void
  onPriorityChange?: (id: string, p: number) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: refItem.element_id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 50 : undefined,
    opacity: isDragging ? 0.9 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`rounded-lg border bg-card transition-shadow ${
        isDragging ? 'shadow-lg ring-2 ring-primary/20' : 'shadow-sm'
      }`}
    >
      <div className="flex items-center gap-2 p-3">
        {/* Drag handle */}
        <button
          {...attributes}
          {...listeners}
          className="touch-none text-muted-foreground hover:text-foreground cursor-grab active:cursor-grabbing p-0.5 rounded"
        >
          <GripVertical className="w-4 h-4" />
        </button>

        {/* Priority badge */}
        <div className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold shrink-0">
          {refItem.priority ?? index + 1}
        </div>

        {/* Icon + Name */}
        <span className="text-base shrink-0">{ELEMENT_TYPE_ICONS[element.element_type]}</span>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate">{element.name}</div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => setExpanded((v) => !v)}
            className="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => onRemove(refItem.element_id)}
            className="p-1 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-3 pb-3 pt-0 border-t border-border/50">
          <div className="flex items-center gap-1.5 mt-2 flex-wrap">
            <Badge variant="primary" className="text-[10px]">
              {ELEMENT_TYPE_LABELS[element.element_type]}
            </Badge>
            {element.platform && (
              <Badge variant="default" className="text-[10px]">
                {element.platform}
              </Badge>
            )}
          </div>
          {element.description && (
            <p className="text-xs text-muted-foreground mt-2">{element.description}</p>
          )}
          {onPriorityChange && (
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-muted-foreground">优先级:</span>
              <input
                type="range"
                min={1}
                max={10}
                value={refItem.priority ?? 5}
                onChange={(e) => onPriorityChange(refItem.element_id, Number(e.target.value))}
                className="flex-1 h-1 accent-primary"
              />
              <span className="text-xs font-medium w-4 text-right">{refItem.priority ?? 5}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function StrategyCompositionPanel({
  elements,
  composition,
  onMove,
  onRemove,
  onPriorityChange,
}: StrategyCompositionPanelProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event
      if (over && active.id !== over.id) {
        const oldIndex = composition.findIndex((c) => c.element_id === active.id)
        const newIndex = composition.findIndex((c) => c.element_id === over.id)
        if (oldIndex !== -1 && newIndex !== -1) {
          onMove(oldIndex, newIndex)
        }
      }
    },
    [composition, onMove]
  )

  const resolved = composition
    .map((ref) => {
      const el = elements.find((e) => e.element_id === ref.element_id)
      return el ? { ref, el } : null
    })
    .filter(Boolean) as { ref: StrategyElementRef; el: StrategyElement }[]

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold">
          策略组合
          <span className="ml-1.5 text-xs text-muted-foreground font-normal">
            ({composition.length})
          </span>
        </h4>
      </div>

      {composition.length === 0 ? (
        <EmptyState
          emoji="🎯"
          title="尚未选择策略元素"
          description="从左侧元素库点击添加，或拖拽调整顺序"
          className="flex-1 py-8 border border-dashed border-border rounded-lg"
        />
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext
            items={composition.map((c) => c.element_id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-2 overflow-y-auto pr-1">
              {resolved.map(({ ref, el }, index) => (
                <SortableItem
                  key={ref.element_id}
                  element={el}
                  refItem={ref}
                  index={index}
                  onRemove={onRemove}
                  onPriorityChange={onPriorityChange}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}
    </div>
  )
}
