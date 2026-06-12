import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAgentOrchestraStore } from './agentOrchestraStore'

vi.mock('../lib/api', () => ({
  authHeaders: () => ({ Authorization: 'Bearer test' }),
}))

describe('agentOrchestraStore — updateAgent / deleteAgent', () => {
  beforeEach(() => {
    useAgentOrchestraStore.setState({
      agents: [
        { id: 'a1', name: 'Agent1', role: 'planner', description: '', skills: ['s1'], config: {}, status: 'active', created_at: '', updated_at: '' },
      ],
      isLoading: false,
      error: null,
    })
  })

  it('updateAgent should replace agent in local state', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'a1', name: 'Updated', role: 'generator', description: 'new', skills: ['s2'], config: {}, status: 'active', created_at: '', updated_at: 'now' }),
    } as Response)

    const store = useAgentOrchestraStore.getState()
    const result = await store.updateAgent('a1', { name: 'Updated', role: 'generator' })

    expect(result).not.toBeNull()
    const agents = useAgentOrchestraStore.getState().agents
    expect(agents[0].name).toBe('Updated')
    expect(agents[0].role).toBe('generator')
  })

  it('deleteAgent should remove agent from local state', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => '',
    } as Response)

    const store = useAgentOrchestraStore.getState()
    const result = await store.deleteAgent('a1')

    expect(result).toBe(true)
    expect(useAgentOrchestraStore.getState().agents).toHaveLength(0)
  })

  it('should handle update error gracefully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Not found' }),
    } as Response)

    const store = useAgentOrchestraStore.getState()
    const result = await store.updateAgent('bad', {})

    expect(result).toBeNull()
    expect(useAgentOrchestraStore.getState().error).toContain('Update: 404')
  })
})
