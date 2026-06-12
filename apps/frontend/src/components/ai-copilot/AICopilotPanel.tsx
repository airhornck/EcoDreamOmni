import { useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAICopilotStore } from '../../stores/aiCopilotStore'
import { authHeaders } from '../../lib/api'
import { useCopilotFallbackHandler } from '../../hooks/useCopilotFallbackHandler'
import { ContextBar } from './ContextBar'
import { MessageHistory } from './MessageHistory'
import { ActionCardStack } from './ActionCardStack'
import { PageActionCardArea } from './PageActionCardArea'
import { QuickActionBar } from './QuickActionBar'
import { InputBox } from './InputBox'
import { PanelRightClose } from 'lucide-react'

export function AICopilotPanel() {
  const navigate = useNavigate()
  const { isOpen, toggle, addMessage, updateMessage, setStatus, setError, status, pageActionHandler } =
    useAICopilotStore()
  const { resolveQuickAction } = useCopilotFallbackHandler()

  const abortRef = useRef<AbortController | null>(null)

  const abort = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setStatus('idle')
  }, [setStatus])

  // Direct SSE streaming into aiCopilotStore — no intermediate hook state
  const handleSend = useCallback(
    async (content: string) => {
      // Cancel any in-flight request
      if (abortRef.current) {
        abortRef.current.abort()
      }
      const controller = new AbortController()
      abortRef.current = controller

      setStatus('thinking')
      setError(null)

      const userMsg = {
        id: `msg_${Date.now()}`,
        role: 'user' as const,
        content,
        timestamp: new Date().toISOString(),
      }
      addMessage(userMsg)

      const assistantId = `msg_${Date.now()}_assistant`
      addMessage({
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      })

      try {
        const response = await fetch('/api/v1/ai/conversations/stream', {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ message: content }),
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) throw new Error('No response body')

        const decoder = new TextDecoder()
        let buffer = ''
        let assistantContent = ''

        setStatus('streaming')

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') continue
              try {
                const parsed = JSON.parse(data)
                if (parsed.content) {
                  assistantContent += parsed.content
                  updateMessage(assistantId, (m) => ({
                    ...m,
                    content: assistantContent,
                  }))
                }
                if (parsed.action_card) {
                  updateMessage(assistantId, (m) => ({
                    ...m,
                    actionCard: parsed.action_card,
                  }))
                }
              } catch {
                // ignore malformed JSON
              }
            }
          }
        }

        setStatus('completed')
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          setStatus('idle')
        } else {
          setError(err instanceof Error ? err.message : '发送失败')
          setStatus('error')
          // Update assistant message to show error indicator
          updateMessage(assistantId, (m) => ({
            ...m,
            content: m.content || '（响应失败）',
          }))
        }
      } finally {
        abortRef.current = null
      }
    },
    [addMessage, updateMessage, setStatus, setError]
  )

  // Quick Action 点击处理
  // 优先级：1) 前端导航映射 2) 页面级 handler（自定义页面操作）3) 发给 LLM
  const handleQuickAction = useCallback(
    async (action: string) => {
      // 1. 前端纯导航映射（全局快捷导航）
      const quickAction = resolveQuickAction(action)
      if (quickAction?.type === 'navigate') {
        navigate(quickAction.target)
        return
      }

      // 2. 页面级 handler（如 TaskHubCreatePage 的「上一步/下一步」）
      // 约定：cardId = '__quick_action__' 表示来自 QuickActionBar
      if (pageActionHandler) {
        await pageActionHandler('__quick_action__', action, {})
        return
      }

      // 3. 未知 quick action，当作普通聊天消息发给 LLM
      await handleSend(action)
    },
    [resolveQuickAction, navigate, handleSend, pageActionHandler],
  )

  // Panel visibility is controlled by WorkspaceLayout grid column width.
  // When isOpen=false, the grid column is 0px and this component is hidden.
  // We use opacity transition for visual smoothness.
  return (
    <aside
      className="h-full bg-card border-l border-border flex flex-col transition-opacity duration-200"
      style={{ opacity: isOpen ? 1 : 0, pointerEvents: isOpen ? 'auto' : 'none' }}
      aria-label="AI Copilot"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
        <div>
          <h2 className="text-sm font-semibold text-foreground">AI Copilot</h2>
          <p className="text-xs text-muted-foreground">智能助手面板</p>
        </div>
        <button
          onClick={toggle}
          className="p-1.5 rounded hover:bg-secondary transition-colors"
          aria-label="关闭 AI Copilot"
        >
          <PanelRightClose className="w-4 h-4 text-muted-foreground" />
        </button>
      </div>

      {/* Context Bar */}
      <ContextBar />

      {/* Message History */}
      <MessageHistory />

      {/* Legacy Action Cards (from message history) */}
      <ActionCardStack />

      {/* Copilot-Driven Page Action Cards — v4.0 */}
      <PageActionCardArea onAction={pageActionHandler || undefined} />

      {/* Quick Actions */}
      <QuickActionBar onActionClick={handleQuickAction} />

      {/* Input */}
      <InputBox onSend={handleSend} onAbort={abort} status={status} />
    </aside>
  )
}
