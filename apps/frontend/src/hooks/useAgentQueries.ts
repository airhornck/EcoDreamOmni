import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/api'
import type { Agent, AgentRecommendation } from '../types/api'

function buildUrl(path: string, params: Record<string, string>): string {
  const qs = new URLSearchParams(params).toString()
  return qs ? `${path}?${qs}` : path
}

const agentKeys = {
  all: () => ['agents'] as const,
  list: (filters: Record<string, string>) => ['agents', 'list', filters] as const,
  recommend: (params: Record<string, string>) => ['agents', 'recommend', params] as const,
}

/** 获取可用 Agent 列表（支持 platform/format 筛选） */
export function useAgents(filters?: { platform?: string; format?: string }) {
  return useQuery({
    queryKey: agentKeys.list(filters || {}),
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (filters?.platform) params.platform = filters.platform
      if (filters?.format) params.format = filters.format
      return apiClient<Agent[]>(buildUrl('/api/agents', params))
    },
    staleTime: 30000,
    retry: 2,
  })
}

/** 智能推荐 Agent（基于 platform + format + persona） */
export function useRecommendedAgent(params: {
  platform: string
  format: string
  personaId?: string
  accountId?: string
}) {
  return useQuery({
    queryKey: agentKeys.recommend({
      platform: params.platform,
      format: params.format,
      ...(params.personaId ? { persona_id: params.personaId } : {}),
      ...(params.accountId ? { account_id: params.accountId } : {}),
    }),
    queryFn: async () => {
      const query: Record<string, string> = {
        platform: params.platform,
        format: params.format,
      }
      if (params.personaId) query.persona_id = params.personaId
      if (params.accountId) query.account_id = params.accountId
      return apiClient<AgentRecommendation>(buildUrl('/api/agents/recommend', query))
    },
    enabled: !!params.platform && !!params.format,
    staleTime: 60000,
    retry: 2,
  })
}
