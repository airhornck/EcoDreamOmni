import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { TaskHubCreatePage } from '../TaskHubCreatePage'

const mockStore = {
  accounts: [
    { id: 'acc1', username: '账号A', platform: 'xhs' },
    { id: 'acc2', username: '账号B', platform: 'douyin' },
  ],
  personas: [{ id: 'per1', name: '人设A' }],
  personaStories: [{ id: 'story1', name: '故事线1', nodes: [{ id: 'node1', theme: '主题1', label: '节点1' }] }],
  agents: [
    { id: 'content_forge_xhs_image', name: '小红书图文生成 Agent', status: 'ACTIVE', supported_platforms: ['xhs'], supported_formats: ['图文'], skills: ['text_generate_skill'], success_rate: 0.95, recent_tasks_1h: 2, description: 'test' },
  ],
  contentSeries: [{ id: 'cs1', name: '系列A' }],
  platformSchemas: [{ platform_id: 'xhs', display_name: '小红书', rules: [], content_formats: [{ format_name: '图文' }] }],
  isFormLoading: false,
  fetchAccounts: vi.fn(),
  fetchPersonas: vi.fn(),
  fetchAgents: vi.fn(),
  fetchContentSeries: vi.fn(),
  fetchPersonaStories: vi.fn(),
  fetchPlatformSchemas: vi.fn(),
  fetchPersonaStoryNodes: vi.fn().mockResolvedValue([]),
  error: null,
  createTask: vi.fn().mockResolvedValue(true),
}

vi.mock('../../hooks/useStrategyQueries', () => ({
  useStrategyElement: () => ({ data: null, isSuccess: false }),
  useStrategyElements: () => ({ data: undefined, isSuccess: false }),
}))

vi.mock('../../stores/taskHubStore', () => ({
  useTaskHubStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('TaskHubCreatePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the canvas stepper with 4 steps', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )
    expect(screen.getByText('新建任务')).toBeInTheDocument()
    expect(screen.getByTestId('step-node-0')).toBeInTheDocument()
    expect(screen.getByTestId('step-node-1')).toBeInTheDocument()
    expect(screen.getByTestId('step-node-2')).toBeInTheDocument()
    expect(screen.getByTestId('step-node-3')).toBeInTheDocument()
    // Step labels appear in both stepper and node cards
    expect(screen.getAllByText('基础配置').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('主题与策略').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Agent 选择').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('发布确认').length).toBeGreaterThanOrEqual(1)
  })

  it('persists basic config input when collapsing and re-expanding the node', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )

    // First node is expanded by default
    fireEvent.change(screen.getByPlaceholderText('输入任务名称'), { target: { value: '持久化测试' } })

    // Collapse the node by clicking it again
    fireEvent.click(screen.getByTestId('step-node-0'))
    expect(screen.queryByPlaceholderText('输入任务名称')).not.toBeInTheDocument()

    // Re-expand and verify the value persists
    fireEvent.click(screen.getByTestId('step-node-0'))
    expect(screen.getByDisplayValue('持久化测试')).toBeInTheDocument()
  })

  it('fills basic config and shows summary after saving the node', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )

    // First node is expanded by default
    fireEvent.change(screen.getByPlaceholderText('输入任务名称'), { target: { value: '测试任务' } })

    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: 'xhs' } })
    fireEvent.change(selects[1], { target: { value: '图文' } })
    fireEvent.change(selects[2], { target: { value: 'acc1' } })

    fireEvent.click(screen.getByRole('button', { name: '暂存节点' }))

    // Summary should show the task name
    expect(screen.getByText('测试任务')).toBeInTheDocument()
  })

  it('expands the theme strategy node', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByTestId('step-node-1'))
    expect(screen.getByText('基础关联（可选）')).toBeInTheDocument()
  })

  it('expands the agent select node and renders the agent card', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByTestId('step-node-2'))
    expect(screen.getByText('小红书图文生成 Agent')).toBeInTheDocument()
  })

  it('expands the publish confirm node', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByTestId('step-node-3'))
    expect(screen.getByText('配置汇总')).toBeInTheDocument()
  })
})
