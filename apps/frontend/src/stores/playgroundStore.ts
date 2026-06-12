import { create } from 'zustand'
import type {
  NoteInput,
  AnalysisReport,
  ViralTemplate,
  LabTab,
  CopilotState,
} from '../components/playground/types'

// Legacy types (keep for backward compat during refactor)
export interface ViralContent {
  url?: string
  screenshot?: string
  text?: string
}

export interface ParsedStructure {
  hook_pattern: string
  body_structure: string
  cta_pattern: string
  tone: string
  keywords: string[]
}

export interface ContentTemplate {
  id: string
  name: string
  prompt_template: string
  variables: TemplateVariable[]
}

export interface TemplateVariable {
  key: string
  label: string
  default_value: string
  current_value: string
}

export interface GeneratedContent {
  title: string
  body: string
  hashtags: string[]
  diff?: { before: string; after: string }
}

interface LabState {
  // ─── v4.0 ViralAnalyzer (new)
  noteInput: NoteInput | null
  analysisReport: AnalysisReport | null
  isAnalyzing: boolean
  analysisError: string | null
  viralTemplate: ViralTemplate | null
  isGeneratingTemplate: boolean
  templateError: string | null
  activeTab: LabTab
  copilotState: CopilotState

  // ─── Legacy (keep during refactor)
  input: ViralContent
  parsed: ParsedStructure | null
  isParsing: boolean
  parseError: string | null
  templates: ContentTemplate[]
  selectedTemplateId: string | null
  variables: TemplateVariable[]
  generated: GeneratedContent | null
  isGenerating: boolean
  generateError: string | null

  // ─── Actions
  setNoteInput: (noteInput: NoteInput | null) => void
  setAnalysisReport: (report: AnalysisReport | null) => void
  setIsAnalyzing: (v: boolean) => void
  setAnalysisError: (e: string | null) => void
  setViralTemplate: (template: ViralTemplate | null) => void
  setIsGeneratingTemplate: (v: boolean) => void
  setTemplateError: (e: string | null) => void
  setActiveTab: (tab: LabTab) => void
  setCopilotState: (state: CopilotState) => void

  // Legacy actions
  setInput: (input: Partial<ViralContent>) => void
  setParsed: (parsed: ParsedStructure | null) => void
  setIsParsing: (v: boolean) => void
  setParseError: (e: string | null) => void
  setTemplates: (templates: ContentTemplate[]) => void
  selectTemplate: (id: string) => void
  updateVariable: (key: string, value: string) => void
  setGenerated: (generated: GeneratedContent | null) => void
  setIsGenerating: (v: boolean) => void
  setGenerateError: (e: string | null) => void
  reset: () => void
}

const initialState = {
  // v4.0
  noteInput: null,
  analysisReport: null,
  isAnalyzing: false,
  analysisError: null,
  viralTemplate: null,
  isGeneratingTemplate: false,
  templateError: null,
  activeTab: 'edit' as LabTab,
  copilotState: 'empty' as CopilotState,

  // Legacy
  input: {},
  parsed: null,
  isParsing: false,
  parseError: null,
  templates: [],
  selectedTemplateId: null,
  variables: [],
  generated: null,
  isGenerating: false,
  generateError: null,
}

export const usePlaygroundStore = create<LabState>((set) => ({
  ...initialState,

  // v4.0 actions
  setNoteInput: (noteInput) => {
    set({ noteInput })
    if (noteInput && noteInput.title && noteInput.content) {
      set({ copilotState: 'input_ready' })
    } else {
      set({ copilotState: 'empty' })
    }
  },
  setAnalysisReport: (analysisReport) => {
    set({ analysisReport })
    if (analysisReport) {
      set({ copilotState: 'analyzed', activeTab: 'preview' })
    }
  },
  setIsAnalyzing: (isAnalyzing) => {
    set({ isAnalyzing })
    if (isAnalyzing) {
      set({ copilotState: 'analyzing' })
    }
  },
  setAnalysisError: (analysisError) => set({ analysisError }),
  setViralTemplate: (viralTemplate) => {
    set({ viralTemplate })
    if (viralTemplate) {
      set({ copilotState: 'template_ready', activeTab: 'template' })
    }
  },
  setIsGeneratingTemplate: (isGeneratingTemplate) => set({ isGeneratingTemplate }),
  setTemplateError: (templateError) => set({ templateError }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setCopilotState: (copilotState) => set({ copilotState }),

  // Legacy actions
  setInput: (input) => set((s) => ({ input: { ...s.input, ...input } })),
  setParsed: (parsed) => set({ parsed }),
  setIsParsing: (isParsing) => set({ isParsing }),
  setParseError: (parseError) => set({ parseError }),
  setTemplates: (templates) => set({ templates }),
  selectTemplate: (selectedTemplateId) =>
    set((s) => {
      const tmpl = s.templates.find((t) => t.id === selectedTemplateId)
      return {
        selectedTemplateId,
        variables: tmpl ? tmpl.variables.map((v) => ({ ...v })) : [],
      }
    }),
  updateVariable: (key, value) =>
    set((s) => ({
      variables: s.variables.map((v) => (v.key === key ? { ...v, current_value: value } : v)),
    })),
  setGenerated: (generated) => set({ generated }),
  setIsGenerating: (isGenerating) => set({ isGenerating }),
  setGenerateError: (generateError) => set({ generateError }),
  reset: () => set(initialState),
}))
