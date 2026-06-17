import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PlatformRulesPage } from '../PlatformRulesPage'

const mockStore = {
  rules: [] as unknown[],
  isLoading: false,
  error: null as string | null,
  selectedPlatform: 'all' as const,
  ruleHistory: [] as unknown[],
  historyLoading: false,
  evaluateResult: null,
  evaluateLoading: false,
  fetchRules: vi.fn(),
  createRule: vi.fn(),
  updateRule: vi.fn(),
  deleteRule: vi.fn(),
  fetchRuleHistory: vi.fn(),
  evaluateContent: vi.fn(),
  clearEvaluate: vi.fn(),
}

vi.mock('../../stores/platformRulesStore', () => ({
  usePlatformRulesStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

describe('PlatformRulesPage — Copilot 适配', () => {
  beforeEach(() => {
    mockStore.rules = []
    mockStore.error = null
    mockStore.selectedPlatform = 'all'
    vi.clearAllMocks()
  })

  it('renders page header', () => {
    render(<PlatformRulesPage />)
    expect(screen.getByText('平台规则')).toBeInTheDocument()
    expect(screen.getByText('新建规则')).toBeInTheDocument()
  })

  it('uses inline flex layout with main content shrink protection', () => {
    const { container } = render(<PlatformRulesPage />)
    const mainWrapper = container.querySelector('.flex.gap-6.items-start')
    expect(mainWrapper).toBeInTheDocument()
    const mainContent = mainWrapper?.querySelector('.flex-1.min-w-0')
    expect(mainContent).toBeInTheDocument()
  })

  it('rule list and test run cards have shrink protection', () => {
    const { container } = render(<PlatformRulesPage />)
    const cards = container.querySelectorAll('.bg-card.rounded-xl.border.border-border.min-w-0.overflow-hidden')
    expect(cards.length).toBeGreaterThanOrEqual(2)
  })

  it('renders rule list', () => {
    mockStore.rules = [
      {
        id: 'r1',
        name: '禁止处方药',
        layer: 'l1_static',
        platform: 'xiaohongshu',
        action: 'block',
        priority: 100,
        enabled: true,
        version: 1,
        condition_json: { type: 'keyword', keywords: ['处方药'] },
      },
    ]
    render(<PlatformRulesPage />)
    expect(screen.getByText('禁止处方药')).toBeInTheDocument()
  })

  it('opens detail side panel when clicking detail', () => {
    mockStore.rules = [
      {
        id: 'r1',
        name: '禁止处方药',
        layer: 'l1_static',
        platform: 'xiaohongshu',
        action: 'block',
        priority: 100,
        enabled: true,
        version: 1,
        description: '禁止处方药内容',
        condition_json: { type: 'keyword', keywords: ['处方药'] },
      },
    ]
    const { container } = render(<PlatformRulesPage />)
    fireEvent.click(screen.getByTitle('详情'))
    expect(screen.getByText('规则详情')).toBeInTheDocument()

    const aside = container.querySelector('aside')
    expect(aside).toBeInTheDocument()
    expect(aside).toHaveClass('sticky')
    expect(aside).not.toHaveClass('fixed')
  })
})
