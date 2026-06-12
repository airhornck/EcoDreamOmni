import { useCallback, useRef, useState } from 'react'
import { authHeaders } from '../lib/api'

export interface SSEMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  actionCard?: ActionCard
}

export interface ActionCard {
  id: string
  type: 'DIFF' | 'CONFIRM' | 'MULTI_SELECT' | 'INFO'
  title: string
  description?: string
  diff?: { before: string; after: string }
  options?: { label: string; value: string }[]
}

interface SSEState {
  messages: SSEMessage[]
  status: 'idle' | 'thinking' | 'streaming' | 'completed' | 'error'
  error: string | null
}

interface SSEActions {
  sendMessage: (content: string, context?: Record<string, unknown>) => void
  abort: () => void
  clear: () => void
}

export function useSSEStream(endpoint = '/api/v1/ai/conversations/stream'): SSEState & SSEActions {
  const [messages, setMessages] = useState<SSEMessage[]>([])
  const [status, setStatus] = useState<SSEState['status']>('idle')
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async (content: string, context?: Record<string, unknown>) => {
      if (abortRef.current) {
        abortRef.current.abort()
      }
      const controller = new AbortController()
      abortRef.current = controller

      const userMsg: SSEMessage = {
        id: `msg_${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMsg])
      setStatus('thinking')
      setError(null)

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ message: content, context }),
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
        const assistantId = `msg_${Date.now()}_assistant`

        setStatus('streaming')
        setMessages((prev) => [
          ...prev,
          {
            id: assistantId,
            role: 'assistant',
            content: '',
            timestamp: new Date().toISOString(),
          },
        ])

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
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId ? { ...m, content: assistantContent } : m
                    )
                  )
                }
                if (parsed.action_card) {
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId
                        ? { ...m, actionCard: parsed.action_card as ActionCard }
                        : m
                    )
                  )
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
          setError(err instanceof Error ? err.message : 'Stream error')
          setStatus('error')
        }
      }
    },
    [endpoint]
  )

  const abort = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setStatus('idle')
  }, [])

  const clear = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setMessages([])
    setStatus('idle')
    setError(null)
  }, [])

  return { messages, status, error, sendMessage, abort, clear }
}
