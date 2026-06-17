import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AccountPoolPage } from '../AccountPoolPage'

const mockStore = {
  accounts: [] as unknown[],
  personas: [] as unknown[],
  stats: { total: 0, active: 0, avg_health_score: 0, today_posts: 0 },
  isLoading: false,
  isFormLoading: false,
  error: null as string | null,
  fetchAccounts: vi.fn(),
  fetchPersonas: vi.fn(),
  createAccount: vi.fn(),
  updateAccount: vi.fn(),
  deleteAccount: vi.fn(),
  updateAccountStatus: vi.fn(),
  bindPersona: vi.fn(),
}

const mockTaskHubStore = {
  platformSchemas: [],
  fetchPlatformSchemas: vi.fn(),
}

const mockProxyStore = {
  proxies: [],
  fetchProxies: vi.fn(),
}

vi.mock('../../stores/accountPoolStore', () => ({
  useAccountPoolStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

vi.mock('../../stores/taskHubStore', () => ({
  useTaskHubStore: (selector?: (s: typeof mockTaskHubStore) => unknown) => {
    return selector ? selector(mockTaskHubStore) : mockTaskHubStore
  },
}))

vi.mock('../../stores/proxyStore', () => ({
  useProxyStore: (selector?: (s: typeof mockProxyStore) => unknown) => {
    return selector ? selector(mockProxyStore) : mockProxyStore
  },
}))

describe('AccountPoolPage', () => {
  beforeEach(() => {
    mockStore.accounts = []
    mockStore.personas = []
    mockStore.stats = { total: 0, active: 0, avg_health_score: 0, today_posts: 0 }
    mockStore.isLoading = false
    mockStore.isFormLoading = false
    mockStore.error = null
    vi.clearAllMocks()
  })

  it('renders account card list', () => {
    mockStore.accounts = [
      {
        id: 'a1',
        platform: 'xhs',
        username: 'test_user',
        status: 'active',
        health_score: 85,
        created_at: '2024-01-01T00:00:00Z',
        risk_level: 'safe',
      },
    ]
    render(<AccountPoolPage />)
    expect(screen.getByText('test_user')).toBeInTheDocument()
    expect(screen.getAllByText('活跃')[0]).toBeInTheDocument()
  })

  it('renders top stats bar', () => {
    mockStore.stats = { total: 10, active: 8, avg_health_score: 82, today_posts: 5 }
    render(<AccountPoolPage />)
    expect(screen.getByText('总账号数')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('活跃账号')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('平均健康分')).toBeInTheDocument()
    expect(screen.getByText('今日发布')).toBeInTheDocument()
  })

  it('opens detail side panel when clicking account card', () => {
    mockStore.accounts = [
      {
        id: 'a1',
        platform: 'xhs',
        username: 'test_user',
        status: 'active',
        health_score: 85,
        created_at: '2024-01-01T00:00:00Z',
        risk_level: 'safe',
        health_detail: {
          activity_score: 80,
          content_quality_score: 85,
          engagement_rate: 75,
          compliance_score: 90,
        },
      },
    ]
    const { container } = render(<AccountPoolPage />)
    fireEvent.click(screen.getByText('test_user'))
    expect(screen.getByText('账号详情')).toBeInTheDocument()

    // Detail panel should be rendered as inline aside, not fixed overlay
    const aside = container.querySelector('aside')
    expect(aside).toBeInTheDocument()
    expect(aside).toHaveClass('sticky')
    expect(aside).not.toHaveClass('fixed')
  })

  it('shows health score details in detail panel', () => {
    mockStore.accounts = [
      {
        id: 'a1',
        platform: 'xhs',
        username: 'test_user',
        status: 'active',
        health_score: 85,
        created_at: '2024-01-01T00:00:00Z',
        risk_level: 'safe',
        health_detail: {
          activity_score: 80,
          content_quality_score: 85,
          engagement_rate: 75,
          compliance_score: 90,
        },
      },
    ]
    render(<AccountPoolPage />)
    fireEvent.click(screen.getByText('test_user'))
    expect(screen.getByText('活跃度')).toBeInTheDocument()
    expect(screen.getByText('内容质量')).toBeInTheDocument()
    expect(screen.getByText('互动率')).toBeInTheDocument()
    expect(screen.getByText('合规记录')).toBeInTheDocument()
  })

  it('uses inline flex layout with main content shrink protection', () => {
    const { container } = render(<AccountPoolPage />)
    const mainWrapper = container.querySelector('.flex.gap-6.items-start')
    expect(mainWrapper).toBeInTheDocument()

    const mainContent = mainWrapper?.querySelector('.flex-1.min-w-0')
    expect(mainContent).toBeInTheDocument()
  })

  it('opens form side panel when clicking edit', () => {
    mockStore.accounts = [
      {
        id: 'a1',
        platform: 'xhs',
        username: 'test_user',
        status: 'active',
        health_score: 85,
        created_at: '2024-01-01T00:00:00Z',
        risk_level: 'safe',
      },
    ]
    const { container } = render(<AccountPoolPage />)
    fireEvent.click(screen.getByTitle('编辑'))
    expect(screen.getByText('编辑账号')).toBeInTheDocument()

    const aside = container.querySelector('aside')
    expect(aside).toBeInTheDocument()
    expect(aside).toHaveClass('sticky')
    expect(aside).not.toHaveClass('fixed')
  })

  it('closes detail panel when opening edit form', () => {
    mockStore.accounts = [
      {
        id: 'a1',
        platform: 'xhs',
        username: 'test_user',
        status: 'active',
        health_score: 85,
        created_at: '2024-01-01T00:00:00Z',
        risk_level: 'safe',
        health_detail: {
          activity_score: 80,
          content_quality_score: 85,
          engagement_rate: 75,
          compliance_score: 90,
        },
      },
    ]
    render(<AccountPoolPage />)
    fireEvent.click(screen.getByText('test_user'))
    expect(screen.getByText('账号详情')).toBeInTheDocument()

    fireEvent.click(screen.getByTitle('编辑'))
    expect(screen.queryByText('账号详情')).not.toBeInTheDocument()
    expect(screen.getByText('编辑账号')).toBeInTheDocument()
  })
})
