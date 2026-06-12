import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { TaskHubCreatePage } from '../TaskHubCreatePage'

// Copilot action handler — captured from page useEffect
let copilotActionHandler: ((cardId: string, actionId: string) => void) | null = null

// Mock Zustand store
vi.mock('../../stores/taskHubStore', () => ({
  useTaskHubStore: () => ({
    accounts: [{ id: 'acc_001', username: '小艾养猫记', platform: 'xiaohongshu' }],
    personas: [{ id: 'per_001', name: '省钱铲屎官' }],
    personaStories: [],
    agents: [
      {
        id: 'content_forge_xhs_image',
        name: '小红书图文生成 Agent',
        role: 'content_generation',
        description: '专为小红书图文笔记优化',
        skills: ['text_generate'],
        supported_platforms: ['xiaohongshu'],
        supported_formats: ['图文'],
        config: {},
        success_rate: 0.94,
        recent_tasks_1h: 12,
        status: 'ACTIVE',
        created_at: '',
        updated_at: '',
      },
    ],
    contentSeries: [],
    platformSchemas: [
      {
        id: 'schema_001',
        platform_id: 'xiaohongshu',
        display_name: '小红书',
        version: '1',
        content_dna: [],
        audit_rules: [],
        content_formats: [{ format_name: '图文', fields: [] }],
      },
    ],
    isFormLoading: false,
    error: null,
    fetchAccounts: vi.fn(),
    fetchPersonas: vi.fn(),
    fetchAgents: vi.fn(),
    fetchContentSeries: vi.fn(),
    fetchPlatformSchemas: vi.fn(),
    fetchPersonaStories: vi.fn(),
    fetchPersonaStoryNodes: vi.fn(),
    createTask: vi.fn().mockResolvedValue(true),
  }),
}))

vi.mock('../../stores/aiCopilotStore', () => ({
  useAICopilotStore: () => ({
    setPageActionCards: vi.fn(),
    setQuickActions: vi.fn(),
    setWelcomeMessage: vi.fn(),
    setPageActionHandler: (handler: typeof copilotActionHandler) => {
      copilotActionHandler = handler
    },
  }),
}))

const strategyStoreMock = {
  elements: [],
  setElements: vi.fn(),
  currentStrategy: { name: null, elements: [], variables: {}, custom_fragments: [] },
  addElementToStrategy: vi.fn(),
  removeElementFromStrategy: vi.fn(),
  moveElement: vi.fn(),
  setElementPriority: vi.fn(),
  setStrategyVariable: vi.fn(),
}

vi.mock('../../stores/strategyStore', () => ({
  useStrategyStore: () => strategyStoreMock,
}))

vi.mock('../../hooks/useStrategyQueries', () => ({
  useStrategyElements: () => ({ data: [], isSuccess: true }),
  useStrategyElementRecommendations: () => ({ data: [], isLoading: false }),
}))

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('TaskHubCreatePage', () => {
  beforeEach(() => {
    queryClient.clear()
    copilotActionHandler = null
  })

  it('renders 4-step wizard', () => {
    renderWithProviders(<TaskHubCreatePage />)

    expect(screen.getAllByText('基础配置').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('主题与策略').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Agent 选择').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('发布确认').length).toBeGreaterThanOrEqual(1)
  })

  it('shows Step 1 (Basic Config) by default', () => {
    renderWithProviders(<TaskHubCreatePage />)

    expect(screen.getByPlaceholderText('输入任务名称')).toBeInTheDocument()
    expect(screen.getByText('目标平台')).toBeInTheDocument()
  })

  it('shows Step 2 with theme and strategy section', async () => {
    renderWithProviders(<TaskHubCreatePage />)

    // Wait for useEffect to register the handler
    await waitFor(() => expect(copilotActionHandler).not.toBeNull())

    // Fill Step 1
    fireEvent.change(screen.getByPlaceholderText('输入任务名称'), {
      target: { value: '测试任务' },
    })
    fireEvent.change(screen.getByDisplayValue('选择平台'), {
      target: { value: 'xiaohongshu' },
    })
    fireEvent.change(screen.getByDisplayValue('选择内容格式'), {
      target: { value: '图文' },
    })
    fireEvent.change(screen.getByDisplayValue('选择账号'), {
      target: { value: 'acc_001' },
    })

    // Advance to Step 2
    act(() => {
      copilotActionHandler?.('', '下一步')
    })

    await waitFor(() => {
      expect(screen.getByText('基础关联（可选）')).toBeInTheDocument()
      expect(screen.getByText('策略元素组合')).toBeInTheDocument()
    })
  })

  it('advances to Step 2 after filling Step 1', async () => {
    renderWithProviders(<TaskHubCreatePage />)

    await waitFor(() => expect(copilotActionHandler).not.toBeNull())

    fireEvent.change(screen.getByPlaceholderText('输入任务名称'), {
      target: { value: '测试任务' },
    })
    fireEvent.change(screen.getByDisplayValue('选择平台'), {
      target: { value: 'xiaohongshu' },
    })
    fireEvent.change(screen.getByDisplayValue('选择内容格式'), {
      target: { value: '图文' },
    })
    fireEvent.change(screen.getByDisplayValue('选择账号'), {
      target: { value: 'acc_001' },
    })

    act(() => {
      copilotActionHandler?.('', '下一步')
    })

    await waitFor(() => {
      expect(screen.getByText('策略元素组合')).toBeInTheDocument()
    })
  })

  it('renders Agent selection cards in Step 3', async () => {
    renderWithProviders(<TaskHubCreatePage />)

    await waitFor(() => expect(copilotActionHandler).not.toBeNull())

    // Fill Step 1
    fireEvent.change(screen.getByPlaceholderText('输入任务名称'), {
      target: { value: '测试任务' },
    })
    fireEvent.change(screen.getByDisplayValue('选择平台'), {
      target: { value: 'xiaohongshu' },
    })
    fireEvent.change(screen.getByDisplayValue('选择内容格式'), {
      target: { value: '图文' },
    })
    fireEvent.change(screen.getByDisplayValue('选择账号'), {
      target: { value: 'acc_001' },
    })

    // Advance to Step 2
    act(() => {
      copilotActionHandler?.('', '下一步')
    })

    await waitFor(() => {
      expect(screen.getByText('策略元素组合')).toBeInTheDocument()
    })

    // Advance to Step 3
    act(() => {
      copilotActionHandler?.('', '下一步')
    })

    // Step 3 - Agent Select
    await waitFor(() => {
      expect(screen.getByText('选择执行 Agent')).toBeInTheDocument()
      expect(screen.getByText('小红书图文生成 Agent')).toBeInTheDocument()
      expect(screen.getByText('✨ 推荐')).toBeInTheDocument()
    })
  })
})
