/**
 * Copilot Fallback Action Handler — Phase 2 MetaOrchestrator Bridge
 *
 * 为所有未注册自定义 pageActionHandler 的页面提供统一的 Action Card 处理能力。
 * Phase 2 变更：
 *   - 纯导航类 action → 前端直接 navigate（不走后端）
 *   - 业务类 action → 统一 POST /api/ai/copilot/agent，由后端 CapabilityRegistry + MetaOrchestrator 动态路由
 */

import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../lib/api'
import {
  resolveNavigateAction,
  QUICK_ACTION_NAVIGATE_MAP,
} from '../lib/copilotCapabilities'

export function useCopilotFallbackHandler() {
  const navigate = useNavigate()

  /** Fallback handler：当页面未注册自定义 handler 时使用 */
  const fallbackHandler = useCallback(
    async (cardId: string, actionId: string, payload?: Record<string, unknown>) => {
      // 1. 纯导航类 action → 前端直接处理
      const navCap = resolveNavigateAction(actionId)
      if (navCap) {
        navigate(navCap.target)
        return
      }

      // 2. 业务类 action → 统一调用后端 Agent Router
      try {
        const res = await apiClient<{
          code: string
          message: string
          data: Record<string, unknown>
          copilot_followup?: {
            message: string
            suggested_cards: unknown[]
          }
        }>('/api/ai/copilot/agent', {
          method: 'POST',
          body: JSON.stringify({
            card_id: cardId,
            action_id: actionId,
            inputs: payload || {},
            payload: payload || {},
            context: {
              page: window.location.pathname,
            },
          }),
        })
        console.log('[Copilot] Agent action result:', res)
        // TODO: Phase 2+ — 根据 res.copilot_followup 动态更新 Action Cards
      } catch (err) {
        console.error('[Copilot] Agent action failed:', err)
      }
    },
    [navigate],
  )

  /** 根据 action 文本解析 quick action 操作 */
  const resolveQuickAction = useCallback(
    (actionText: string) => {
      return QUICK_ACTION_NAVIGATE_MAP[actionText] || null
    },
    [],
  )

  return { fallbackHandler, resolveQuickAction }
}
