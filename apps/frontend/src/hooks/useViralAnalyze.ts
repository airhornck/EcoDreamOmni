import { useMutation } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import type { NoteInput, AnalysisReport } from '../components/playground/types'

interface AnalyzeResponse {
  code: string
  data: AnalysisReport
}

export function useViralAnalyze() {
  return useMutation<AnalysisReport, Error, NoteInput>({
    mutationFn: async (input) => {
      const res = await apiClient<AnalyzeResponse>('/api/playground/analyze', {
        method: 'POST',
        body: JSON.stringify(input),
      })
      return res.data
    },
  })
}
