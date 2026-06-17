import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LabPage } from '../../../pages/PlaygroundPage'
import { usePlaygroundStore } from '../../../stores/playgroundStore'

const mockAnalyze = vi.fn()
const mockTemplate = vi.fn()

vi.mock('../../../hooks/useViralAnalyze', () => ({
  useViralAnalyze: () => ({
    mutateAsync: mockAnalyze,
    isPending: false,
    error: null,
  }),
}))

vi.mock('../../../hooks/useViralTemplate', () => ({
  useViralTemplate: () => ({
    mutateAsync: mockTemplate,
    isPending: false,
    error: null,
  }),
}))

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
})

const renderWithQueryClient = (ui: React.ReactNode) =>
  render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)

describe('Lab · 爆款笔记分析 E2E Flow', () => {
  beforeEach(() => {
    usePlaygroundStore.getState().reset()
    queryClient.clear()
    mockAnalyze.mockReset()
    mockTemplate.mockReset()
  })

  it('renders the viral analyzer capability by default', () => {
    renderWithQueryClient(<LabPage />)

    // Capability nav shows all 4 capabilities
    expect(screen.getByText('爆款笔记分析')).toBeInTheDocument()
    expect(screen.getByText('标题优化器')).toBeInTheDocument()
    expect(screen.getByText('封面生成器')).toBeInTheDocument()
    expect(screen.getByText('A/B 测试')).toBeInTheDocument()

    // Default active capability renders the note editor tab
    expect(screen.getByText('笔记编辑')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('粘贴笔记正文...')).toBeInTheDocument()
  })

  it('switches between lab tabs', () => {
    renderWithQueryClient(<LabPage />)

    fireEvent.click(screen.getByText('报告详情'))
    expect(screen.getByText('报告详情')).toBeInTheDocument()

    fireEvent.click(screen.getByText('模板预览'))
    expect(screen.getByText('模板预览')).toBeInTheDocument()
  })

  it('shows analysis preview when a report is loaded', () => {
    usePlaygroundStore.setState({
      analysisReport: {
        note_id: 'note_1',
        structure_type: '清单体',
        structure_confidence: 0.92,
        viral_score: 88,
        scoring_breakdown: {
          completeness: 35,
          keyword_richness: 30,
          emotion_curve: 20,
          interaction_weight: 15,
          emoji_strategy: 10,
        },
        keyword_matches: {
          structure: [],
          function: [],
          emotion: [],
          industry: [],
          effect: [],
        },
        title_analysis: {
          pattern: '数字清单',
          contains_number: true,
          contains_question: false,
          length: 18,
        },
        hook_analysis: {
          hook_type: '痛点共鸣',
          hook_text: '驱虫花了好多钱',
          effectiveness: 0.85,
        },
        body_analysis: {
          sections: 3,
          avg_section_length: 120,
          has_story: true,
          has_data: true,
        },
        cta_analysis: {
          cta_type: '互动引导',
          cta_text: '评论区交流',
          effectiveness: 0.8,
        },
        emoji_analysis: {
          emoji_count: 4,
          emoji_density: '适中',
          top_emojis: ['😱', '✅', '💡', '🎯'],
        },
        emotion_curve: [
          { segment: 1, emotion: '惊讶', intensity: 0.8 },
          { segment: 2, emotion: '信任', intensity: 0.7 },
        ],
        success_factors: ['结构清晰', '痛点精准', '数据支撑'],
      },
      activeTab: 'preview',
      copilotState: 'analyzed',
    })

    renderWithQueryClient(<LabPage />)

    expect(screen.getByText('识别结构类型')).toBeInTheDocument()
    expect(screen.getByText('清单体')).toBeInTheDocument()
  })
})
