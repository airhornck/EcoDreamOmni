import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useAICopilotStore } from '../stores/aiCopilotStore'
import { apiClient } from '../lib/api'
import { useCopilotFallbackHandler } from './useCopilotFallbackHandler'
import { getPageCopilotDefaultConfig } from '../lib/copilotPageDefaults'

export function useCopilotPageSync() {
  const location = useLocation()
  const { setContext, setWelcomeMessage, setQuickActions, setPageActionCards, setPageActionHandler } =
    useAICopilotStore()
  const { fallbackHandler } = useCopilotFallbackHandler()

  useEffect(() => {
    const page = location.pathname

    // 1. 上报上下文到后端（静默失败，不阻塞页面功能）
    apiClient('/api/ai/copilot/context', {
      method: 'POST',
      body: JSON.stringify({
        page,
        page_title: document.title,
        timestamp: new Date().toISOString(),
      }),
    }).catch(() => {
      /* silent fail */
    })

    // 2. 设置基础上下文（前端本地）
    setContext({ page })

    // 3. 获取后端推荐的 Action Cards、欢迎语、快捷动作
    apiClient<{
      cards: unknown[]
      ai_insights?: string[]
      suggested_actions?: string[]
    }>(`/api/ai/copilot/action-cards?page=${encodeURIComponent(page)}`)
      .then((res) => {
        const cards = (res.cards || []).map((c) => {
          const card = c as Record<string, unknown>
          return {
            id: String(card.id),
            type: String(card.type) as
              | 'decision'
              | 'generation'
              | 'suggestion'
              | 'info',
            title: String(card.title),
            description: String(card.description),
            priority: Number(card.priority || 1),
            inputs: Array.isArray(card.inputs) ? card.inputs : [],
            actions: Array.isArray(card.actions) ? card.actions : [],
          }
        })
        setPageActionCards(cards)
        setWelcomeMessage(res.ai_insights?.[0] || null)
        setQuickActions(res.suggested_actions || [])
      })
      .catch(() => {
        // 后端失败时使用前端默认配置兜底（优雅降级）
        // TODO: 当后端 action-cards 接口覆盖全部页面后，移除兜底
        const defaultConfig = getPageCopilotDefaultConfig(page)
        if (defaultConfig) {
          setPageActionCards(defaultConfig.actionCards)
          setWelcomeMessage(defaultConfig.welcomeMessage)
          setQuickActions(defaultConfig.quickActions)
        } else {
          setPageActionCards([])
          setWelcomeMessage(null)
          setQuickActions([])
        }
      })

    // 4. 注册统一的 fallback handler（Phase 2 已完成）
    //    当具体页面没有注册自定义 handler 时，fallback 负责：
    //    - 导航类 action → 前端直接 navigate
    //    - 业务类 action → POST /api/ai/copilot/agent（后端 CapabilityRegistry + MetaOrchestrator）
    setPageActionHandler(fallbackHandler)

    // Cleanup: 切换页面时清空旧状态
    return () => {
      setPageActionCards([])
      setWelcomeMessage(null)
      setQuickActions([])
      setPageActionHandler(null)
    }
  }, [
    location.pathname,
    fallbackHandler,
    setContext,
    setPageActionCards,
    setPageActionHandler,
    setQuickActions,
    setWelcomeMessage,
  ])
}
