import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PublisherPage } from '../PublisherPage'

const mockStore = {
  tasks: [] as unknown[],
  drafts: [] as unknown[],
  accounts: [] as unknown[],
  stats: { todayPublished: 0, pendingCount: 0, successRate7d: 0, failedRetryCount: 0 },
  isLoading: false,
  isFormLoading: false,
  error: null as string | null,
  fetchTasks: vi.fn(),
  fetchDrafts: vi.fn(),
  fetchAccounts: vi.fn(),
  createTask: vi.fn(),
  executeTask: vi.fn(),
  retryTask: vi.fn(),
  deleteTask: vi.fn(),
}

vi.mock('../../stores/publisherStore', () => ({
  usePublisherStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('PublisherPage', () => {
  beforeEach(() => {
    mockStore.tasks = []
    mockStore.drafts = []
    mockStore.accounts = []
    mockStore.stats = { todayPublished: 0, pendingCount: 0, successRate7d: 0, failedRetryCount: 0 }
    mockStore.isLoading = false
    mockStore.isFormLoading = false
    mockStore.error = null
    vi.clearAllMocks()
  })

  it('renders top stats bar', () => {
    mockStore.stats = { todayPublished: 5, pendingCount: 3, successRate7d: 95, failedRetryCount: 1 }
    render(<PublisherPage />)
    expect(screen.getByText('今日发布数')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('待发布数')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('近7日成功率')).toBeInTheDocument()
    expect(screen.getByText('失败待重试')).toBeInTheDocument()
  })

  it('renders tab switching (list/calendar)', () => {
    render(<PublisherPage />)
    expect(screen.getByText('列表视图')).toBeInTheDocument()
    expect(screen.getByText('日历视图')).toBeInTheDocument()
  })

  it('renders publish task list', () => {
    mockStore.tasks = [
      {
        id: 'p1',
        draft_id: 'd1',
        account_id: 'a1',
        platform: 'xhs',
        status: 'pending',
        draft_title: '猫咪养护',
        account_name: '小红',
        created_at: '2024-01-01T00:00:00Z',
        retry_count: 0,
      },
    ]
    render(<PublisherPage />)
    expect(screen.getByText('猫咪养护')).toBeInTheDocument()
    expect(screen.getAllByText('待发布')[0]).toBeInTheDocument()
  })

  it('does not show new task create button', () => {
    render(<PublisherPage />)
    expect(screen.queryByRole('button', { name: /新建发布任务/i })).not.toBeInTheDocument()
  })

  it('shows unified publish entry hint', () => {
    render(<PublisherPage />)
    expect(screen.getByText(/发布入口已统一/i)).toBeInTheDocument()
    expect(screen.getByText(/审核发布中心/i)).toBeInTheDocument()
  })
})
