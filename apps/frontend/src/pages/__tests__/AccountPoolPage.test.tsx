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

vi.mock('../../stores/accountPoolStore', () => ({
  useAccountPoolStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
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

  it('opens detail drawer when clicking account card', () => {
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
  })

  it('shows health score details in detail drawer', () => {
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
})
