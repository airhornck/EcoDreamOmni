import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AgentOrchestraPage } from './AgentOrchestraPage'

const mockStore = {
  dashboard: null as unknown,
  agents: [] as unknown[],
  agentDetail: null as unknown,
  agentConfigs: [] as unknown[],
  alerts: [] as unknown[],
  overallMetrics: null as unknown,
  costByAgent: [] as unknown[],
  activity: [] as unknown[],
  alertSummary: null as unknown,
  isLoading: false,
  error: null as string | null,
  activeTab: 'dashboard' as const,
  fetchDashboard: vi.fn(),
  fetchAgents: vi.fn(),
  fetchAgentDetail: vi.fn(),
  fetchAgentConfigs: vi.fn(),
  fetchAlerts: vi.fn(),
  ackAlert: vi.fn(),
  fetchOverallMetrics: vi.fn(),
  fetchCostByAgent: vi.fn(),
  fetchActivity: vi.fn(),
  fetchAlertSummary: vi.fn(),
  setActiveTab: vi.fn(),
  clearError: vi.fn(),
}

vi.mock('../stores/agentCockpitStore', () => ({
  useAgentCockpitStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('AgentOrchestraPage (Agent Cockpit)', () => {
  beforeEach(() => {
    mockStore.dashboard = null
    mockStore.agents = []
    mockStore.agentDetail = null
    mockStore.agentConfigs = []
    mockStore.alerts = []
    mockStore.overallMetrics = null
    mockStore.costByAgent = []
    mockStore.activity = []
    mockStore.alertSummary = null
    mockStore.isLoading = false
    mockStore.error = null
    mockStore.activeTab = 'dashboard'
    vi.clearAllMocks()
  })

  it('renders page title', () => {
    render(<AgentOrchestraPage />)
    expect(screen.getByText('Agent Cockpit')).toBeInTheDocument()
    expect(screen.getByText(/Agent 驾驶舱/i)).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockStore.isLoading = true
    render(<AgentOrchestraPage />)
    expect(screen.getByText(/加载中/i)).toBeInTheDocument()
  })

  it('shows error banner when error exists', () => {
    mockStore.error = '加载失败'
    render(<AgentOrchestraPage />)
    expect(screen.getByText('加载失败')).toBeInTheDocument()
  })

  it('fetches dashboard and alert summary on mount', () => {
    render(<AgentOrchestraPage />)
    expect(mockStore.fetchDashboard).toHaveBeenCalled()
    expect(mockStore.fetchAlertSummary).toHaveBeenCalled()
  })

  describe('Dashboard tab', () => {
    it('renders fleet status cards and agent table', () => {
      mockStore.dashboard = {
        agents: [
          { agent_id: 'a1', name: '策划Agent', role: 'planner', status: 'ACTIVE', healthy: true, queue_depth: 0, version: '1.0', completion_rate: 0.95, total_tasks_1h: 12 },
          { agent_id: 'a2', name: '生成Agent', role: 'generator', status: 'DEGRADED', healthy: false, queue_depth: 3, version: '1.1', completion_rate: 0.8, total_tasks_1h: 5 },
        ],
        agent_summary: { total: 2, healthy: 1, unhealthy: 1 },
        overall_metrics: {},
        open_alerts: [],
        active_traces: [],
      }
      render(<AgentOrchestraPage />)
      // Fleet status labels should be present
      expect(screen.getByText(/Agent.*fleet.*状态/i)).toBeInTheDocument()
      expect(screen.getByText('策划Agent')).toBeInTheDocument()
      expect(screen.getByText('生成Agent')).toBeInTheDocument()
    })

    it('renders alert summary', () => {
      mockStore.alertSummary = {
        total: 3,
        by_severity: { P0: 1, P1: 1, P2: 1 },
        by_type: {},
        by_status: {},
        latest: [
          { id: 'al1', severity: 'P0', message: 'Agent 离线', created_at: new Date().toISOString() },
        ],
      }
      render(<AgentOrchestraPage />)
      expect(screen.getByText(/告警摘要/i)).toBeInTheDocument()
      expect(screen.getByText(/P0: 1/i)).toBeInTheDocument()
    })

    it('renders activity stream', () => {
      mockStore.activity = [
        { type: 'heartbeat', timestamp: new Date().toISOString(), agent_id: 'a1', status: 'healthy', queue_depth: 0 },
      ]
      render(<AgentOrchestraPage />)
      expect(screen.getByText(/最近活动/i)).toBeInTheDocument()
      expect(screen.getByText(/a1/i)).toBeInTheDocument()
    })
  })

  describe('Agents tab', () => {
    it('switches to agents tab and fetches agents', () => {
      render(<AgentOrchestraPage />)
      fireEvent.click(screen.getByRole('tab', { name: /Agents/i }))
      expect(mockStore.setActiveTab).toHaveBeenCalledWith('agents')
    })

    it('displays agent list', () => {
      mockStore.activeTab = 'agents'
      mockStore.agents = [
        { id: 'a1', name: '策划Agent', role: 'planner', description: '策划', owner: 'alice', status: 'ACTIVE', created_at: '', updated_at: '' },
      ]
      render(<AgentOrchestraPage />)
      expect(screen.getByText('策划Agent')).toBeInTheDocument()
      expect(screen.getByText('ACTIVE')).toBeInTheDocument()
    })
  })

  describe('Metrics tab', () => {
    it('switches to metrics tab and fetches data', () => {
      render(<AgentOrchestraPage />)
      fireEvent.click(screen.getByRole('tab', { name: /统计/i }))
      expect(mockStore.setActiveTab).toHaveBeenCalledWith('metrics')
    })

    it('displays overall metrics', () => {
      mockStore.activeTab = 'metrics'
      mockStore.overallMetrics = {
        total_tasks: 100,
        total_agents: 5,
        overall_completion_rate: 0.95,
        total_tokens: 50000,
        total_cost_usd: 1.2345,
      }
      render(<AgentOrchestraPage />)
      expect(screen.getByText('总任务数')).toBeInTheDocument()
      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('$1.2345')).toBeInTheDocument()
    })

    it('displays cost by agent table', () => {
      mockStore.activeTab = 'metrics'
      mockStore.costByAgent = [
        { agent_id: 'a1', agent_role: 'planner', task_count: 10, total_tokens: 1000, total_cost_usd: 0.5 },
      ]
      render(<AgentOrchestraPage />)
      expect(screen.getByText('成本归因（按 Agent）')).toBeInTheDocument()
      expect(screen.getByText('a1')).toBeInTheDocument()
      expect(screen.getByText('$0.5000')).toBeInTheDocument()
    })
  })

  describe('Alerts tab', () => {
    it('switches to alerts tab and fetches alerts', () => {
      render(<AgentOrchestraPage />)
      fireEvent.click(screen.getByRole('tab', { name: /告警/i }))
      expect(mockStore.setActiveTab).toHaveBeenCalledWith('alerts')
    })

    it('displays alerts and supports ack', async () => {
      mockStore.activeTab = 'alerts'
      mockStore.alerts = [
        { id: 'al1', severity: 'P0', alert_type: 'offline', agent_id: 'a1', message: 'Agent 离线', created_at: new Date().toISOString(), status: 'open' },
      ]
      mockStore.ackAlert.mockResolvedValue(true)
      render(<AgentOrchestraPage />)
      expect(screen.getByText(/Agent 离线/i)).toBeInTheDocument()
      fireEvent.click(screen.getByRole('button', { name: /确认/i }))
      await waitFor(() => {
        expect(mockStore.ackAlert).toHaveBeenCalledWith('al1', 'operator')
      })
    })
  })
})
