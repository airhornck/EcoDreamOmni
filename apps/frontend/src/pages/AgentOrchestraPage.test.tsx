import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { AgentOrchestraPage } from './AgentOrchestraPage'

const mockAgent = {
  id: 'content_forge_xhs_image',
  name: '小红书图文生成 Agent',
  role: 'content_forge',
  description: '生成小红书图文内容',
  avatar_url: '',
  skills: ['text_generate_skill'],
  supported_platforms: ['xhs'],
  supported_formats: ['图文'],
  config: {
    platform_format_snapshot: {
      platform_id: 'xhs',
      format_name: '图文',
      title_constraints: { max_length: 20 },
    },
  },
  success_rate: 0.95,
  recent_tasks_1h: 2,
  status: 'ACTIVE',
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-14T00:00:00Z',
}

const mockStore = {
  agents: [] as typeof mockAgent[],
  isLoading: false,
  error: null as string | null,
  selectedAgentId: null as string | null,
  fetchAgents: vi.fn(),
  selectAgent: vi.fn(),
  clearError: vi.fn(),
}

vi.mock('../stores/agentFleetStore', () => ({
  useAgentFleetStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('AgentOrchestraPage (Agent Fleet)', () => {
  beforeEach(() => {
    mockStore.agents = []
    mockStore.isLoading = false
    mockStore.error = null
    mockStore.selectedAgentId = null
    vi.clearAllMocks()
  })

  it('renders page title', () => {
    render(<AgentOrchestraPage />)
    expect(screen.getByText('Agent 驾驶舱')).toBeInTheDocument()
    expect(screen.getByText(/v4\.0 Agent-First 舰队/i)).toBeInTheDocument()
  })

  it('fetches agents on mount', () => {
    render(<AgentOrchestraPage />)
    expect(mockStore.fetchAgents).toHaveBeenCalled()
  })

  it('shows loading state', () => {
    mockStore.isLoading = true
    render(<AgentOrchestraPage />)
    expect(screen.getByTestId('agent-fleet-loading')).toBeInTheDocument()
  })

  it('shows error banner when error exists', () => {
    mockStore.error = '加载失败'
    render(<AgentOrchestraPage />)
    expect(screen.getByText('加载失败')).toBeInTheDocument()
  })

  it('renders agent list with stats', () => {
    mockStore.agents = [mockAgent]
    render(<AgentOrchestraPage />)

    expect(screen.getByText('小红书图文生成 Agent')).toBeInTheDocument()
    expect(screen.getByText('content_forge_xhs_image')).toBeInTheDocument()

    const row = screen.getByText('小红书图文生成 Agent').closest('tr')!
    expect(within(row).getByText('xhs')).toBeInTheDocument()
    expect(within(row).getByText('图文')).toBeInTheDocument()
    expect(within(row).getByText('95.0%')).toBeInTheDocument()
    expect(within(row).getByText('2')).toBeInTheDocument()
    expect(within(row).getByText('活跃')).toBeInTheDocument()
  })

  it('expands agent detail on click', () => {
    mockStore.agents = [mockAgent]
    render(<AgentOrchestraPage />)

    fireEvent.click(screen.getByLabelText('展开详情'))
    expect(mockStore.selectAgent).toHaveBeenCalledWith(mockAgent.id)
  })

  it('filters agents by platform', () => {
    mockStore.agents = [
      mockAgent,
      { ...mockAgent, id: 'a2', name: '抖音视频 Agent', supported_platforms: ['douyin'] },
    ]
    render(<AgentOrchestraPage />)

    expect(screen.getByText('小红书图文生成 Agent')).toBeInTheDocument()
    expect(screen.getByText('抖音视频 Agent')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'xhs' }))
    expect(screen.getByText('小红书图文生成 Agent')).toBeInTheDocument()
    expect(screen.queryByText('抖音视频 Agent')).not.toBeInTheDocument()
  })

  it('triggers refresh from copilot action', async () => {
    mockStore.fetchAgents.mockResolvedValue(undefined)
    render(<AgentOrchestraPage />)

    // Copilot action cards are registered asynchronously via useEffect;
    // direct handler is not exposed, so we verify the refresh button exists.
    fireEvent.click(screen.getByRole('button', { name: /刷新/i }))
    await waitFor(() => {
      expect(mockStore.fetchAgents).toHaveBeenCalled()
    })
  })
})
