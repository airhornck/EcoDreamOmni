import { create } from 'zustand'

export type SuggestionType = 'OPTIMIZE' | 'ADD' | 'REMOVE' | 'WARNING' | 'INFO'

export interface InlineSuggestion {
  id: string
  type: SuggestionType
  title: string
  description: string
  targetId: string
  diff?: { before: string; after: string }
}

interface InlineAIState {
  suggestions: InlineSuggestion[]
  dismissedIds: string[]
  selectedTargetId: string | null

  showSuggestions: (suggestions: InlineSuggestion[]) => void
  dismiss: (id: string) => void
  apply: (id: string) => void
  selectTarget: (targetId: string | null) => void
  clear: () => void
}

export const useInlineAIStore = create<InlineAIState>((set, get) => ({
  suggestions: [],
  dismissedIds: [],
  selectedTargetId: null,

  showSuggestions: (suggestions) =>
    set((s) => ({
      suggestions: [...s.suggestions, ...suggestions.filter((sg) => !s.dismissedIds.includes(sg.id))],
    })),

  dismiss: (id) =>
    set((s) => ({
      dismissedIds: [...s.dismissedIds, id],
      suggestions: s.suggestions.filter((sg) => sg.id !== id),
    })),

  apply: (id) => {
    const sg = get().suggestions.find((s) => s.id === id)
    if (sg) {
      console.log('Inline AI applied:', sg)
    }
    set((s) => ({
      suggestions: s.suggestions.filter((sg) => sg.id !== id),
    }))
  },

  selectTarget: (selectedTargetId) => set({ selectedTargetId }),

  clear: () => set({ suggestions: [], selectedTargetId: null }),
}))
