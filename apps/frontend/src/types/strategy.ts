/** Strategy Element Architecture type definitions — v4.0 */

export type ElementType =
  | 'structure_framework'
  | 'hook_pattern'
  | 'body_structure'
  | 'cta_pattern'
  | 'keyword_strategy'
  | 'emotion_curve'
  | 'engagement_formula'
  | 'scene_anchor'
  | 'persona'
  | 'persona_story'
  | 'content_series'
  | 'timeline_event'
  | 'methodology_stage'
  | 'platform_style'
  | 'brand_knowledge'
  | 'custom_fragment'
  | 'safety_constraint'

export type ElementSource = 'manual' | 'viral_analyzer' | 'ai_generated' | 'system'
export type ElementStatus = 'active' | 'deprecated' | 'draft'

export interface TemplateVariable {
  name: string
  label: string
  type: string
  default_value?: string | null
}

export interface StrategyElement {
  element_id: string
  element_type: ElementType
  element_subtype?: string | null
  name: string
  description?: string | null
  content: Record<string, unknown>
  render_template: string
  variables: TemplateVariable[]
  source: ElementSource
  source_content_id?: string | null
  platform?: string | null
  content_format?: string | null
  methodology_stage_id?: string | null
  category?: string | null
  usage_count: number
  avg_engagement: Record<string, unknown>
  effectiveness_score: number
  status: ElementStatus
  created_by: string
  created_at: string
  updated_at: string
}

export interface StrategyElementRef {
  element_id: string
  element_type?: ElementType
  priority?: number
  override_variables?: Record<string, string>
  override_content?: Record<string, unknown>
}

export interface StrategySet {
  set_id: string
  name: string
  description?: string | null
  element_refs: StrategyElementRef[]
  default_variables: Record<string, string>
  source: ElementSource
  source_content_id?: string | null
  platform?: string | null
  content_format?: string | null
  methodology_stage_id?: string | null
  category?: string | null
  usage_count: number
  avg_engagement: Record<string, unknown>
  status: ElementStatus
  created_by: string
  created_at: string
  updated_at: string
}

export interface ContentStrategy {
  strategy_id?: string | null
  name?: string | null
  elements: StrategyElementRef[]
  variables: Record<string, string>
  custom_fragments: string[]
  persona_id?: string | null
  persona_story_id?: string | null
  node_id?: string | null
  content_series_id?: string | null
  timeline_event_id?: string | null
  methodology_stage_id?: string | null
}

export interface ElementFilters {
  element_type?: ElementType
  platform?: string
  source?: ElementSource
  methodology_stage_id?: string
  status?: ElementStatus
  category?: string
  search?: string
  sort_by?: 'usage_count' | 'effectiveness_score' | 'created_at'
  sort_order?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface ElementRecommendParams {
  topic: string
  platform: string
  methodology_stage_id?: string
  element_types?: ElementType[]
  limit?: number
}

export const ELEMENT_TYPE_LABELS: Record<ElementType, string> = {
  structure_framework: '结构框架',
  hook_pattern: 'Hook模式',
  body_structure: '正文结构',
  cta_pattern: 'CTA模式',
  keyword_strategy: '关键词策略',
  emotion_curve: '情感曲线',
  engagement_formula: '互动公式',
  scene_anchor: '场景切入',
  persona: '人设',
  persona_story: '故事线',
  content_series: '内容系列',
  timeline_event: '时间线',
  methodology_stage: '方法论',
  platform_style: '平台风格',
  brand_knowledge: '品牌知识',
  custom_fragment: '自定义片段',
  safety_constraint: '内容安全约束',
}

export const ELEMENT_TYPE_ICONS: Record<ElementType, string> = {
  structure_framework: '🏗️',
  hook_pattern: '🪝',
  body_structure: '📄',
  cta_pattern: '📢',
  keyword_strategy: '🔑',
  emotion_curve: '📊',
  engagement_formula: '⚡',
  scene_anchor: '🎯',
  persona: '👤',
  persona_story: '📖',
  content_series: '📂',
  timeline_event: '📅',
  methodology_stage: '🎓',
  platform_style: '🎨',
  brand_knowledge: '📚',
  custom_fragment: '✏️',
  safety_constraint: '🛡️',
}
