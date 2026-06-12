import React, { useEffect, useRef } from 'react'
import { useAgentFlowStore, type NodeStatus, type AgentFlowExecution } from '../../stores/agentFlowStore'
import {
  Circle,
  Loader2,
  CheckCircle2,
  XCircle,
  SkipForward,
  ChevronDown,
  ChevronUp,
  Activity,
} from 'lucide-react'

interface AgentFlowBarProps {
  executionId?: string
}

const statusConfig: Record<
  NodeStatus,
  { icon: React.ElementType; color: string; bg: string; label: string }
> = {
  PENDING: { icon: Circle, color: 'text-muted-foreground', bg: 'bg-muted', label: '待执行' },
  RUNNING: { icon: Loader2, color: 'text-primary', bg: 'bg-primary/10', label: '执行中' },
  SUCCESS: { icon: CheckCircle2, color: 'text-success', bg: 'bg-success/10', label: '成功' },
  FAILED: { icon: XCircle, color: 'text-destructive', bg: 'bg-destructive/10', label: '失败' },
  SKIPPED: { icon: SkipForward, color: 'text-muted-foreground', bg: 'bg-muted', label: '跳过' },
}

export function AgentFlowBar({ executionId }: AgentFlowBarProps) {
  const { execution, isConnected, setConnected } = useAgentFlowStore()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!executionId) return

    const token = localStorage.getItem('token')
    if (!token) return

    const connect = () => {
      try {
        const ws = new WebSocket(`ws://localhost:8001/ws/pipeline/${executionId}?token=${token}`)
        wsRef.current = ws

        ws.onopen = () => {
          setConnected(true)
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'node_update') {
              useAgentFlowStore.getState().updateNodeStatus(data.node_id, data.status, data.output)
            } else if (data.type === 'execution_status') {
              useAgentFlowStore.getState().setExecution(data.execution)
            }
          } catch {
            // ignore invalid json
          }
        }

        ws.onclose = () => {
          setConnected(false)
          reconnectRef.current = setTimeout(connect, 3000)
        }

        ws.onerror = () => {
          setConnected(false)
        }
      } catch {
        setConnected(false)
      }
    }

    connect()

    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [executionId, setConnected])

  if (!execution) {
    return (
      <div className="h-10 flex items-center justify-center text-xs text-muted-foreground border-t border-border bg-card">
        <Activity className="w-3.5 h-3.5 mr-1.5" />
        暂无执行中的 Pipeline
      </div>
    )
  }

  const completedCount = execution.nodes.filter((n) => n.status === 'SUCCESS').length
  const totalCount = execution.nodes.length
  const progress = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0

  return (
    <div className="border-t border-border bg-card">
      {/* Summary bar */}
      <div className="flex items-center justify-between px-4 py-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <Activity className={`w-3.5 h-3.5 ${isConnected ? 'text-success' : 'text-muted-foreground'}`} />
            <span className="text-xs font-medium">{execution.templateName}</span>
            <span className="text-[10px] text-muted-foreground">#{execution.executionId.slice(0, 8)}</span>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <span>{completedCount}/{totalCount}</span>
            <span>·</span>
            <span>{progress}%</span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {/* Mini progress dots */}
          <div className="flex gap-1">
            {execution.nodes.slice(0, 8).map((node) => {
              const cfg = statusConfig[node.status]
              const Icon = cfg.icon
              return (
                <div
                  key={node.id}
                  title={`${node.name}: ${cfg.label}`}
                  className={`w-2 h-2 rounded-full ${cfg.bg} flex items-center justify-center`}
                >
                  {node.status === 'RUNNING' && <Icon className={`w-1.5 h-1.5 ${cfg.color} animate-spin`} />}
                </div>
              )
            })}
            {execution.nodes.length > 8 && (
              <span className="text-[10px] text-muted-foreground">+{execution.nodes.length - 8}</span>
            )}
          </div>
        </div>
      </div>

      {/* Detailed node list (expandable) */}
      <AgentFlowDetails execution={execution} />
    </div>
  )
}

function AgentFlowDetails({ execution }: { execution: AgentFlowExecution }) {
  const [expanded, setExpanded] = React.useState(false)

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full flex items-center justify-center py-1 text-[10px] text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
      >
        <ChevronDown className="w-3 h-3 mr-0.5" />
        展开详情
      </button>
    )
  }

  return (
    <div className="px-4 pb-3 space-y-1.5">
      <button
        onClick={() => setExpanded(false)}
        className="w-full flex items-center justify-center py-1 text-[10px] text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
      >
        <ChevronUp className="w-3 h-3 mr-0.5" />
        收起
      </button>

      {execution.nodes.map((node, index) => {
        const cfg = statusConfig[node.status]
        const Icon = cfg.icon
        return (
          <div key={node.id} className="flex items-center gap-2">
            <span className="text-[10px] text-muted-foreground w-4 text-right">{index + 1}</span>
            <div className={`w-5 h-5 rounded-full ${cfg.bg} flex items-center justify-center`}>
              <Icon className={`w-3 h-3 ${cfg.color} ${node.status === 'RUNNING' ? 'animate-spin' : ''}`} />
            </div>
            <span className="text-xs flex-1">{node.name}</span>
            <span className={`text-[10px] ${cfg.color}`}>{cfg.label}</span>
            {node.output && (
              <span className="text-[10px] text-muted-foreground truncate max-w-[120px]">{node.output}</span>
            )}
          </div>
        )
      })}
    </div>
  )
}
