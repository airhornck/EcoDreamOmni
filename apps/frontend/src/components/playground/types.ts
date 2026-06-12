export interface NoteInput {
  title: string
  content: string
  cover_image_url?: string
  category: string
  tags: string[]
  metrics?: {
    likes: number
    collects: number
    comments: number
  }
}

export interface KeywordMatch {
  keyword: string
  position: number
  weight: number
}

export interface EmotionMatch extends KeywordMatch {
  intensity: number
}

export interface AnalysisReport {
  note_id: string
  structure_type: string
  structure_confidence: number
  viral_score: number
  scoring_breakdown: {
    completeness: number
    keyword_richness: number
    emotion_curve: number
    interaction_weight: number
    emoji_strategy: number
  }
  keyword_matches: {
    structure: KeywordMatch[]
    function: KeywordMatch[]
    emotion: EmotionMatch[]
    industry: KeywordMatch[]
    effect: KeywordMatch[]
  }
  title_analysis: {
    pattern: string
    contains_number: boolean
    contains_question: boolean
    length: number
  }
  hook_analysis: {
    hook_type: string
    hook_text: string
    effectiveness: number
  }
  body_analysis: {
    sections: number
    avg_section_length: number
    has_story: boolean
    has_data: boolean
  }
  cta_analysis: {
    cta_type: string
    cta_text: string
    effectiveness: number
  }
  emoji_analysis: {
    emoji_count: number
    emoji_density: string
    top_emojis: string[]
  }
  emotion_curve: Array<{
    segment: number
    emotion: string
    intensity: number
  }>
  success_factors: string[]
}

export interface ViralTemplate {
  template_id: string
  name: string
  source: string
  source_content_id: string
  structure_type: string
  prompt_template: string
  variables: Array<{
    name: string
    label: string
    type: string
    default_value: string
  }>
  constraints: {
    title_length: [number, number]
    body_section_min: number
    emoji_density: string
    hook_length: [number, number]
  }
}

export type LabTab = 'edit' | 'preview' | 'report' | 'template'

export type CopilotState = 'empty' | 'input_ready' | 'analyzing' | 'analyzed' | 'template_ready'
