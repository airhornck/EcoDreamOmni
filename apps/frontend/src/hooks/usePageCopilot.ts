import { useEffect, useMemo, useRef } from 'react'
import { useAICopilotStore, type PageActionCard } from '../stores/aiCopilotStore'

export type PageCopilotHandler = (
  cardId: string,
  actionId: string,
  payload?: Record<string, unknown>
) => void | Promise<void>

/**
 * 注册页面级 Copilot Action Cards 与 Handler。
 * 切换页面时会自动清理，避免卡片残留。
 * handler 通过 ref 保持最新，无需 useCallback 稳定。
 * cards 通过 JSON 序列化做稳定化，避免每次渲染新引用导致无限循环。
 */
export function usePageCopilot(cards: PageActionCard[], handler: PageCopilotHandler) {
  const { setPageActionCards, setPageActionHandler } = useAICopilotStore()
  const handlerRef = useRef(handler)

  useEffect(() => {
    handlerRef.current = handler
  }, [handler])

  // 将 cards 稳定化：内容不变时保持同一引用，防止 setPageActionCards 触发 re-render 后又产生新引用。
  const cardsJson = JSON.stringify(cards)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const stableCards = useMemo(() => cards, [cardsJson])

  useEffect(() => {
    setPageActionCards(stableCards)
    setPageActionHandler((cardId, actionId, payload) => handlerRef.current(cardId, actionId, payload))

    return () => {
      setPageActionCards([])
      setPageActionHandler(null)
    }
  }, [setPageActionCards, setPageActionHandler, stableCards])
}
