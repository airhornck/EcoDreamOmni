import { describe, it, expect, vi, beforeEach } from 'vitest'
import { usePersonaStoryStore } from './personaStoryStore'

vi.mock('../lib/api', () => ({
  authHeaders: () => ({ Authorization: 'Bearer test' }),
}))

describe('personaStoryStore — node CRUD', () => {
  beforeEach(() => {
    usePersonaStoryStore.setState({
      stories: [],
      nodes: [],
      currentStory: null,
      storyContext: null,
      isLoading: false,
      error: null,
    })
  })

  it('updateNode calls correct endpoint', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: 'n1',
        story_id: 's1',
        sequence_index: 0,
        theme: 'Updated Theme',
        emotion_tone: 'high',
        key_event: 'event',
      }),
    } as Response)

    const store = usePersonaStoryStore.getState()
    const result = await store.updateNode('n1', { theme: 'Updated Theme' })

    expect(result).toBe(true)
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/persona-stories/story-nodes/n1',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ theme: 'Updated Theme' }),
      })
    )
  })

  it('deleteNode calls correct endpoint', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Node deleted' }),
    } as Response)

    usePersonaStoryStore.setState({
      nodes: [
        { id: 'n1', story_id: 's1', sequence_index: 0, theme: 'A', emotion_tone: 'medium', key_event: 'e1' },
      ],
    })

    const store = usePersonaStoryStore.getState()
    const result = await store.deleteNode('n1')

    expect(result).toBe(true)
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/persona-stories/story-nodes/n1',
      expect.objectContaining({
        method: 'DELETE',
      })
    )
    expect(usePersonaStoryStore.getState().nodes).toHaveLength(0)
  })

  it('createNode appends node and returns it', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: 'n2',
        story_id: 's1',
        sequence_index: 1,
        theme: 'New Node',
        emotion_tone: 'low',
        key_event: 'new event',
      }),
    } as Response)

    usePersonaStoryStore.setState({
      nodes: [
        { id: 'n1', story_id: 's1', sequence_index: 0, theme: 'A', emotion_tone: 'medium', key_event: 'e1' },
      ],
    })

    const store = usePersonaStoryStore.getState()
    const node = await store.createNode('s1', {
      sequence_index: 1,
      theme: 'New Node',
      emotion_tone: 'low',
      key_event: 'new event',
    })

    expect(node).not.toBeNull()
    expect(usePersonaStoryStore.getState().nodes).toHaveLength(2)
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/persona-stories/s1/nodes',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          sequence_index: 1,
          theme: 'New Node',
          emotion_tone: 'low',
          key_event: 'new event',
        }),
      })
    )
  })
})
