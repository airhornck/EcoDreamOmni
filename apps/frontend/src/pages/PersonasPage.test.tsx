import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PersonasPage } from './PersonasPage'
import { usePersonaPoolStore } from '../stores/personaPoolStore'
import { usePersonaStoryStore } from '../stores/personaStoryStore'

vi.mock('../stores/personaPoolStore', () => ({
  usePersonaPoolStore: vi.fn(),
}))

vi.mock('../stores/personaStoryStore', () => ({
  usePersonaStoryStore: vi.fn(),
}))

function mockPersonaPoolStore(overrides: Partial<ReturnType<typeof usePersonaPoolStore>> = {}) {
  const defaultState = {
    personas: [
      { id: 'p1', name: '人设A', voice_style: '温暖亲切', target_platforms: ['xhs'] },
    ],
    isLoading: false,
    error: null,
    fetchPersonas: vi.fn(),
    createPersona: vi.fn(),
    deletePersona: vi.fn(),
  }
  return { ...defaultState, ...overrides }
}

function mockPersonaStoryStore(overrides: Partial<ReturnType<typeof usePersonaStoryStore>> = {}) {
  const defaultState = {
    stories: [
      { id: 's1', persona_id: 'p1', name: '剧本一', description: 'desc', emotion_curve_template: 'gradual_growth', status: 'draft' as const, nodes_count: 2 },
    ],
    nodes: [
      { id: 'n1', story_id: 's1', sequence_index: 0, theme: '开篇', emotion_tone: 'medium' as const, key_event: 'event1' },
      { id: 'n2', story_id: 's1', sequence_index: 1, theme: '转折', emotion_tone: 'high' as const, key_event: 'event2' },
    ],
    currentStory: null,
    storyContext: null,
    isLoading: false,
    error: null,
    fetchStories: vi.fn(),
    fetchStory: vi.fn(),
    createStory: vi.fn(),
    updateStory: vi.fn(),
    deleteStory: vi.fn(),
    cloneStory: vi.fn(),
    updateStoryStatus: vi.fn(),
    fetchNodes: vi.fn(),
    createNode: vi.fn(),
    updateNode: vi.fn(),
    deleteNode: vi.fn(),
    reorderNodes: vi.fn(),
    fetchStoryContext: vi.fn(),
    bindContentToNode: vi.fn(),
    clearError: vi.fn(),
  }
  return { ...defaultState, ...overrides }
}

describe('PersonasPage', () => {
  it('renders personas tab by default', () => {
    vi.mocked(usePersonaPoolStore).mockReturnValue(mockPersonaPoolStore())
    vi.mocked(usePersonaStoryStore).mockReturnValue(mockPersonaStoryStore())
    render(<PersonasPage />)
    expect(screen.getAllByText('人设列表').length).toBeGreaterThanOrEqual(1)
  })

  it('switches to stories tab and renders story list', () => {
    vi.mocked(usePersonaPoolStore).mockReturnValue(mockPersonaPoolStore())
    vi.mocked(usePersonaStoryStore).mockReturnValue(mockPersonaStoryStore())
    render(<PersonasPage />)
    fireEvent.click(screen.getByText('故事剧本'))
    expect(screen.getByText('剧本一')).toBeInTheDocument()
  })

  it('renders node reorder buttons when editing a story', async () => {
    const story = { id: 's1', persona_id: 'p1', name: '剧本一', description: 'desc', emotion_curve_template: 'gradual_growth', status: 'draft' as const, nodes_count: 2 }
    vi.mocked(usePersonaPoolStore).mockReturnValue(mockPersonaPoolStore())
    vi.mocked(usePersonaStoryStore).mockReturnValue(
      mockPersonaStoryStore({
        stories: [story],
      })
    )
    render(<PersonasPage />)
    fireEvent.click(screen.getByText('故事剧本'))
    fireEvent.click(screen.getByText('剧本一'))
    // When editing, node timeline with reorder buttons should appear
    expect(await screen.findByText('节点时间轴')).toBeInTheDocument()
    expect(screen.getAllByTitle('左移').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByTitle('右移').length).toBeGreaterThanOrEqual(1)
  })

  it('calls reorderNodes when clicking move buttons', async () => {
    const reorderNodes = vi.fn()
    const story = { id: 's1', persona_id: 'p1', name: '剧本一', description: 'desc', emotion_curve_template: 'gradual_growth', status: 'draft' as const, nodes_count: 2 }
    vi.mocked(usePersonaPoolStore).mockReturnValue(mockPersonaPoolStore())
    vi.mocked(usePersonaStoryStore).mockReturnValue(
      mockPersonaStoryStore({
        stories: [story],
        reorderNodes,
      })
    )
    render(<PersonasPage />)
    fireEvent.click(screen.getByText('故事剧本'))
    fireEvent.click(screen.getByText('剧本一'))

    await screen.findByText('节点时间轴')
    const rightBtns = screen.getAllByTitle('右移')
    // Click the first right-move button (first node moving right)
    fireEvent.click(rightBtns[0])
    expect(reorderNodes).toHaveBeenCalledWith('s1', ['n2', 'n1'])
  })

  it('keeps editor open after saving an existing story', async () => {
    const story = { id: 's1', persona_id: 'p1', name: '剧本一', description: 'desc', emotion_curve_template: 'gradual_growth', status: 'draft' as const, nodes_count: 2 }
    const updateStory = vi.fn().mockResolvedValue(true)
    vi.mocked(usePersonaPoolStore).mockReturnValue(mockPersonaPoolStore())
    vi.mocked(usePersonaStoryStore).mockReturnValue(
      mockPersonaStoryStore({
        stories: [story],
        updateStory,
      })
    )
    render(<PersonasPage />)
    fireEvent.click(screen.getByText('故事剧本'))
    fireEvent.click(screen.getByText('剧本一'))

    await screen.findByText('节点时间轴')
    // Change story name and save
    const nameInput = screen.getByPlaceholderText('输入剧本名称')
    fireEvent.change(nameInput, { target: { value: '剧本一改名' } })
    fireEvent.click(screen.getByText('保存剧本'))

    expect(updateStory).toHaveBeenCalled()
    // Editor should still be open after save
    expect(screen.getByText('节点时间轴')).toBeInTheDocument()
    expect(screen.getByDisplayValue('剧本一改名')).toBeInTheDocument()
  })

  it('opens newly created story automatically after creation', async () => {
    const newStory = { id: 's2', persona_id: 'p1', name: '新剧本', description: '', emotion_curve_template: 'gradual_growth', status: 'draft' as const, nodes_count: 0 }
    const createStory = vi.fn().mockResolvedValue(newStory)
    const fetchNodes = vi.fn()
    vi.mocked(usePersonaPoolStore).mockReturnValue(mockPersonaPoolStore())
    vi.mocked(usePersonaStoryStore).mockReturnValue(
      mockPersonaStoryStore({
        stories: [],
        createStory,
        fetchNodes,
      })
    )
    render(<PersonasPage />)
    fireEvent.click(screen.getByText('故事剧本'))
    fireEvent.click(screen.getByText('新建剧本'))

    // Fill form and save
    const nameInput = screen.getByPlaceholderText('输入剧本名称')
    fireEvent.change(nameInput, { target: { value: '新剧本' } })
    const personaSelect = screen.getByDisplayValue('选择人设')
    fireEvent.change(personaSelect, { target: { value: 'p1' } })
    fireEvent.click(screen.getByText('保存剧本'))

    await waitFor(() => {
      expect(createStory).toHaveBeenCalled()
    })
    // Should automatically open the new story editor
    await waitFor(() => {
      expect(fetchNodes).toHaveBeenCalledWith('s2')
      expect(screen.getByText('节点时间轴')).toBeInTheDocument()
    })
  })
})
