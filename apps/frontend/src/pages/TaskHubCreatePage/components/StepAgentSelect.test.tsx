import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { StepAgentSelect } from './StepAgentSelect'
import type { Agent } from '../../../types/api'

const mockAgents: Agent[] = [
  {
    id: 'content_forge_xhs_image',
    name: '小红书图文生成 Agent',
    role: 'content_generation',
    description: '专为小红书图文笔记优化',
    skills: ['text_generate', 'rag_inject'],
    supported_platforms: ['xiaohongshu'],
    supported_formats: ['图文'],
    config: {},
    success_rate: 0.94,
    recent_tasks_1h: 12,
    status: 'ACTIVE',
    created_at: '',
    updated_at: '',
  },
  {
    id: 'content_forge_xhs_video',
    name: '小红书视频生成 Agent',
    role: 'content_generation',
    description: '专为小红书视频内容优化',
    skills: ['video_gen', 'voice_syn'],
    supported_platforms: ['xiaohongshu'],
    supported_formats: ['视频'],
    config: {},
    success_rate: 0.91,
    recent_tasks_1h: 8,
    status: 'ACTIVE',
    created_at: '',
    updated_at: '',
  },
]

describe('StepAgentSelect', () => {
  it('renders agent cards with success rate and task count', () => {
    render(
      <StepAgentSelect
        agents={mockAgents}
        selectedAgentId=""
        recommendedAgentId="content_forge_xhs_image"
        platform="xiaohongshu"
        contentFormat="图文"
        onSelect={vi.fn()}
      />
    )

    expect(screen.getByText('小红书图文生成 Agent')).toBeInTheDocument()
    expect(screen.getByText('成功率 94%')).toBeInTheDocument()
    expect(screen.getByText('近1h 12 任务')).toBeInTheDocument()
    expect(screen.getByText('✨ 推荐')).toBeInTheDocument()
  })

  it('filters agents by platform and format', () => {
    render(
      <StepAgentSelect
        agents={mockAgents}
        selectedAgentId=""
        recommendedAgentId={null}
        platform="xiaohongshu"
        contentFormat="视频"
        onSelect={vi.fn()}
      />
    )

    // Only video agent should show
    expect(screen.getByText('小红书视频生成 Agent')).toBeInTheDocument()
    expect(screen.queryByText('小红书图文生成 Agent')).not.toBeInTheDocument()
  })

  it('calls onSelect when agent card is clicked', () => {
    const onSelect = vi.fn()
    render(
      <StepAgentSelect
        agents={mockAgents}
        selectedAgentId=""
        recommendedAgentId={null}
        platform="xiaohongshu"
        contentFormat="图文"
        onSelect={onSelect}
      />
    )

    fireEvent.click(screen.getByText('小红书图文生成 Agent'))
    expect(onSelect).toHaveBeenCalledWith('content_forge_xhs_image')
  })

  it('shows error message when provided', () => {
    render(
      <StepAgentSelect
        agents={mockAgents}
        selectedAgentId=""
        recommendedAgentId={null}
        platform="xiaohongshu"
        contentFormat="图文"
        error="请选择执行 Agent"
        onSelect={vi.fn()}
      />
    )

    expect(screen.getByText('请选择执行 Agent')).toBeInTheDocument()
  })

  it('shows empty state when no matching agents', () => {
    render(
      <StepAgentSelect
        agents={mockAgents}
        selectedAgentId=""
        recommendedAgentId={null}
        platform="douyin"
        contentFormat="图文"
        onSelect={vi.fn()}
      />
    )

    expect(screen.getByText('🔍 暂无匹配的 Agent')).toBeInTheDocument()
  })
})
