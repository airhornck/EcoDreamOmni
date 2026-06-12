import { apiClient } from '../lib/api'
import type {
  ContentStrategy,
  ElementFilters,
  ElementRecommendParams,
  StrategyElement,
  StrategySet,
} from '../types/strategy'

const API_BASE = '/api'

function buildQuery(params: Record<string, string | number | undefined>): string {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') q.append(k, String(v))
  }
  const s = q.toString()
  return s ? `?${s}` : ''
}

// ═══════════════════════════════════════════════════════════════════
// Strategy Elements
// ═══════════════════════════════════════════════════════════════════

export async function fetchStrategyElements(
  filters: ElementFilters = {}
): Promise<StrategyElement[]> {
  const query = buildQuery({
    element_type: filters.element_type,
    platform: filters.platform,
    source: filters.source,
    methodology_stage_id: filters.methodology_stage_id,
    status: filters.status ?? 'active',
    category: filters.category,
    search: filters.search,
    sort_by: filters.sort_by,
    sort_order: filters.sort_order,
    limit: filters.limit ?? 50,
    offset: filters.offset ?? 0,
  })
  return apiClient<StrategyElement[]>(`${API_BASE}/strategy-elements${query}`)
}

export async function createStrategyElement(
  data: Partial<StrategyElement>
): Promise<StrategyElement> {
  return apiClient<StrategyElement>(`${API_BASE}/strategy-elements`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function fetchStrategyElement(elementId: string): Promise<StrategyElement> {
  return apiClient<StrategyElement>(`${API_BASE}/strategy-elements/${elementId}`)
}

export async function updateStrategyElement(
  elementId: string,
  data: Partial<StrategyElement>
): Promise<StrategyElement> {
  return apiClient<StrategyElement>(`${API_BASE}/strategy-elements/${elementId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteStrategyElement(elementId: string): Promise<void> {
  await apiClient<void>(`${API_BASE}/strategy-elements/${elementId}`, {
    method: 'DELETE',
  })
}

export async function fetchStrategyElementRecommendations(
  params: ElementRecommendParams
): Promise<StrategyElement[]> {
  const query = buildQuery({
    topic: params.topic,
    platform: params.platform,
    methodology_stage_id: params.methodology_stage_id,
    limit: params.limit ?? 6,
  })
  return apiClient<StrategyElement[]>(`${API_BASE}/strategy-elements/recommend${query}`)
}

export interface RenderPreviewResponse {
  element_id: string
  element_type: string
  rendered_fragment: string
  target_layer: string
}

export async function renderStrategyElementPreview(
  elementId: string,
  variables: Record<string, string>,
  topic?: string,
  platform?: string
): Promise<RenderPreviewResponse> {
  return apiClient<RenderPreviewResponse>(`${API_BASE}/strategy-elements/${elementId}/render`, {
    method: 'POST',
    body: JSON.stringify({ variables, topic, platform }),
  })
}

// ═══════════════════════════════════════════════════════════════════
// Strategy Sets
// ═══════════════════════════════════════════════════════════════════

export async function fetchStrategySets(
  filters: { platform?: string; search?: string } = {}
): Promise<StrategySet[]> {
  const query = buildQuery({
    platform: filters.platform,
    search: filters.search,
    status: 'active',
    limit: 50,
  })
  return apiClient<StrategySet[]>(`${API_BASE}/strategy-sets${query}`)
}

export async function createStrategySet(data: Partial<StrategySet>): Promise<StrategySet> {
  return apiClient<StrategySet>(`${API_BASE}/strategy-sets`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function fetchStrategySet(setId: string): Promise<StrategySet> {
  return apiClient<StrategySet>(`${API_BASE}/strategy-sets/${setId}`)
}

export async function updateStrategySet(
  setId: string,
  data: Partial<StrategySet>
): Promise<StrategySet> {
  return apiClient<StrategySet>(`${API_BASE}/strategy-sets/${setId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteStrategySet(setId: string): Promise<void> {
  await apiClient<void>(`${API_BASE}/strategy-sets/${setId}`, {
    method: 'DELETE',
  })
}

// ═══════════════════════════════════════════════════════════════════
// Playground — extract elements from viral analysis
// ═══════════════════════════════════════════════════════════════════

export interface ExtractElementsResponse {
  elements: StrategyElement[]
  saved_element_ids: string[]
  strategy_set_id?: string
}

export async function extractStrategyElementsFromReport(
  report: Record<string, unknown>,
  options: {
    platform?: string
    save_to_library?: boolean
    save_as_set?: boolean
    set_name?: string
  } = {}
): Promise<ExtractElementsResponse> {
  return apiClient<ExtractElementsResponse>(`${API_BASE}/playground/elements`, {
    method: 'POST',
    body: JSON.stringify({
      report,
      platform: options.platform ?? 'xiaohongshu',
      save_to_library: options.save_to_library ?? true,
      save_as_set: options.save_as_set ?? false,
      set_name: options.set_name,
    }),
  })
}

// ═══════════════════════════════════════════════════════════════════
// Prompt Composition (local-side helpers)
// ═══════════════════════════════════════════════════════════════════

export function buildContentStrategy(
  elementRefs: { element_id: string; priority?: number; override_variables?: Record<string, string> }[],
  variables: Record<string, string>,
  metadata: {
    name?: string
    methodology_stage_id?: string
    timeline_event_id?: string
    persona_id?: string
  } = {}
): ContentStrategy {
  return {
    name: metadata.name ?? null,
    elements: elementRefs.map((ref, index) => ({
      element_id: ref.element_id,
      priority: ref.priority ?? Math.max(1, 5 - index),
      override_variables: ref.override_variables ?? {},
    })),
    variables,
    custom_fragments: [],
    methodology_stage_id: metadata.methodology_stage_id ?? null,
    timeline_event_id: metadata.timeline_event_id ?? null,
    persona_id: metadata.persona_id ?? null,
    persona_story_id: null,
    node_id: null,
    content_series_id: null,
  }
}
