import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from '@tanstack/react-query'
import {
  createStrategyElement,
  createStrategySet,
  deleteStrategyElement,
  deleteStrategySet,
  extractStrategyElementsFromReport,
  fetchStrategyElement,
  fetchStrategyElementRecommendations,
  fetchStrategyElements,
  fetchStrategySet,
  fetchStrategySets,
  renderStrategyElementPreview,
  updateStrategyElement,
  updateStrategySet,
} from '../api/strategyApi'
import type {
  ElementFilters,
  ElementRecommendParams,
  StrategyElement,
  StrategySet,
} from '../types/strategy'

const STRATEGY_KEYS = {
  all: ['strategy'] as const,
  elements: () => [...STRATEGY_KEYS.all, 'elements'] as const,
  element: (id: string) => [...STRATEGY_KEYS.elements(), id] as const,
  elementRecommendations: (params: ElementRecommendParams) =>
    [...STRATEGY_KEYS.elements(), 'recommend', params] as const,
  sets: () => [...STRATEGY_KEYS.all, 'sets'] as const,
  set: (id: string) => [...STRATEGY_KEYS.sets(), id] as const,
}

// ── Elements ──────────────────────────────────────────────────────

export function useStrategyElements(
  filters: ElementFilters = {},
  options?: Omit<UseQueryOptions<StrategyElement[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<StrategyElement[], Error>({
    queryKey: STRATEGY_KEYS.elements(),
    queryFn: () => fetchStrategyElements(filters),
    ...options,
  })
}

export function useStrategyElement(elementId: string, enabled = true) {
  return useQuery<StrategyElement, Error>({
    queryKey: STRATEGY_KEYS.element(elementId),
    queryFn: () => fetchStrategyElement(elementId),
    enabled: !!elementId && enabled,
  })
}

export function useStrategyElementRecommendations(
  params: ElementRecommendParams,
  enabled = true
) {
  return useQuery<StrategyElement[], Error>({
    queryKey: STRATEGY_KEYS.elementRecommendations(params),
    queryFn: () => fetchStrategyElementRecommendations(params),
    enabled: !!params.topic && enabled,
  })
}

export function useCreateStrategyElement() {
  const qc = useQueryClient()
  return useMutation<StrategyElement, Error, Partial<StrategyElement>>({
    mutationFn: createStrategyElement,
    onSuccess: () => qc.invalidateQueries({ queryKey: STRATEGY_KEYS.elements() }),
  })
}

export function useUpdateStrategyElement() {
  const qc = useQueryClient()
  return useMutation<StrategyElement, Error, { elementId: string; data: Partial<StrategyElement> }>({
    mutationFn: ({ elementId, data }) => updateStrategyElement(elementId, data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: STRATEGY_KEYS.elements() })
      qc.invalidateQueries({ queryKey: STRATEGY_KEYS.element(vars.elementId) })
    },
  })
}

export function useDeleteStrategyElement() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: deleteStrategyElement,
    onSuccess: () => qc.invalidateQueries({ queryKey: STRATEGY_KEYS.elements() }),
  })
}

export function useRenderStrategyElementPreview() {
  return useMutation<
    { element_id: string; element_type: string; rendered_fragment: string; target_layer: string },
    Error,
    { elementId: string; variables: Record<string, string>; topic?: string; platform?: string }
  >({
    mutationFn: ({ elementId, variables, topic, platform }) =>
      renderStrategyElementPreview(elementId, variables, topic, platform),
  })
}

// ── Sets ──────────────────────────────────────────────────────────

export function useStrategySets(
  filters: { platform?: string; search?: string } = {},
  options?: Omit<UseQueryOptions<StrategySet[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<StrategySet[], Error>({
    queryKey: STRATEGY_KEYS.sets(),
    queryFn: () => fetchStrategySets(filters),
    ...options,
  })
}

export function useStrategySet(setId: string, enabled = true) {
  return useQuery<StrategySet, Error>({
    queryKey: STRATEGY_KEYS.set(setId),
    queryFn: () => fetchStrategySet(setId),
    enabled: !!setId && enabled,
  })
}

export function useCreateStrategySet() {
  const qc = useQueryClient()
  return useMutation<StrategySet, Error, Partial<StrategySet>>({
    mutationFn: createStrategySet,
    onSuccess: () => qc.invalidateQueries({ queryKey: STRATEGY_KEYS.sets() }),
  })
}

export function useUpdateStrategySet() {
  const qc = useQueryClient()
  return useMutation<StrategySet, Error, { setId: string; data: Partial<StrategySet> }>({
    mutationFn: ({ setId, data }) => updateStrategySet(setId, data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: STRATEGY_KEYS.sets() })
      qc.invalidateQueries({ queryKey: STRATEGY_KEYS.set(vars.setId) })
    },
  })
}

export function useDeleteStrategySet() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: deleteStrategySet,
    onSuccess: () => qc.invalidateQueries({ queryKey: STRATEGY_KEYS.sets() }),
  })
}

// ── Playground extract ────────────────────────────────────────────

export function useExtractStrategyElementsFromReport() {
  const qc = useQueryClient()
  return useMutation<
    { elements: StrategyElement[]; saved_element_ids: string[]; strategy_set_id?: string },
    Error,
    {
      report: Record<string, unknown>
      platform?: string
      save_to_library?: boolean
      save_as_set?: boolean
      set_name?: string
    }
  >({
    mutationFn: ({ report, ...options }) => extractStrategyElementsFromReport(report, options),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: STRATEGY_KEYS.elements() })
      qc.invalidateQueries({ queryKey: STRATEGY_KEYS.sets() })
    },
  })
}
