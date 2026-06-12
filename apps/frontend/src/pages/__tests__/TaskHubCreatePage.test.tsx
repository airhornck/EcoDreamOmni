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
  workflowTemplates: [
    { id: 'wf1', name: '模板A', variables: [{ key: 'topic', label: '话题', type: 'string', required: true }] },
  ],
  contentSeries: [{ id: 'cs1', name: '系列A' }],
  platformSchemas: [{ platform_id: 'xhs', display_name: '小红书', rules: [], content_formats: [{ format_name: '图文' }] }],
  isFormLoading: false,
  fetchAccounts: vi.fn(),
  fetchPersonas: vi.fn(),
  fetchAgents: vi.fn(),
  fetchWorkflowTemplates: vi.fn(),
  fetchContentSeries: vi.fn(),
  fetchPersonaStories: vi.fn(),
  fetchPlatformSchemas: vi.fn(),
  fetchPersonaStoryNodes: vi.fn(),
  error: null,
  createTask: vi.fn().mockResolvedValue(true),
}

vi.mock('../../stores/taskHubStore', () => ({
  useTaskHubStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('TaskHubCreatePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders step 1 by default', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )
    expect(screen.getByRole('heading', { name: '基础配置' })).toBeInTheDocument()
    expect(screen.getByPlaceholderText('输入任务名称')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /下一步/i })).toBeInTheDocument()
  })

  it('shows stepper with 4 steps', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )
    // Stepper buttons
    const stepperButtons = screen.getAllByRole('button')
    const stepLabels = ['基础配置', '人设与故事', 'Agent 选择', '发布确认']
    stepLabels.forEach((label) => {
      expect(stepperButtons.some((b) => b.textContent?.includes(label))).toBe(true)
    })
  })

  it('navigates to step 2 when next is clicked with valid step 1', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )
    fireEvent.change(screen.getByPlaceholderText('输入任务名称'), { target: { value: '测试任务' } })
    // Select platform
    let selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: 'xhs' } })
    // Select content format
    selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[1], { target: { value: '图文' } })
    // Select account
    selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[2], { target: { value: 'acc1' } })

    fireEvent.click(screen.getByRole('button', { name: /下一步/i }))
    expect(screen.getByRole('heading', { name: '人设与故事' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /上一步/i })).toBeInTheDocument()
  })

  it('shows validation errors on step 1 when required fields are empty', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )
    fireEvent.click(screen.getByRole('button', { name: /下一步/i }))
    expect(screen.getByText('请输入任务名称')).toBeInTheDocument()
    expect(screen.getByText('请选择目标平台')).toBeInTheDocument()
  })

  it('can go back to previous step', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )
    fireEvent.change(screen.getByPlaceholderText('输入任务名称'), { target: { value: '测试任务' } })
    let selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: 'xhs' } })
    selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[1], { target: { value: '图文' } })
    selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[2], { target: { value: 'acc1' } })

    fireEvent.click(screen.getByRole('button', { name: /下一步/i }))
    expect(screen.getByRole('heading', { name: '人设与故事' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /上一步/i }))
    expect(screen.getByRole('heading', { name: '基础配置' })).toBeInTheDocument()
  })

  it('renders step 4 summary when navigated through all steps', () => {
    render(
      <MemoryRouter>
        <TaskHubCreatePage />
      </MemoryRouter>
    )
    // Step 1
    fireEvent.change(screen.getByPlaceholderText('输入任务名称'), { target: { value: '测试任务' } })
    let selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: 'xhs' } })
    fireEvent.change(selects[1], { target: { value: '图文' } })
    fireEvent.change(selects[2], { target: { value: 'acc1' } })
    fireEvent.click(screen.getByRole('button', { name: /下一步/i }))

    // Step 2
    selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: 'per1' } })
    fireEvent.click(screen.getByRole('button', { name: /下一步/i }))

    // Step 3: Agent 选择
    fireEvent.click(screen.getByRole('button', { name: /小红书图文生成 Agent/i }))
    fireEvent.click(screen.getByRole('button', { name: /下一步/i }))

    // Step 4
    expect(screen.getByRole('heading', { name: '发布确认' })).toBeInTheDocument()
    expect(screen.getByText('配置汇总')).toBeInTheDocument()
    expect(screen.getByText('测试任务')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /确认创建/i })).toBeInTheDocument()
  })
})
