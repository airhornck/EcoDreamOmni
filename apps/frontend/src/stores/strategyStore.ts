import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type {
  ContentStrategy,
  ElementType,
  StrategyElement,
  StrategyElementRef,
  StrategySet,
} from '../types/strategy'

// ──────────────────────────────────────────────────────────────────
// State shape
// ──────────────────────────────────────────────────────────────────

interface ElementBrowserState {
  /** Active filter in element library browser */
  filterType: ElementType | 'all'
  searchQuery: string
  selectedIds: string[]
  hoveredId: string | null
  draggedId: string | null
}

export interface StrategyState {
  // Library cache
  elements: StrategyElement[]
  elementsLoading: boolean
  elementsError: string | null

  // Sets cache
  sets: StrategySet[]
  setsLoading: boolean
  setsError: string | null

  // Current composition (live)
  currentStrategy: ContentStrategy
  activeSetId: string | null

  // Selection & DnD
  browser: ElementBrowserState

  // Recommendations cache
  recommendations: Record<string, StrategyElement[]>
  recommendationsLoading: boolean

  // Preview
  renderedPreview: string | null
  previewLoading: boolean
  previewError: string | null
}

// ──────────────────────────────────────────────────────────────────
// Actions
// ──────────────────────────────────────────────────────────────────

export interface StrategyActions {
  // Library cache actions
  setElements: (elements: StrategyElement[]) => void
  addElement: (element: StrategyElement) => void
  updateElementInCache: (elementId: string, patch: Partial<StrategyElement>) => void
  removeElementFromCache: (elementId: string) => void
  setElementsLoading: (loading: boolean) => void
  setElementsError: (error: string | null) => void

  // Sets cache actions
  setSets: (sets: StrategySet[]) => void
  addSet: (set: StrategySet) => void
  updateSetInCache: (setId: string, patch: Partial<StrategySet>) => void
  removeSetFromCache: (setId: string) => void
  setSetsLoading: (loading: boolean) => void
  setSetsError: (error: string | null) => void

  // Composition actions
  setCurrentStrategy: (strategy: Partial<ContentStrategy>) => void
  setActiveSetId: (setId: string | null) => void
  addElementToStrategy: (elementId: string, options?: { priority?: number; override_variables?: Record<string, string> }) => void
  removeElementFromStrategy: (elementId: string) => void
  moveElement: (oldIndex: number, newIndex: number) => void
  setElementPriority: (elementId: string, priority: number) => void
  setElementOverride: (elementId: string, variables: Record<string, string>) => void
  setStrategyVariable: (key: string, value: string) => void
  removeStrategyVariable: (key: string) => void
  addCustomFragment: (fragment: string) => void
  removeCustomFragment: (fragment: string) => void
  clearStrategy: () => void
  loadSetIntoStrategy: (set: StrategySet) => void

  // Browser state actions
  setBrowserFilter: (filterType: ElementType | 'all') => void
  setBrowserSearch: (query: string) => void
  toggleElementSelection: (elementId: string) => void
  clearElementSelection: () => void
  setHoveredElement: (elementId: string | null) => void
  setDraggedElement: (elementId: string | null) => void

  // Recommendations actions
  setRecommendations: (key: string, elements: StrategyElement[]) => void
  setRecommendationsLoading: (loading: boolean) => void

  // Preview actions
  setRenderedPreview: (preview: string | null) => void
  setPreviewLoading: (loading: boolean) => void
  setPreviewError: (error: string | null) => void
}

// ──────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────

const initialContentStrategy = (): ContentStrategy => ({
  name: null,
  elements: [],
  variables: {},
  custom_fragments: [],
})

const initialBrowserState = (): ElementBrowserState => ({
  filterType: 'all',
  searchQuery: '',
  selectedIds: [],
  hoveredId: null,
  draggedId: null,
})

const initialState = (): StrategyState => ({
  elements: [],
  elementsLoading: false,
  elementsError: null,

  sets: [],
  setsLoading: false,
  setsError: null,

  currentStrategy: initialContentStrategy(),
  activeSetId: null,

  browser: initialBrowserState(),

  recommendations: {},
  recommendationsLoading: false,

  renderedPreview: null,
  previewLoading: false,
  previewError: null,
})

// ──────────────────────────────────────────────────────────────────
// Store
// ──────────────────────────────────────────────────────────────────

export const useStrategyStore = create<StrategyState & StrategyActions>()(
  devtools(
    (set) => ({
      ...initialState(),

      // ── Library cache ────────────────────────────────────────────
      setElements: (elements) =>
        set({ elements }, false, 'setElements'),

      addElement: (element) =>
        set((state) => ({ elements: [element, ...state.elements] }), false, 'addElement'),

      updateElementInCache: (elementId, patch) =>
        set(
          (state) => ({
            elements: state.elements.map((e) =>
              e.element_id === elementId ? { ...e, ...patch } : e
            ),
          }),
          false,
          'updateElementInCache'
        ),

      removeElementFromCache: (elementId) =>
        set(
          (state) => ({
            elements: state.elements.filter((e) => e.element_id !== elementId),
          }),
          false,
          'removeElementFromCache'
        ),

      setElementsLoading: (loading) =>
        set({ elementsLoading: loading }, false, 'setElementsLoading'),

      setElementsError: (error) =>
        set({ elementsError: error }, false, 'setElementsError'),

      // ── Sets cache ───────────────────────────────────────────────
      setSets: (sets) =>
        set({ sets }, false, 'setSets'),

      addSet: (newSet) =>
        set((state) => ({ sets: [newSet, ...state.sets] }), false, 'addSet'),

      updateSetInCache: (setId, patch) =>
        set(
          (state) => ({
            sets: state.sets.map((s) => (s.set_id === setId ? { ...s, ...patch } : s)),
          }),
          false,
          'updateSetInCache'
        ),

      removeSetFromCache: (setId) =>
        set(
          (state) => ({ sets: state.sets.filter((s) => s.set_id !== setId) }),
          false,
          'removeSetFromCache'
        ),

      setSetsLoading: (loading) =>
        set({ setsLoading: loading }, false, 'setSetsLoading'),

      setSetsError: (error) =>
        set({ setsError: error }, false, 'setSetsError'),

      // ── Composition ──────────────────────────────────────────────
      setCurrentStrategy: (strategy) =>
        set(
          (state) => ({ currentStrategy: { ...state.currentStrategy, ...strategy } }),
          false,
          'setCurrentStrategy'
        ),

      setActiveSetId: (setId) =>
        set({ activeSetId: setId }, false, 'setActiveSetId'),

      addElementToStrategy: (elementId, options = {}) =>
        set((state) => {
          if (state.currentStrategy.elements.some((el) => el.element_id === elementId)) {
            return state
          }
          const element = state.elements.find((el) => el.element_id === elementId)
          return {
            currentStrategy: {
              ...state.currentStrategy,
              elements: [
                ...state.currentStrategy.elements,
                {
                  element_id: elementId,
                  element_type: element?.element_type,
                  priority: options.priority ?? 5,
                  override_variables: options.override_variables ?? {},
                },
              ],
            },
          }
        }, false, 'addElementToStrategy'),

      removeElementFromStrategy: (elementId) =>
        set(
          (state) => ({
            currentStrategy: {
              ...state.currentStrategy,
              elements: state.currentStrategy.elements.filter(
                (el) => el.element_id !== elementId
              ),
            },
          }),
          false,
          'removeElementFromStrategy'
        ),

      moveElement: (oldIndex, newIndex) =>
        set((state) => {
          const arr = [...state.currentStrategy.elements]
          const [moved] = arr.splice(oldIndex, 1)
          arr.splice(newIndex, 0, moved)
          const recomputed = arr.map((el, i) => ({
            ...el,
            priority: Math.max(1, 10 - i),
          }))
          return {
            currentStrategy: {
              ...state.currentStrategy,
              elements: recomputed,
            },
          }
        }, false, 'moveElement'),

      setElementPriority: (elementId, priority) =>
        set(
          (state) => ({
            currentStrategy: {
              ...state.currentStrategy,
              elements: state.currentStrategy.elements.map((el) =>
                el.element_id === elementId ? { ...el, priority } : el
              ),
            },
          }),
          false,
          'setElementPriority'
        ),

      setElementOverride: (elementId, variables) =>
        set(
          (state) => ({
            currentStrategy: {
              ...state.currentStrategy,
              elements: state.currentStrategy.elements.map((el) =>
                el.element_id === elementId
                  ? { ...el, override_variables: { ...el.override_variables, ...variables } }
                  : el
              ),
            },
          }),
          false,
          'setElementOverride'
        ),

      setStrategyVariable: (key, value) =>
        set(
          (state) => ({
            currentStrategy: {
              ...state.currentStrategy,
              variables: { ...state.currentStrategy.variables, [key]: value },
            },
          }),
          false,
          'setStrategyVariable'
        ),

      removeStrategyVariable: (key) =>
        set((state) => {
          const next = { ...state.currentStrategy.variables }
          delete next[key]
          return {
            currentStrategy: {
              ...state.currentStrategy,
              variables: next,
            },
          }
        }, false, 'removeStrategyVariable'),

      addCustomFragment: (fragment) =>
        set((state) => {
          if (state.currentStrategy.custom_fragments.includes(fragment)) return state
          return {
            currentStrategy: {
              ...state.currentStrategy,
              custom_fragments: [...state.currentStrategy.custom_fragments, fragment],
            },
          }
        }, false, 'addCustomFragment'),

      removeCustomFragment: (fragment) =>
        set(
          (state) => ({
            currentStrategy: {
              ...state.currentStrategy,
              custom_fragments: state.currentStrategy.custom_fragments.filter(
                (f) => f !== fragment
              ),
            },
          }),
          false,
          'removeCustomFragment'
        ),

      clearStrategy: () =>
        set(
          {
            currentStrategy: initialContentStrategy(),
            activeSetId: null,
            renderedPreview: null,
          },
          false,
          'clearStrategy'
        ),

      loadSetIntoStrategy: (strategySet) =>
        set(
          {
            currentStrategy: {
              name: strategySet.name,
              elements: strategySet.element_refs.map((ref) => ({
                element_id: ref.element_id,
                priority: ref.priority ?? 5,
                override_variables: ref.override_variables ?? {},
              })),
              variables: { ...strategySet.default_variables },
              custom_fragments: [],
              methodology_stage_id: strategySet.methodology_stage_id ?? null,
              content_series_id: null,
              timeline_event_id: null,
              persona_id: null,
              persona_story_id: null,
              node_id: null,
            },
            activeSetId: strategySet.set_id,
          },
          false,
          'loadSetIntoStrategy'
        ),

      // ── Browser state ────────────────────────────────────────────
      setBrowserFilter: (filterType) =>
        set((state) => ({ browser: { ...state.browser, filterType } }), false, 'setBrowserFilter'),

      setBrowserSearch: (query) =>
        set((state) => ({ browser: { ...state.browser, searchQuery: query } }), false, 'setBrowserSearch'),

      toggleElementSelection: (elementId) =>
        set((state) => {
          const ids = state.browser.selectedIds
          const selectedIds = ids.includes(elementId)
            ? ids.filter((id) => id !== elementId)
            : [...ids, elementId]
          return { browser: { ...state.browser, selectedIds } }
        }, false, 'toggleElementSelection'),

      clearElementSelection: () =>
        set(
          (state) => ({ browser: { ...state.browser, selectedIds: [] } }),
          false,
          'clearElementSelection'
        ),

      setHoveredElement: (elementId) =>
        set(
          (state) => ({ browser: { ...state.browser, hoveredId: elementId } }),
          false,
          'setHoveredElement'
        ),

      setDraggedElement: (elementId) =>
        set(
          (state) => ({ browser: { ...state.browser, draggedId: elementId } }),
          false,
          'setDraggedElement'
        ),

      // ── Recommendations ──────────────────────────────────────────
      setRecommendations: (key, elements) =>
        set(
          (state) => ({
            recommendations: { ...state.recommendations, [key]: elements },
          }),
          false,
          'setRecommendations'
        ),

      setRecommendationsLoading: (loading) =>
        set({ recommendationsLoading: loading }, false, 'setRecommendationsLoading'),

      // ── Preview ──────────────────────────────────────────────────
      setRenderedPreview: (preview) =>
        set({ renderedPreview: preview }, false, 'setRenderedPreview'),

      setPreviewLoading: (loading) =>
        set({ previewLoading: loading }, false, 'setPreviewLoading'),

      setPreviewError: (error) =>
        set({ previewError: error }, false, 'setPreviewError'),
    }),
    { name: 'strategy-store' }
  )
)

// ──────────────────────────────────────────────────────────────────
// Selectors
// ──────────────────────────────────────────────────────────────────

export function selectCurrentElements(state: StrategyState): StrategyElementRef[] {
  return state.currentStrategy.elements
}

export function selectStrategyElementCount(state: StrategyState): number {
  return state.currentStrategy.elements.length
}

export function selectStrategyVariables(state: StrategyState): Record<string, string> {
  return state.currentStrategy.variables
}

export function selectBrowserFilteredElements(state: StrategyState): StrategyElement[] {
  const { elements } = state
  const { filterType, searchQuery } = state.browser
  const q = searchQuery.trim().toLowerCase()
  return elements.filter((el) => {
    if (filterType !== 'all' && el.element_type !== filterType) return false
    if (!q) return true
    return (
      el.name.toLowerCase().includes(q) ||
      (el.description ?? '').toLowerCase().includes(q) ||
      (el.category ?? '').toLowerCase().includes(q)
    )
  })
}

export function selectElementsByType(state: StrategyState, type: ElementType): StrategyElement[] {
  return state.elements.filter((el) => el.element_type === type && el.status === 'active')
}
