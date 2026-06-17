import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useTaskHubStore } from './taskHubStore'

vi.mock('../lib/api', () => ({
  authHeaders: () => ({ Authorization: 'Bearer test' }),
}))

const baseTask = {
  id: 't1',
  name: 'Task 1',
  status: 'running',
  priority: 1,
  account_id: 'a1',
  persona_id: 'p1',
  created_at: '2024-01-01T00:00:00Z',
}

describe('taskHubStore', () => {
  beforeEach(() => {
    useTaskHubStore.setState({
      tasks: [],
      contentSeries: [],
      dlqItems: [],
      accounts: [],
      personas: [],
      personaStories: [],
      platformSchemas: [],
      agents: [],
      isLoading: false,
      isFormLoading: false,
      error: null,
    })
  })

  it('fetchTasks parses { items } response from /api/task-hub/tasks', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [baseTask],
        copilot_summary: { kanban_stats: {} },
      }),
    } as Response)

    await useTaskHubStore.getState().fetchTasks()

    const state = useTaskHubStore.getState()
    expect(state.tasks).toHaveLength(1)
    expect(state.tasks[0].id).toBe('t1')
    expect(state.isLoading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('fetchTasks falls back to empty array when items is missing', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ copilot_summary: {} }),
    } as Response)

    await useTaskHubStore.getState().fetchTasks()

    expect(useTaskHubStore.getState().tasks).toEqual([])
  })

  it('fetchTasks records HTTP status on API failure', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Server error' }),
    } as Response)

    await useTaskHubStore.getState().fetchTasks()

    expect(useTaskHubStore.getState().error).toContain('500')
  })
})
