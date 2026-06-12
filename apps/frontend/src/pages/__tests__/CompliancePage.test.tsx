import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CompliancePage } from '../CompliancePage'

const mockStore = {
  rules: [] as unknown[],
  results: [] as unknown[],
  stats: null as unknown,
  history: [] as unknown[],
  isLoading: false,
  error: null as string | null,
  activeTab: 'single' as const,
  levelFilter: 'all',
  searchQuery: '',
  fetchRules: vi.fn(),
  checkContent: vi.fn(),
  batchCheck: vi.fn(),
  fetchStats: vi.fn(),
  fetchHistory: vi.fn(),
  clearHistory: vi.fn(),
  setActiveTab: vi.fn(),
  setLevelFilter: vi.fn(),
  setSearchQuery: vi.fn(),
}

vi.mock('../../stores/complianceStore', () => ({
  useComplianceStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('CompliancePage', () => {
  beforeEach(() => {
    mockStore.rules = []
    mockStore.results = []
    mockStore.stats = null
    mockStore.history = []
    mockStore.isLoading = false
    mockStore.error = null
    mockStore.activeTab = 'single'
    mockStore.levelFilter = 'all'
    mockStore.searchQuery = ''
    vi.clearAllMocks()
  })

  it('renders four-layer risk control stats dashboard', () => {
    mockStore.stats = {
      l1: { today: 2, total: 10 },
      l2: { today: 5, total: 20 },
      l3: { today: 3 },
      l4: { today: 1 },
    }
    render(<CompliancePage />)
    expect(screen.getByText('L1 法律红线')).toBeInTheDocument()
    expect(screen.getByText('L2 平台规则')).toBeInTheDocument()
    expect(screen.getByText('L3 账号策略')).toBeInTheDocument()
    expect(screen.getByText('L4 动态风控')).toBeInTheDocument()
    expect(screen.getAllByText('2').length).toBeGreaterThanOrEqual(1)
  })

  it('renders tab switching (single/batch)', () => {
    render(<CompliancePage />)
    expect(screen.getByText('单条扫描')).toBeInTheDocument()
    expect(screen.getByText('批量扫描')).toBeInTheDocument()
  })

  it('performs single scan when entering text and clicking scan', async () => {
    mockStore.checkContent.mockResolvedValue({})
    render(<CompliancePage />)
    const textarea = screen.getByPlaceholderText('粘贴需要审核的内容文本...')
    fireEvent.change(textarea, { target: { value: '测试内容' } })
    fireEvent.click(screen.getByRole('button', { name: /开始扫描/i }))
    await waitFor(() => {
      expect(mockStore.checkContent).toHaveBeenCalledWith('测试内容')
    })
  })

  it('filters rule library by level (L1/L2/L3/L4)', () => {
    render(<CompliancePage />)
    const l1Btn = screen.getByRole('button', { name: 'L1' })
    fireEvent.click(l1Btn)
    expect(mockStore.setLevelFilter).toHaveBeenCalledWith('l1')
  })
})
