import { create } from 'zustand'

export type NodeStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'SKIPPED'

export interface AgentFlowNode {
  id: string
  name: string
  type: string
  status: NodeStatus
  startTime?: string
  endTime?: string
  output?: string
}

export interface AgentFlowExecution {
  executionId: string
  templateName: string
  status: 'RUNNING' | 'PAUSED' | 'FAILED' | 'COMPLETED'
  nodes: AgentFlowNode[]
  startedAt: string
  completedAt?: string
}

interface AgentFlowState {
  execution: AgentFlowExecution | null
  isConnected: boolean
  wsError: string | null

  setExecution: (execution: AgentFlowExecution | null) => void
  updateNodeStatus: (nodeId: string, status: NodeStatus, output?: string) => void
  setConnected: (v: boolean) => void
  setWsError: (e: string | null) => void
  reset: () => void
}

export const useAgentFlowStore = create<AgentFlowState>((set) => ({
  execution: null,
  isConnected: false,
  wsError: null,

  setExecution: (execution) => set({ execution }),

  updateNodeStatus: (nodeId, status, output) =>
    set((s) => {
      if (!s.execution) return s
      const now = new Date().toISOString()
      return {
        execution: {
          ...s.execution,
          nodes: s.execution.nodes.map((n) =>
            n.id === nodeId
              ? {
                  ...n,
                  status,
                  ...(status === 'RUNNING' && !n.startTime ? { startTime: now } : {}),
                  ...(['SUCCESS', 'FAILED', 'SKIPPED'].includes(status) ? { endTime: now } : {}),
                  ...(output ? { output } : {}),
                }
              : n
          ),
          status:
            status === 'FAILED'
              ? 'FAILED'
              : s.execution.nodes.every((n) => ['SUCCESS', 'SKIPPED'].includes(n.status))
                ? 'COMPLETED'
                : s.execution.status,
        },
      }
    }),

  setConnected: (isConnected) => set({ isConnected }),
  setWsError: (wsError) => set({ wsError }),
  reset: () => set({ execution: null, isConnected: false, wsError: null }),
}))
