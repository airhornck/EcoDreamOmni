import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useReviewPublishStore } from './reviewPublishStore'

// Mock authHeaders
vi.mock('../lib/api', () => ({
  authHeaders: () => ({ Authorization: 'Bearer test' }),
}))

describe('reviewPublishStore — fetchConclusions', () => {
  beforeEach(() => {
    useReviewPublishStore.setState({
      conclusions: [],
      isLoading: false,
      isDeciding: false,
      error: null,
    })
  })

  it('should fetch conclusions and parse { items } response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [
          { task_id: 't1', task_name: 'Task 1', status: 'human_wait', review_decision: null },
          { task_id: 't2', task_name: 'Task 2', status: 'approved_waiting_publish', review_decision: 'APPROVE' },
        ],
        total: 2,
      }),
    } as Response)

    const store = useReviewPublishStore.getState()
    await store.fetchConclusions()

    expect(useReviewPublishStore.getState().conclusions).toHaveLength(2)
    expect(useReviewPublishStore.getState().conclusions[0].task_id).toBe('t1')
    expect(useReviewPublishStore.getState().isLoading).toBe(false)
    expect(useReviewPublishStore.getState().error).toBeNull()
  })

  it('should handle empty items response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ items: [], total: 0 }),
    } as Response)

    const store = useReviewPublishStore.getState()
    await store.fetchConclusions()

    expect(useReviewPublishStore.getState().conclusions).toEqual([])
  })

  it('should set error on API failure', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Server error' }),
    } as Response)

    const store = useReviewPublishStore.getState()
    await store.fetchConclusions()

    expect(useReviewPublishStore.getState().error).toContain('获取审核结论失败: 500')
    expect(useReviewPublishStore.getState().isLoading).toBe(false)
  })
})

describe('reviewPublishStore — decideTask', () => {
  beforeEach(() => {
    useReviewPublishStore.setState({
      conclusions: [],
      isLoading: false,
      isDeciding: false,
      error: null,
    })
  })

  it('should set isDeciding while calling decideTask', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'APPROVED_WAITING_PUBLISH' }),
    } as Response)

    const store = useReviewPublishStore.getState()
    expect(store.isDeciding).toBe(false)

    const promise = store.decideTask('task_1', 'approve')
    expect(useReviewPublishStore.getState().isDeciding).toBe(true)

    const result = await promise
    expect(result.success).toBe(true)
    expect(useReviewPublishStore.getState().isDeciding).toBe(false)
  })

  it('should call correct endpoint for reject with reason', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'REJECTED' }),
    } as Response)

    const store = useReviewPublishStore.getState()
    await store.decideTask('task_1', 'reject', '违规内容')

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/human-in-the-loop/tasks/task_1/reject',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ reason: '违规内容' }),
      })
    )
  })

  it('should handle API error gracefully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Task not found' }),
    } as Response)

    const store = useReviewPublishStore.getState()
    const result = await store.decideTask('bad_id', 'approve')

    expect(result.success).toBe(false)
    expect(useReviewPublishStore.getState().error).toContain('Task not found')
    expect(useReviewPublishStore.getState().isDeciding).toBe(false)
  })
})
