import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LlmCockpitPage } from './LlmCockpitPage'
import { useLlmCockpitStore } from '../stores/llmCockpitStore'

// Mock the store
vi.mock('../stores/llmCockpitStore', () => ({
  useLlmCockpitStore: vi.fn(),
}))

function mockStore(overrides: Partial<ReturnType<typeof useLlmCockpitStore>> = {}) {
  const defaultState = {
    models: [],
    scopeConfigs: [],
    costSummary: null,
    usageLogs: [],
    isLoading: false,
    error: null,
    activeTab: 'models' as const,
    fetchModels: vi.fn(),
    createModel: vi.fn(),
    updateModel: vi.fn(),
    deleteModel: vi.fn(),
    testConnectivity: vi.fn(),
    fetchScopeConfigs: vi.fn(),
    setGlobalDefault: vi.fn(),
    setNodeOverride: vi.fn(),
    removeNodeOverride: vi.fn(),
    fetchCostSummary: vi.fn(),
    fetchUsageLogs: vi.fn(),
    setActiveTab: vi.fn(),
    clearError: vi.fn(),
  }
  return { ...defaultState, ...overrides }
}

describe('LlmCockpitPage', () => {
  it('renders header and tabs', () => {
    const state = mockStore()
    vi.mocked(useLlmCockpitStore).mockReturnValue(state)
    render(<LlmCockpitPage />)
    expect(screen.getByText('LLM Cockpit')).toBeInTheDocument()
    expect(screen.getByText('模型管理')).toBeInTheDocument()
    expect(screen.getByText('应用范围')).toBeInTheDocument()
    expect(screen.getByText('成本看板')).toBeInTheDocument()
    expect(screen.getByText('调用日志')).toBeInTheDocument()
  })

  it('shows empty state for models', () => {
    const state = mockStore({ activeTab: 'models' })
    vi.mocked(useLlmCockpitStore).mockReturnValue(state)
    render(<LlmCockpitPage />)
    expect(screen.getByText('暂无注册模型')).toBeInTheDocument()
  })

  it('renders model list with status badges', () => {
    const state = mockStore({
      activeTab: 'models',
      models: [
        {
          id: 'm1',
          provider: 'deepseek',
          model_name: 'deepseek-chat',
          api_key_masked: '••••••••',
          endpoint_base_url: 'https://api.deepseek.com',
          status: 'active' as const,
          data_training_opt_out: true,
        },
      ],
    })
    vi.mocked(useLlmCockpitStore).mockReturnValue(state)
    render(<LlmCockpitPage />)
    expect(screen.getByText('deepseek')).toBeInTheDocument()
    expect(screen.getByText('deepseek-chat')).toBeInTheDocument()
    expect(screen.getByText('启用')).toBeInTheDocument()
  })

  it('switches tab to costs', () => {
    const setActiveTab = vi.fn()
    const state = mockStore({ setActiveTab })
    vi.mocked(useLlmCockpitStore).mockReturnValue(state)
    render(<LlmCockpitPage />)
    fireEvent.click(screen.getByText('成本看板'))
    expect(setActiveTab).toHaveBeenCalledWith('costs')
  })

  it('renders scope config table', () => {
    const state = mockStore({
      activeTab: 'scopes',
      scopeConfigs: [
        {
          id: 's1',
          scope_type: 'node' as const,
          node_id: 'ContentForge',
          node_type: 'Agent',
          model_id: 'm1',
          model_name: 'GPT-4o',
          temperature: 0.7,
          timeout_seconds: 30,
          source: 'override' as const,
        },
      ],
    })
    vi.mocked(useLlmCockpitStore).mockReturnValue(state)
    render(<LlmCockpitPage />)
    expect(screen.getByText('ContentForge')).toBeInTheDocument()
    expect(screen.getByText('覆盖')).toBeInTheDocument()
  })

  it('renders cost summary cards', () => {
    const state = mockStore({
      activeTab: 'costs',
      costSummary: {
        period_days: 7,
        total_calls: 1200,
        total_input_tokens: 500000,
        total_output_tokens: 200000,
        estimated_cost_cny: 15.5,
        by_model: [{ model_id: 'm1', model_name: 'GPT-4o', calls: 800, cost_cny: 12 }],
        by_node: [{ node_id: 'n1', calls: 400, cost_cny: 6 }],
        trend: [{ date: '2024-01-01', calls: 100, cost_cny: 1.2 }],
      },
    })
    vi.mocked(useLlmCockpitStore).mockReturnValue(state)
    render(<LlmCockpitPage />)
    expect(screen.getByText('今日调用次数')).toBeInTheDocument()
    expect(screen.getByText('1,200')).toBeInTheDocument()
    expect(screen.getByText('¥15.50')).toBeInTheDocument()
  })

  it('renders usage logs table', () => {
    const state = mockStore({
      activeTab: 'logs',
      usageLogs: [
        {
          id: 'l1',
          model_id: 'm1',
          model_name: 'GPT-4o',
          node_id: 'n1',
          provider_region: 'us-east',
          input_tokens: 1000,
          output_tokens: 500,
          latency_ms: 1200,
          status: 'success',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    })
    vi.mocked(useLlmCockpitStore).mockReturnValue(state)
    render(<LlmCockpitPage />)
    expect(screen.getByText('GPT-4o')).toBeInTheDocument()
    expect(screen.getByText('success')).toBeInTheDocument()
  })

  it('shows error banner when error exists', () => {
    const clearError = vi.fn()
    const state = mockStore({ error: 'Network error', clearError })
    vi.mocked(useLlmCockpitStore).mockReturnValue(state)
    render(<LlmCockpitPage />)
    expect(screen.getByText('Network error')).toBeInTheDocument()
  })

  it('uses xl breakpoint for cost dashboard two-column layout', () => {
    const state = mockStore({
      activeTab: 'costs',
      costSummary: {
        period_days: 7,
        total_calls: 100,
        total_input_tokens: 1000,
        total_output_tokens: 500,
        estimated_cost_cny: 10,
        by_model: [{ model_id: 'm1', model_name: 'GPT-4o', calls: 50, cost_cny: 5 }],
        by_node: [{ node_id: 'n1', calls: 50, cost_cny: 5 }],
        trend: [{ date: '2024-01-01', calls: 50, cost_cny: 5 }],
      },
    })
    vi.mocked(useLlmCockpitStore).mockReturnValue(state)
    const { container } = render(<LlmCockpitPage />)
    const twoColGrid = container.querySelector('.grid.grid-cols-1.xl\\:grid-cols-2')
    expect(twoColGrid).toBeInTheDocument()
  })

  it('table wrappers have shrink protection', () => {
    const state = mockStore({
      activeTab: 'models',
      models: [
        {
          id: 'm1',
          provider: 'deepseek',
          model_name: 'deepseek-chat',
          api_key_masked: '••••••••',
          endpoint_base_url: 'https://api.deepseek.com',
          status: 'active',
          data_training_opt_out: true,
        },
      ],
    })
    vi.mocked(useLlmCockpitStore).mockReturnValue(state)
    const { container } = render(<LlmCockpitPage />)
    const tableWrappers = container.querySelectorAll('.bg-card.rounded-xl.border.border-border.overflow-hidden.min-w-0')
    expect(tableWrappers.length).toBeGreaterThanOrEqual(1)
  })
})
