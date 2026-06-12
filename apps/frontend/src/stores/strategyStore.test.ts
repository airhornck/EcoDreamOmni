import { describe, it, expect, beforeEach } from 'vitest'
import { useStrategyStore } from './strategyStore'
import type { StrategyElement } from '../types/strategy'

const sampleElement = (id: string, type: string): StrategyElement => ({
  element_id: id,
  element_type: type as StrategyElement['element_type'],
  name: `Element ${id}`,
  content: {},
  render_template: '',
  variables: [],
  source: 'manual',
  usage_count: 0,
  avg_engagement: {},
  effectiveness_score: 0.8,
  status: 'active',
  created_by: 'u1',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
})

describe('strategyStore — composition actions', () => {
  beforeEach(() => {
    useStrategyStore.setState({
      ...useStrategyStore.getState(),
      elements: [sampleElement('e1', 'hook_pattern'), sampleElement('e2', 'structure_framework')],
      currentStrategy: {
        name: null,
        elements: [],
        variables: {},
        custom_fragments: [],
      },
      activeSetId: null,
    })
  })

  it('addElementToStrategy should append element with default priority', () => {
    const store = useStrategyStore.getState()
    store.addElementToStrategy('e1')
    const current = useStrategyStore.getState().currentStrategy.elements
    expect(current).toHaveLength(1)
    expect(current[0].element_id).toBe('e1')
    expect(current[0].priority).toBe(5)
  })

  it('addElementToStrategy should not duplicate element ids', () => {
    const store = useStrategyStore.getState()
    store.addElementToStrategy('e1')
    store.addElementToStrategy('e1')
    expect(useStrategyStore.getState().currentStrategy.elements).toHaveLength(1)
  })

  it('moveElement should reorder and recompute priority descending', () => {
    const store = useStrategyStore.getState()
    store.addElementToStrategy('e1', { priority: 3 })
    store.addElementToStrategy('e2', { priority: 7 })
    store.moveElement(1, 0)
    const current = useStrategyStore.getState().currentStrategy.elements
    expect(current[0].element_id).toBe('e2')
    expect(current[0].priority).toBe(10)
    expect(current[1].priority).toBe(9)
  })

  it('removeElementFromStrategy should filter by id', () => {
    const store = useStrategyStore.getState()
    store.addElementToStrategy('e1')
    store.addElementToStrategy('e2')
    store.removeElementFromStrategy('e1')
    const current = useStrategyStore.getState().currentStrategy.elements
    expect(current).toHaveLength(1)
    expect(current[0].element_id).toBe('e2')
  })

  it('setStrategyVariable should upsert variables', () => {
    const store = useStrategyStore.getState()
    store.setStrategyVariable('topic', 'Test Topic')
    expect(useStrategyStore.getState().currentStrategy.variables.topic).toBe('Test Topic')
  })

  it('clearStrategy should reset composition state', () => {
    const store = useStrategyStore.getState()
    store.addElementToStrategy('e1')
    store.setStrategyVariable('topic', 'Test')
    store.clearStrategy()
    const state = useStrategyStore.getState()
    expect(state.currentStrategy.elements).toHaveLength(0)
    expect(Object.keys(state.currentStrategy.variables)).toHaveLength(0)
    expect(state.activeSetId).toBeNull()
  })
})

describe('strategyStore — browser selectors', () => {
  beforeEach(() => {
    useStrategyStore.setState({
      ...useStrategyStore.getState(),
      elements: [
        { ...sampleElement('e1', 'hook_pattern'), name: 'Hook Alpha' },
        { ...sampleElement('e2', 'structure_framework'), name: 'Structure Beta' },
      ],
      browser: {
        filterType: 'all',
        searchQuery: '',
        selectedIds: [],
        hoveredId: null,
        draggedId: null,
      },
    })
  })

  it('setBrowserFilter should filter by element type', () => {
    const store = useStrategyStore.getState()
    store.setBrowserFilter('hook_pattern')
    const filtered = useStrategyStore.getState().browser.filterType
    expect(filtered).toBe('hook_pattern')
  })

  it('toggleElementSelection should add and remove ids', () => {
    const store = useStrategyStore.getState()
    store.toggleElementSelection('e1')
    store.toggleElementSelection('e2')
    expect(useStrategyStore.getState().browser.selectedIds).toEqual(['e1', 'e2'])
    store.toggleElementSelection('e1')
    expect(useStrategyStore.getState().browser.selectedIds).toEqual(['e2'])
  })
})
