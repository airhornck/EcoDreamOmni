import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CronCockpitPage } from './CronCockpitPage'
import { useCronCockpitStore } from '../stores/cronCockpitStore'

vi.mock('../stores/cronCockpitStore', () => ({
  useCronCockpitStore: vi.fn(),
}))

function mockStore(overrides: Partial<ReturnType<typeof useCronCockpitStore>> = {}) {
  const defaultState = {
    jobs: [],
    executions: [],
    dlq: [],
    isLoading: false,
    error: null,
    activeTab: 'jobs' as const,
    fetchJobs: vi.fn(),
    fetchExecutions: vi.fn(),
    fetchDLQ: vi.fn(),
    createJob: vi.fn(),
    deleteJob: vi.fn(),
    executeJob: vi.fn(),
    retryExecution: vi.fn(),
    reviewDLQ: vi.fn(),
    setActiveTab: vi.fn(),
    clearError: vi.fn(),
  }
  return { ...defaultState, ...overrides }
}

describe('CronCockpitPage', () => {
  it('renders header and tabs', () => {
    const state = mockStore()
    vi.mocked(useCronCockpitStore).mockReturnValue(state)
    render(<CronCockpitPage />)
    expect(screen.getByRole('heading', { name: '定时任务' })).toBeInTheDocument()
    expect(screen.getByText('执行历史')).toBeInTheDocument()
    expect(screen.getByText('死信队列')).toBeInTheDocument()
  })

  it('shows empty state for jobs', () => {
    const state = mockStore({ activeTab: 'jobs' })
    vi.mocked(useCronCockpitStore).mockReturnValue(state)
    render(<CronCockpitPage />)
    expect(screen.getByText('暂无定时任务')).toBeInTheDocument()
  })

  it('renders job list with actions', () => {
    const deleteJob = vi.fn()
    const executeJob = vi.fn()
    const state = mockStore({
      activeTab: 'jobs',
      jobs: [
        { id: 'job_1', name: 'Daily Sync', schedule: '0 9 * * *', target_type: 'AGENT', target_id: 'a1', status: 'ACTIVE', concurrency_policy: 'SKIP', owner: 'alice' },
      ],
      deleteJob,
      executeJob,
    })
    vi.mocked(useCronCockpitStore).mockReturnValue(state)
    render(<CronCockpitPage />)
    expect(screen.getByText('Daily Sync')).toBeInTheDocument()
    expect(screen.getByText('0 9 * * *')).toBeInTheDocument()
    fireEvent.click(screen.getByTitle('执行'))
    expect(executeJob).toHaveBeenCalledWith('job_1')
    fireEvent.click(screen.getByTitle('删除'))
    expect(deleteJob).toHaveBeenCalledWith('job_1')
  })

  it('renders execution history', () => {
    const state = mockStore({
      activeTab: 'executions',
      executions: [
        { id: 'exec_1', job_id: 'job_1', execution_type: 'MANUAL', status: 'SUCCESS', scheduled_at: '', started_at: null, ended_at: null, duration_ms: null, output_summary: 'Done', error_message: null },
        { id: 'exec_2', job_id: 'job_1', execution_type: 'SCHEDULED', status: 'FAILED', scheduled_at: '', started_at: null, ended_at: null, duration_ms: null, output_summary: null, error_message: 'Timeout' },
      ],
    })
    vi.mocked(useCronCockpitStore).mockReturnValue(state)
    render(<CronCockpitPage />)
    expect(screen.getByText('Done')).toBeInTheDocument()
    expect(screen.getByText('Timeout')).toBeInTheDocument()
  })

  it('renders DLQ with review actions', () => {
    const reviewDLQ = vi.fn()
    const state = mockStore({
      activeTab: 'dlq',
      dlq: [
        { id: 'dlq_1', job_id: 'job_1', execution_id: 'exec_1', failed_at: '', error_message: 'Connection error', error_type: 'RETRYABLE', retry_exhausted: true, status: 'PENDING_REVIEW' },
      ],
      reviewDLQ,
    })
    vi.mocked(useCronCockpitStore).mockReturnValue(state)
    render(<CronCockpitPage />)
    expect(screen.queryByText('Connection error')).not.toBeInTheDocument()
    expect(screen.getByText('已耗尽')).toBeInTheDocument()
    fireEvent.click(screen.getByText('忽略'))
    expect(reviewDLQ).toHaveBeenCalledWith('dlq_1', 'IGNORED', 'admin')
  })

  it('switches tabs', () => {
    const setActiveTab = vi.fn()
    const state = mockStore({ setActiveTab })
    vi.mocked(useCronCockpitStore).mockReturnValue(state)
    render(<CronCockpitPage />)
    fireEvent.click(screen.getByText('死信队列'))
    expect(setActiveTab).toHaveBeenCalledWith('dlq')
  })
})
