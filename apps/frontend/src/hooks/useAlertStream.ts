import { useEffect, useRef, useState, useCallback } from 'react'

export interface StreamAlert {
  id: string
  level: 'emergency' | 'warning' | 'info' | 'success'
  title: string
  message: string
  timestamp: string
  source: string
}

interface AlertStreamState {
  alerts: StreamAlert[]
  isConnected: boolean
  error: string | null
}

export function useAlertStream(): AlertStreamState & { dismissAlert: (id: string) => void } {
  const [alerts, setAlerts] = useState<StreamAlert[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const dismissAlert = useCallback((id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }, [])

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return

    const connect = () => {
      try {
        const ws = new WebSocket(`ws://localhost:8001/ws/alerts?token=${token}`)
        wsRef.current = ws

        ws.onopen = () => {
          setIsConnected(true)
          setError(null)
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'pong') return
            setAlerts((prev) => {
              const next = [data as StreamAlert, ...prev]
              return next.slice(0, 50) // keep last 50
            })
          } catch {
            // ignore invalid json
          }
        }

        ws.onerror = () => {
          setError('WebSocket 连接错误')
          setIsConnected(false)
        }

        ws.onclose = () => {
          setIsConnected(false)
          // Auto reconnect after 3s
          reconnectTimerRef.current = setTimeout(connect, 3000)
        }
      } catch {
        setError('WebSocket 初始化失败')
      }
    }

    connect()

    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return { alerts, isConnected, error, dismissAlert }
}
