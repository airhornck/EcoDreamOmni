import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { WorkflowCockpitPage } from './WorkflowCockpitPage'
import { useWorkflowCockpitStore } from '../stores/workflowCockpitStore'

vi.mock('../stores/workflowCockpitStore', () => ({
  useWorkflowCockpitStore: vi.fn(),
}))

function mockStore(overrides: Partial<ReturnType<typeof useWorkflowCockpitStore>> = {}) {
  const defaultState = {
    tasks: [],
    templates: [],
    executions: [],
    isLoading: false,
    error: null,
    activeTab: 'kanban' as const,
    fetchTasks: vi.fn(),
    fetchTemplates: vi.fn(),
    fetchExecutions: vi.fn(),
    startExecution: vi.fn(),
    executeNext: vi.fn(),
    transitionTask: vi.fn(),
    setActiveTab: vi.fn(),
    clearError: vi.fn(),
  }
  return { ...defaultState, ...overrides }
}

describe('WorkflowCockpitPage', () => {
  it('renders header and tabs', () => {
    const state = mockStore()
    vi.mocked(useWorkflowCockpitStore).mockReturnValue(state)
    render(<WorkflowCockpitPage />)
    expect(screen.getByRole('heading', { name: '工作流驾驶舱' })).toBeInTheDocument()
    expect(screen.getByText('任务 Kanban')).toBeInTheDocument()
    expect(screen.getByText('工作流模板')).toBeInTheDocument()
    expect(screen.getByText('执行监控')).toBeInTheDocument()
  })

  it('renders kanban columns with tasks', () => {
    const state = mockStore({
      activeTab: 'kanban',
      tasks: [
        { id: 'task_1', name: 'Post A', status: 'RUNNING', account_id: 'acc_1', workflow_template_id: 'wf_1', priority: 80, current_node_index: 2, created_at: '' },
        { id: 'task_2', name: 'Post B', status: 'HUMAN_WAIT', account_id: 'acc_2', workflow_template_id: 'wf_1', priority: 60, current_node_index: 3, created_at: '' },
        { id: 'task_3', name: 'Post C', status: 'COMPLETED', account_id: 'acc_1', workflow_template_id: 'wf_1', priority: 40, current_node_index: 5, created_at: '' },
      ],
    })
    vi.mocked(useWorkflowCockpitStore).mockReturnValue(state)
    render(<WorkflowCockpitPage />)
    expect(screen.getByText('Post A')).toBeInTheDocument()
    expect(screen.getByText('Post B')).toBeInTheDocument()
    expect(screen.getByText('Post C')).toBeInTheDocument()
    expect(screen.getByText('P80')).toBeInTheDocument()
  })

  it('allows approving human_wait tasks from kanban', () => {
    const transitionTask = vi.fn()
    const state = mockStore({
      activeTab: 'kanban',
      tasks: [
        { id: 'task_1', name: 'Post B', status: 'HUMAN_WAIT', account_id: 'acc_2', workflow_template_id: 'wf_1', priority: 60, current_node_index: 3, created_at: '' },
      ],
      transitionTask,
    })
    vi.mocked(useWorkflowCockpitStore).mockReturnValue(state)
    render(<WorkflowCockpitPage />)
    fireEvent.click(screen.getByText('通过'))
    expect(transitionTask).toHaveBeenCalledWith('task_1', 'RUNNING')
  })

  it('renders workflow templates with node pipeline', () => {
    const state = mockStore({
      activeTab: 'templates',
      templates: [
        {
          id: 'wf_1',
          name: 'Standard Pipeline',
          description: 'Content creation standard',
          status: 'ACTIVE',
          nodes: [
            { node_index: 0, node_type: 'AGENT', node_name: 'Generate', fail_strategy: 'FAIL_FAST' },
            { node_index: 1, node_type: 'HUMAN_APPROVAL', node_name: 'Review' },
            { node_index: 2, node_type: 'AGENT', node_name: 'Publish', fail_strategy: 'CONTINUE' },
          ],
        },
      ],
    })
    vi.mocked(useWorkflowCockpitStore).mockReturnValue(state)
    render(<WorkflowCockpitPage />)
    expect(screen.getByText('Standard Pipeline')).toBeInTheDocument()
    expect(screen.getByText('Generate')).toBeInTheDocument()
    expect(screen.getByText('Review')).toBeInTheDocument()
    expect(screen.getByText('Publish')).toBeInTheDocument()
    expect(screen.getByText('CONTINUE')).toBeInTheDocument()
  })

  it('renders execution monitor table', () => {
    const state = mockStore({
      activeTab: 'executions',
      executions: [
        { id: 'exec_1', task_id: 'task_1', template_id: 'wf_1', status: 'COMPLETED', current_node_index: 5, context: { result: 'ok' }, started_at: '', ended_at: '' },
      ],
    })
    vi.mocked(useWorkflowCockpitStore).mockReturnValue(state)
    render(<WorkflowCockpitPage />)
    expect(screen.getByText('COMPLETED')).toBeInTheDocument()
  })

  it('switches tabs', () => {
    const setActiveTab = vi.fn()
    const state = mockStore({ setActiveTab })
    vi.mocked(useWorkflowCockpitStore).mockReturnValue(state)
    render(<WorkflowCockpitPage />)
    fireEvent.click(screen.getByText('执行监控'))
    expect(setActiveTab).toHaveBeenCalledWith('executions')
  })
})
