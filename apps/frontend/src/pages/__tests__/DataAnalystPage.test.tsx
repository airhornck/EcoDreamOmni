import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DataAnalystPage } from '../DataAnalystPage'

const mockStore = {
  dashboard: null,
  publishTrend: [],
  platformDistribution: [],
  engagementDistribution: [],
  mapeTrend: [],
  contentRanking: [],
  accountComparison: [],
  reportList: [],
  calibrationStatus: null,
  importHistory: [],
  isLoading: false,
  error: null,
  fetchDashboard: vi.fn(),
  fetchPublishTrend: vi.fn(),
  fetchPlatformDistribution: vi.fn(),
  fetchEngagementDistribution: vi.fn(),
  fetchMapeTrend: vi.fn(),
  fetchContentRanking: vi.fn(),
  fetchAccountComparison: vi.fn(),
  fetchReportList: vi.fn(),
  fetchCalibrationStatus: vi.fn(),
  fetchImportHistory: vi.fn(),
  createReport: vi.fn(),
  triggerCalibrate: vi.fn(),
  clearError: vi.fn(),
}

vi.mock('../../stores/dataAnalystStore', () => ({
  useDataAnalystStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('DataAnalystPage — Copilot 三栏适配', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  function Wrapper({ children }: { children: React.ReactNode }) {
    return <MemoryRouter>{children}</MemoryRouter>
  }

  it('renders page title and refresh button', () => {
    render(
      <Wrapper>
        <DataAnalystPage />
      </Wrapper>
    )

    expect(screen.getByText('数据报表')).toBeInTheDocument()
    expect(screen.getByText('刷新')).toBeInTheDocument()
  })

  it('uses xl breakpoint for two-column chart layout', () => {
    const { container } = render(
      <Wrapper>
        <DataAnalystPage />
      </Wrapper>
    )

    const chartGrid = container.querySelector('.grid.grid-cols-1.xl\\:grid-cols-2')
    expect(chartGrid).toBeInTheDocument()
  })

  it('chart cards have shrink protection', () => {
    const { container } = render(
      <Wrapper>
        <DataAnalystPage />
      </Wrapper>
    )

    const chartCards = container.querySelectorAll('.min-w-0.overflow-hidden')
    // 4 chart cards: publish trend, platform distribution, engagement distribution, MAPE trend
    expect(chartCards.length).toBeGreaterThanOrEqual(4)
  })

  it('chart containers have min-w-0 to prevent overflow', () => {
    mockStore.publishTrend = [{ date: '2024-01-01', total: 1, xiaohongshu: 1, douyin: 0, videoChannel: 0 }]
    mockStore.platformDistribution = [{ name: '小红书', value: 1, color: '#ff2442' }]
    mockStore.engagementDistribution = [{ type: '点赞', likes: 1, comments: 0, saves: 0 }]
    mockStore.mapeTrend = [{ date: '2024-01-01', mape: 0.1 }]
    mockStore.accountComparison = [{ id: 'a1', name: '账号A', platform: 'xiaohongshu', publishCount: 1, avgLikes: 1, healthScore: 90 }]

    const { container } = render(
      <Wrapper>
        <DataAnalystPage />
      </Wrapper>
    )

    const chartWrappers = container.querySelectorAll('.h-64.min-w-0, .h-56.min-w-0')
    // 5 chart containers: 4 in two-column grid + 1 account comparison bar chart
    expect(chartWrappers.length).toBeGreaterThanOrEqual(5)
  })

  it('loads all data sources on mount', () => {
    render(
      <Wrapper>
        <DataAnalystPage />
      </Wrapper>
    )

    expect(mockStore.fetchDashboard).toHaveBeenCalled()
    expect(mockStore.fetchPublishTrend).toHaveBeenCalled()
    expect(mockStore.fetchPlatformDistribution).toHaveBeenCalled()
    expect(mockStore.fetchEngagementDistribution).toHaveBeenCalled()
    expect(mockStore.fetchMapeTrend).toHaveBeenCalled()
    expect(mockStore.fetchContentRanking).toHaveBeenCalled()
    expect(mockStore.fetchAccountComparison).toHaveBeenCalled()
    expect(mockStore.fetchReportList).toHaveBeenCalled()
    expect(mockStore.fetchCalibrationStatus).toHaveBeenCalled()
    expect(mockStore.fetchImportHistory).toHaveBeenCalled()
  })
})
