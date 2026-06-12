import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SkillHubPage } from './SkillHubPage'

const mockStore = {
  skills: [] as unknown[],
  bindings: [] as unknown[],
  isLoading: false,
  error: null as string | null,
  activeLevel: null as string | null,
  activeTab: 'skills' as const,
  fetchSkills: vi.fn(),
  createSkill: vi.fn(),
  bindSkill: vi.fn(),
  executeSkill: vi.fn(),
  setActiveLevel: vi.fn(),
  setActiveTab: vi.fn(),
  clearError: vi.fn(),
}

vi.mock('../stores/skillHubStore', () => ({
  useSkillHubStore: (selector?: (s: typeof mockStore) => unknown) => {
    return selector ? selector(mockStore) : mockStore
  },
}))

vi.mock('../stores/agentOrchestraStore', () => ({
  useAgentOrchestraStore: () => ({
    agents: [],
    fetchAgents: vi.fn(),
  }),
}))

describe('SkillHubPage', () => {
  beforeEach(() => {
    mockStore.skills = []
    mockStore.bindings = []
    mockStore.isLoading = false
    mockStore.error = null
    mockStore.activeLevel = null
    mockStore.activeTab = 'skills'
    vi.clearAllMocks()
  })

  it('renders page title', () => {
    render(<SkillHubPage />)
    expect(screen.getByRole('heading', { name: '技能中心' })).toBeInTheDocument()
    expect(screen.getByText(/管理 Agent 技能注册、绑定与执行测试/i)).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockStore.isLoading = true
    render(<SkillHubPage />)
    expect(screen.getByText(/加载中/i)).toBeInTheDocument()
  })

  it('displays skill list', () => {
    mockStore.skills = [
      { id: 's1', name: '内容生成', level: 'L1', version: '1.0.0', status: 'active', tags: ['内容'], description: '', code: '', created_at: '', updated_at: '' },
      { id: 's2', name: '合规检测', level: 'L1', version: '1.0.0', status: 'active', tags: ['合规'], description: '', code: '', created_at: '', updated_at: '' },
    ]
    render(<SkillHubPage />)
    expect(screen.getByText('内容生成')).toBeInTheDocument()
    expect(screen.getByText('合规检测')).toBeInTheDocument()
  })

  it('filters skills by level when clicking filter buttons', () => {
    render(<SkillHubPage />)
    const l1Btn = screen.getByRole('button', { name: /L1 内置/i })
    fireEvent.click(l1Btn)
    expect(mockStore.setActiveLevel).toHaveBeenCalledWith('L1')
  })

  it('shows create skill form when clicking create button', () => {
    render(<SkillHubPage />)
    fireEvent.click(screen.getByRole('button', { name: /创建技能/i }))
    expect(screen.getByLabelText(/技能名称/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/层级/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/代码/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/版本/i)).toBeInTheDocument()
  })

  it('switches to binding tab', () => {
    render(<SkillHubPage />)
    fireEvent.click(screen.getByRole('button', { name: /Agent 绑定/i }))
    expect(mockStore.setActiveTab).toHaveBeenCalledWith('bindings')
  })

  it('shows error banner when error exists', () => {
    mockStore.error = '加载失败'
    render(<SkillHubPage />)
    expect(screen.getByText('加载失败')).toBeInTheDocument()
  })
})
