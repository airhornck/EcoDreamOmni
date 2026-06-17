import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardPage } from './DashboardPage'
import type { ReactNode } from 'react'

vi.mock('react-router-dom', () => ({
  Link: ({ to, children, ...props }: { to: string; children: ReactNode }) => (
    <a href={to} {...props}>{children}</a>
  ),
  useNavigate: () => vi.fn(),
  useSearchParams: () => [new URLSearchParams(), vi.fn()],
}))

vi.mock('../stores/authStore', () => ({
  useAuthStore: (selector?: (s: unknown) => unknown) => {
    const store = { user: { username: 'test', email: 'test@example.com', role: 'admin' } }
    return selector ? selector(store) : store
  },
}))

vi.mock('../stores/aiCopilotStore', () => ({
  useAICopilotStore: (selector?: (s: unknown) => unknown) => {
    const store = {
      isOpen: true,
      status: 'idle',
      messages: [],
      context: {},
      error: null,
      quickActions: [],
      pageActionCards: [],
      pageActionHandler: null,
      messages: [],
      toggle: vi.fn(),
      open: vi.fn(),
      close: vi.fn(),
      setStatus: vi.fn(),
      addMessage: vi.fn(),
      updateMessage: vi.fn(),
      setContext: vi.fn(),
      setError: vi.fn(),
      setWelcomeMessage: vi.fn(),
      setQuickActions: vi.fn(),
      setPageActionCards: vi.fn(),
      setPageActionHandler: vi.fn(),
      setMessages: vi.fn(),
      clearMessages: vi.fn(),
      applyActionCard: vi.fn(),
    }
    return selector ? selector(store) : store
  },
}))

// Mock API responses
const mockApiData = {
  overview: { today: { tasksPending: 5, contentsPendingReview: 3, contentsPublished: 12, engagementDelta: 0.15, avgHealthScore: 88, briefsPending: 2 } },
  coreMetrics: { metrics: { pendingReview: 10, publishedToday: 15, queuedTasks: 5, failedDlq: 8, tokenCostToday: 23.5 } },
  alerts: { alerts: [{ id: '1', level: 'warning' as const, title: 'API限额警告', message: '即将达到限额', timestamp: '2024-01-01T00:00:00Z' }] },
  activityLog: { entries: [], total: 0 },
  smartTopics: { topics: [{ id: 't1', title: '春季养猫注意事项', estimatedEngagement: 1200, tags: ['猫', '春季'] }] },
  agentStatus: { status: { activeAgents: 6, pendingMessages: 2, successRate1h: 0.95, lastExecutionStatus: 'success' as const } },
  storyProgress: { items: [] },
  engagementTrend: { trend: [] },
  hitRate: { rates: [] },
}

const mockFetch = vi.fn()
global.fetch = mockFetch

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
}

function renderWithQuery(ui: React.ReactElement) {
  const client = createTestQueryClient()
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}

describe('DashboardPage v4.0', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockImplementation(async (url: string) => {
      const path = url.replace('/api/', '')
      if (path === 'dashboard/overview') return { ok: true, json: async () => mockApiData.overview }
      if (path === 'dashboard/core-metrics') return { ok: true, json: async () => mockApiData.coreMetrics }
      if (path === 'dashboard/alerts') return { ok: true, json: async () => mockApiData.alerts }
      if (path === 'dashboard/activity-log') return { ok: true, json: async () => mockApiData.activityLog }
      if (path.startsWith('trend-scout/topics')) return { ok: true, json: async () => mockApiData.smartTopics }
      if (path === 'agents') return { ok: true, json: async () => mockApiData.agentStatus }
      if (path.startsWith('persona-stories')) return { ok: true, json: async () => mockApiData.storyProgress }
      if (path.startsWith('data-analyst/engagement-trend')) return { ok: true, json: async () => mockApiData.engagementTrend }
      if (path === 'predictions/hit-rate') return { ok: true, json: async () => mockApiData.hitRate }
      return { ok: false, status: 404, statusText: 'Not Found', json: async () => ({}) }
    })
  })

  it('renders PageHeader with title 工作台', async () => {
    renderWithQuery(<DashboardPage />)
    expect(await screen.findByText('工作台')).toBeInTheDocument()
  })

  it('renders 5 core metric cards', async () => {
    renderWithQuery(<DashboardPage />)
    expect(await screen.findByText('待审核任务数')).toBeInTheDocument()
    expect(await screen.findByText('今日已发布数')).toBeInTheDocument()
    expect(await screen.findByText('队列中任务数')).toBeInTheDocument()
    expect(await screen.findByText('失败 / DLQ 数')).toBeInTheDocument()
    expect(await screen.findByText('今日 Token 成本')).toBeInTheDocument()
  })

  it('renders smart topics section', async () => {
    renderWithQuery(<DashboardPage />)
    expect(await screen.findByText('智能选题推荐')).toBeInTheDocument()
    expect(await screen.findByText('春季养猫注意事项')).toBeInTheDocument()
  })

  it('renders alerts section', async () => {
    renderWithQuery(<DashboardPage />)
    expect(await screen.findByText('异常与告警')).toBeInTheDocument()
    expect(await screen.findByText('API限额警告')).toBeInTheDocument()
  })

  it('renders AI insight card', async () => {
    renderWithQuery(<DashboardPage />)
    expect(await screen.findByText('AI 智能建议')).toBeInTheDocument()
  })
})
