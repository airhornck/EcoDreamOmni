import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../ui/EmptyState'
import { Cpu } from 'lucide-react'
import { authHeaders } from '../../lib/api'

interface AgentHeartbeat {
  agentId: string
  status: 'IDLE' | 'BUSY' | 'UNHEALTHY'
  queueDepth: number
}

interface Agent {
  id: string
  name: string
  status: string
}

export function AgentFleetMini() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [heartbeats, setHeartbeats] = useState<AgentHeartbeat[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchAgents() {
      try {
        const [agentsRes, hbRes] = await Promise.all([
          fetch('/api/agents', { headers: authHeaders() }),
          fetch('/api/agent-watch/dashboard', { headers: authHeaders() }),
        ])
        if (agentsRes.ok) {
          const data = await agentsRes.json()
          setAgents(data.agents?.slice(0, 4) || [])
        }
        if (hbRes.ok) {
          const data = await hbRes.json()
          setHeartbeats(data.heartbeats || [])
        }
      } catch {
        // silent fail
      } finally {
        setLoading(false)
      }
    }
    fetchAgents()
  }, [])

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-20 bg-card rounded-xl border border-border animate-pulse" />
        ))}
      </div>
    )
  }

  if (agents.length === 0) {
    return (
      <EmptyState
        icon={Cpu}
        title="Agent 舰队"
        description="暂无 Agent 状态数据"
      />
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {agents.map((agent) => {
        const hb = heartbeats.find((h) => h.agentId === agent.id)
        const isHealthy = agent.status === 'ACTIVE'
        const isDegraded = agent.status === 'DEGRADED'
        return (
          <Link
            key={agent.id}
            to="/agent-orchestra"
            className="p-3 bg-card rounded-xl border border-border hover:border-primary/30 hover:shadow-sm transition-all"
          >
            <div className="flex items-center gap-2 mb-2">
              <Cpu className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs font-medium text-foreground truncate">{agent.name}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-success' : isDegraded ? 'bg-warning' : 'bg-destructive/150'}`} />
              <span className="text-xs text-muted-foreground">
                {hb?.status === 'BUSY' ? '运行中' : hb?.status === 'IDLE' ? '空闲' : hb?.status === 'UNHEALTHY' ? '故障' : '健康'}
              </span>
              {hb && hb.queueDepth > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-warning-bg text-warning">队列 {hb.queueDepth}</span>
              )}
            </div>
          </Link>
        )
      })}
    </div>
  )
}
