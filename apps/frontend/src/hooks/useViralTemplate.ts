import { useMutation } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import type { AnalysisReport, ViralTemplate } from '../components/playground/types'

interface TemplateResponse {
  code: string
  data: ViralTemplate
}

export function useViralTemplate() {
  return useMutation<ViralTemplate, Error, { analysis_report: AnalysisReport; template_name: string }>({
    mutationFn: async (payload) => {
      const res = await apiClient<TemplateResponse>('/api/playground/template', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      return res.data
    },
  })
}
