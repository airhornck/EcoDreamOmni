import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { StrategyElementsPage } from '../StrategyElementsPage'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

const mockElements = [
  {
    element_id: 'el-1',
    element_type: 'keyword_strategy',
    name: '驱虫关键词包',
    description: '针对宠物驱虫内容的关键词策略',
    content: { keywords: ['驱虫', '猫咪驱虫'] },
    render_template: '{{keywords}}',
    variables: [],
    source: 'manual',
    platform: 'xiaohongshu',
    content_format: 'text',
    usage_count: 12,
    avg_engagement: {},
    effectiveness_score: 0.85,
    status: 'active',
    created_by: 'u1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    element_id: 'el-2',
    element_type: 'hook_pattern',
    name: '悬念Hook',
    description: '用悬念吸引点击',
    content: { text: '你知道吗？' },
    render_template: '{{text}}',
    variables: [],
    source: 'viral_analyzer',
    platform: 'douyin',
    content_format: 'video',
    usage_count: 5,
    avg_engagement: {},
    effectiveness_score: 0.72,
    status: 'draft',
    created_by: 'u1',
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-04T00:00:00Z',
  },
  {
    element_id: 'el-3',
    element_type: 'cta_pattern',
    name: '互动CTA',
    description: '引导评论互动',
    content: { text: '评论区见' },
    render_template: '{{text}}',
    variables: [],
    source: 'ai_generated',
    platform: null,
    content_format: null,
    usage_count: 0,
    avg_engagement: {},
    effectiveness_score: 0,
    status: 'deprecated',
    created_by: 'u1',
    created_at: '2024-01-05T00:00:00Z',
    updated_at: '2024-01-06T00:00:00Z',
  },
]

const mockCreateMutate = vi.fn()
const mockUpdateMutate = vi.fn()
const mockDeleteMutate = vi.fn()

let mockElementsData = mockElements
let mockIsLoading = false

vi.mock('../../hooks/useStrategyQueries', () => ({
  useStrategyElements: () => ({ data: mockElementsData, isLoading: mockIsLoading }),
  useCreateStrategyElement: () => ({
    mutateAsync: mockCreateMutate,
    isPending: false,
  }),
  useUpdateStrategyElement: () => ({
    mutateAsync: mockUpdateMutate,
    isPending: false,
  }),
  useDeleteStrategyElement: () => ({
    mutateAsync: mockDeleteMutate,
    isPending: false,
  }),
}))

const mockAuthStore = {
  user: { id: 'u1', username: 'admin', email: 'a@b.com', role: 'admin' },
}

vi.mock('../../stores/authStore', () => ({
  useAuthStore: () => mockAuthStore,
}))

const mockCopilotStore = {
  setPageActionCards: vi.fn(),
  setPageActionHandler: vi.fn(),
}

vi.mock('../../stores/aiCopilotStore', () => ({
  useAICopilotStore: () => mockCopilotStore,
}))

vi.mock('../../lib/toast', () => ({
  showToast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}))

describe('StrategyElementsPage', () => {
  beforeEach(() => {
    mockElementsData = mockElements
    mockIsLoading = false
    vi.clearAllMocks()
  })

  it('renders page header and stats', () => {
    const { container } = render(<StrategyElementsPage />)
    expect(screen.getByText('策略元素')).toBeInTheDocument()
    expect(screen.getByText('关键词库 + 模板库合并 · 统一策略元素管理')).toBeInTheDocument()
    const statCards = container.querySelectorAll('.grid.grid-cols-2.md\\:grid-cols-4 > div')
    expect(statCards[0]).toHaveTextContent('全部元素')
    expect(statCards[0]).toHaveTextContent('3')
    expect(statCards[1]).toHaveTextContent('生效中')
    expect(statCards[1]).toHaveTextContent('1')
    expect(statCards[2]).toHaveTextContent('爆款分析来源')
    expect(statCards[2]).toHaveTextContent('1')
    expect(statCards[3]).toHaveTextContent('AI 生成来源')
    expect(statCards[3]).toHaveTextContent('1')
  })

  it('renders strategy element grid', () => {
    render(<StrategyElementsPage />)
    expect(screen.getByText('驱虫关键词包')).toBeInTheDocument()
    expect(screen.getByText('悬念Hook')).toBeInTheDocument()
    expect(screen.getByText('互动CTA')).toBeInTheDocument()
  })

  it('filters by element type', () => {
    render(<StrategyElementsPage />)
    const typeSelect = screen.getByDisplayValue('全部类型')
    fireEvent.change(typeSelect, { target: { value: 'hook_pattern' } })
    expect(screen.queryByText('驱虫关键词包')).not.toBeInTheDocument()
    expect(screen.getByText('悬念Hook')).toBeInTheDocument()
    expect(screen.queryByText('互动CTA')).not.toBeInTheDocument()
  })

  it('filters by source', () => {
    render(<StrategyElementsPage />)
    const sourceSelect = screen.getByDisplayValue('全部来源')
    fireEvent.change(sourceSelect, { target: { value: 'manual' } })
    expect(screen.getByText('驱虫关键词包')).toBeInTheDocument()
    expect(screen.queryByText('悬念Hook')).not.toBeInTheDocument()
    expect(screen.queryByText('互动CTA')).not.toBeInTheDocument()
  })

  it('filters by status', () => {
    render(<StrategyElementsPage />)
    const statusSelect = screen.getByDisplayValue('全部状态')
    fireEvent.change(statusSelect, { target: { value: 'draft' } })
    expect(screen.queryByText('驱虫关键词包')).not.toBeInTheDocument()
    expect(screen.getByText('悬念Hook')).toBeInTheDocument()
    expect(screen.queryByText('互动CTA')).not.toBeInTheDocument()
  })

  it('filters by search text', () => {
    render(<StrategyElementsPage />)
    const searchInput = screen.getByPlaceholderText('搜索名称、描述、类型...')
    fireEvent.change(searchInput, { target: { value: '悬念' } })
    expect(screen.queryByText('驱虫关键词包')).not.toBeInTheDocument()
    expect(screen.getByText('悬念Hook')).toBeInTheDocument()
    expect(screen.queryByText('互动CTA')).not.toBeInTheDocument()
  })

  it('switches to list view', () => {
    render(<StrategyElementsPage />)
    const listButton = screen.getByLabelText('列表视图')
    fireEvent.click(listButton)
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('opens detail aside when clicking an element', () => {
    render(<StrategyElementsPage />)
    fireEvent.click(screen.getByText('驱虫关键词包'))
    expect(screen.getByText('策略元素详情')).toBeInTheDocument()
    expect(screen.getByText('应用到任务')).toBeInTheDocument()
  })

  it('navigates to TaskHub create with strategyElementId when applying element', () => {
    render(<StrategyElementsPage />)
    fireEvent.click(screen.getByText('驱虫关键词包'))
    fireEvent.click(screen.getByText('应用到任务'))
    expect(mockNavigate).toHaveBeenCalledWith('/generate/create?strategyElementId=el-1')
  })

  it('opens create form and submits new element', async () => {
    mockCreateMutate.mockResolvedValueOnce({ element_id: 'el-new' })
    render(<StrategyElementsPage />)
    fireEvent.click(screen.getByText('创建元素'))
    expect(screen.getByText('创建策略元素')).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('策略元素名称'), { target: { value: '新元素' } })
    fireEvent.change(screen.getByPlaceholderText('例如：{{content}}'), { target: { value: '{{content}}' } })

    fireEvent.click(screen.getByText('创建'))

    await waitFor(() => {
      expect(mockCreateMutate).toHaveBeenCalled()
    })
    const callArg = mockCreateMutate.mock.calls[0][0]
    expect(callArg.name).toBe('新元素')
    expect(callArg.element_type).toBe('keyword_strategy')
    expect(callArg.created_by).toBe('u1')
  })

  it('opens edit form from detail aside and submits update', async () => {
    mockUpdateMutate.mockResolvedValueOnce({ element_id: 'el-1' })
    render(<StrategyElementsPage />)
    fireEvent.click(screen.getByText('驱虫关键词包'))
    fireEvent.click(screen.getByText('编辑'))
    expect(screen.getByText('编辑策略元素')).toBeInTheDocument()

    fireEvent.change(screen.getByDisplayValue('驱虫关键词包'), { target: { value: '更新后的名称' } })
    fireEvent.click(screen.getByText('保存'))

    await waitFor(() => {
      expect(mockUpdateMutate).toHaveBeenCalled()
    })
    const { elementId, data } = mockUpdateMutate.mock.calls[0][0]
    expect(elementId).toBe('el-1')
    expect(data.name).toBe('更新后的名称')
  })

  it('deletes element after confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValueOnce(true)
    mockDeleteMutate.mockResolvedValueOnce(undefined)
    render(<StrategyElementsPage />)
    fireEvent.click(screen.getByText('驱虫关键词包'))
    fireEvent.click(screen.getByText('删除'))
    await waitFor(() => {
      expect(mockDeleteMutate).toHaveBeenCalledWith('el-1')
    })
  })

  it('uses inline flex layout with shrink protection', () => {
    const { container } = render(<StrategyElementsPage />)
    const mainWrapper = container.querySelector('.flex.gap-6')
    expect(mainWrapper).toBeInTheDocument()
    const mainContent = mainWrapper?.querySelector('.flex-1.min-w-0')
    expect(mainContent).toBeInTheDocument()
  })
})
