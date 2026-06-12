import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ContentForgePage } from '../ContentForgePage'

const mockStore = {
  drafts: [] as unknown[],
  generated: null as unknown,
  isLoading: false,
  isGenerating: false,
  error: null as string | null,
  personas: [] as unknown[],
  stories: [] as unknown[],
  storyNodes: [] as unknown[],
  contentSeries: [] as unknown[],
  llmModels: [] as unknown[],
  fetchDrafts: vi.fn(),
  createDraft: vi.fn(),
  deleteDraft: vi.fn(),
  submitForReview: vi.fn(),
  generateContent: vi.fn(),
  fetchPersonas: vi.fn(),
  fetchStories: vi.fn(),
  fetchStoryNodes: vi.fn(),
  fetchContentSeries: vi.fn(),
  fetchLLMModels: vi.fn(),
  clearGenerated: vi.fn(),
  clearError: vi.fn(),
}

vi.mock('react-router-dom', () => {
  return {
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
    useParams: () => ({ taskId: undefined }),
  }
})

vi.mock('../../stores/contentForgeStore', () => ({
  useContentForgeStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('ContentForgePage', () => {
  beforeEach(() => {
    mockStore.drafts = []
    mockStore.generated = null
    mockStore.isLoading = false
    mockStore.isGenerating = false
    mockStore.error = null
    mockStore.personas = []
    mockStore.stories = []
    mockStore.storyNodes = []
    mockStore.contentSeries = []
    mockStore.llmModels = []
    vi.clearAllMocks()
  })

  it('renders three-column layout when creating content', () => {
    render(<ContentForgePage />)
    fireEvent.click(screen.getAllByRole('button', { name: /新建内容/i })[0])
    expect(screen.getByText('生成配置')).toBeInTheDocument()
    expect(screen.getByText('内容预览')).toBeInTheDocument()
    expect(screen.getByText('Agent 摘要')).toBeInTheDocument()
  })

  it('renders config panel with Topic/Platform/Persona fields', () => {
    render(<ContentForgePage />)
    fireEvent.click(screen.getAllByRole('button', { name: /新建内容/i })[0])
    expect(screen.getByPlaceholderText('输入内容主题...')).toBeInTheDocument()
    expect(screen.getByText('平台')).toBeInTheDocument()
    expect(screen.getByText('选择 Persona')).toBeInTheDocument()
  })

  it('renders content preview area', () => {
    render(<ContentForgePage />)
    fireEvent.click(screen.getAllByRole('button', { name: /新建内容/i })[0])
    expect(screen.getByPlaceholderText('生成后标题显示在这里...')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('生成后正文显示在这里...')).toBeInTheDocument()
  })

  it('renders Agent summary area with quality score / token / duration', () => {
    mockStore.generated = {
      title: 'Test',
      body: 'Body',
      tags: [],
      platform: 'xhs',
      scores: {
        overall: 85,
        title_attractiveness: 80,
        body_completeness: 90,
        tag_relevance: 85,
        cover_quality: 80,
      },
      tokens: {
        prompt_tokens: 100,
        completion_tokens: 200,
        total_tokens: 300,
        estimated_cost_cny: 0.05,
      },
      duration_ms: 1200,
    }
    render(<ContentForgePage />)
    fireEvent.click(screen.getAllByRole('button', { name: /新建内容/i })[0])
    expect(screen.getByText('Agent 摘要')).toBeInTheDocument()
    expect(screen.getByText('Token 消耗')).toBeInTheDocument()
    expect(screen.getByText('生成耗时')).toBeInTheDocument()
    expect(screen.getByText('1200 ms')).toBeInTheDocument()
    expect(screen.getByText('300')).toBeInTheDocument()
  })

  it('highlights sensitive words in compliance preview', () => {
    render(<ContentForgePage />)
    fireEvent.click(screen.getAllByRole('button', { name: /新建内容/i })[0])
    const bodyInput = screen.getByPlaceholderText('生成后正文显示在这里...')
    fireEvent.change(bodyInput, { target: { value: '这是一个处方药推荐' } })
    expect(screen.getByText(/敏感词 1 处/)).toBeInTheDocument()
    expect(document.body.innerHTML).toContain('<mark')
  })
})
