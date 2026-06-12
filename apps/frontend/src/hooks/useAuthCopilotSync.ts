/**
 * Auth-Copilot 状态同步 Hook
 *
 * 实现 Copilot 对话记录的用户隔离：
 * - 登录时：从 localStorage 加载当前用户的历史消息
 * - 登出时：清空 Copilot 消息状态
 * - 消息变化时：自动保存到 localStorage（按用户隔离）
 *
 * 存储 key 格式: `ai-copilot-messages-{userId}`
 */

import { useEffect, useRef } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useAICopilotStore } from '../stores/aiCopilotStore'

const MESSAGES_STORAGE_KEY = 'ai-copilot-messages'

function getStorageKey(userId: string): string {
  return `${MESSAGES_STORAGE_KEY}-${userId}`
}

export function useAuthCopilotSync() {
  const { user } = useAuthStore()
  const { messages, setMessages, clearMessages } = useAICopilotStore()

  const prevUserIdRef = useRef<string | null>(null)

  // 监听用户变化：登录时加载，切换时清空
  useEffect(() => {
    const currentUserId = user?.id ?? null
    const prevUserId = prevUserIdRef.current

    // 用户未变，跳过
    if (currentUserId === prevUserId) return

    prevUserIdRef.current = currentUserId

    if (!currentUserId) {
      // 登出或匿名状态：清空 Copilot 消息
      clearMessages()
      return
    }

    // 用户切换（包括新登录）：加载该用户的历史消息
    const saved = localStorage.getItem(getStorageKey(currentUserId))
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) {
          setMessages(parsed)
        } else {
          clearMessages()
        }
      } catch {
        clearMessages()
      }
    } else {
      // 新用户无历史：清空（避免残留其他用户的消息）
      clearMessages()
    }
  }, [user?.id, clearMessages, setMessages])

  // 消息变化时自动保存
  useEffect(() => {
    const currentUserId = user?.id
    if (!currentUserId) return

    localStorage.setItem(getStorageKey(currentUserId), JSON.stringify(messages))
  }, [messages, user?.id])
}
