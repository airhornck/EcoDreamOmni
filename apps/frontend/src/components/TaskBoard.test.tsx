import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TaskBoard } from './TaskBoard'

const mockTasks = [
  { id: 't1', draft_id: 'd1', account_id: 'a1', platform: 'xhs', status: 'pending', scheduled_at: null },
  { id: 't2', draft_id: 'd2', account_id: 'a2', platform: 'douyin', status: 'scheduled', scheduled_at: '2026-05-15T10:00:00Z' },
  { id: 't3', draft_id: 'd3', account_id: 'a3', platform: 'xhs', status: 'published', published_url: 'https://xhs.com/x1' },
  { id: 't4', draft_id: 'd4', account_id: 'a4', platform: 'douyin', status: 'failed', error_reason: 'Cookie expired' },
]

vi.mock('../stores/dashboardStore', () => ({
  useDashboardStore: (selector?: (s: unknown) => unknown) => {
    const store = {
      publishTasks: mockTasks,
      fetchPublishTasks: vi.fn(),
    }
    return selector ? selector(store) : store
  },
}))

describe('TaskBoard', () => {
  beforeEach(() => {
    // Reset mock tasks if needed
    vi.clearAllMocks()
  })

  it('renders task board title', () => {
    render(<TaskBoard />)
    expect(screen.getByText(/发布任务看板/i)).toBeInTheDocument()
  })

  it('renders tasks with correct status badges', () => {
    render(<TaskBoard />)
    expect(screen.getByText('待处理')).toBeInTheDocument()
    expect(screen.getByText('已调度')).toBeInTheDocument()
    expect(screen.getByText('已发布')).toBeInTheDocument()
    expect(screen.getByText('失败')).toBeInTheDocument()
  })

  it('shows published link for published tasks', () => {
    render(<TaskBoard />)
    expect(screen.getByText(/查看/i)).toBeInTheDocument()
  })

  it('shows error reason for failed tasks', () => {
    render(<TaskBoard />)
    expect(screen.getByText(/Cookie expired/i)).toBeInTheDocument()
  })
})
