import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ContentCard } from '../ContentCard'

describe('ContentCard', () => {
  it('renders basic content', () => {
    render(
      <ContentCard
        accountName="小艾养猫记"
        title="猫咪驱虫避坑指南"
        data-testid="card"
      />
    )
    expect(screen.getByText('小艾养猫记')).toBeInTheDocument()
    expect(screen.getByText('猫咪驱虫避坑指南')).toBeInTheDocument()
  })

  it('renders platform badge', () => {
    render(
      <ContentCard
        accountName="小艾养猫记"
        title="测试"
        platform="小红书"
        data-testid="card"
      />
    )
    expect(screen.getByText('小红书')).toBeInTheDocument()
  })

  it('renders tags', () => {
    render(
      <ContentCard
        accountName="小艾养猫记"
        title="测试"
        tags={['驱虫', '新手养猫']}
        data-testid="card"
      />
    )
    expect(screen.getByText('驱虫')).toBeInTheDocument()
    expect(screen.getByText('新手养猫')).toBeInTheDocument()
  })

  it('renders compliance score bar', () => {
    render(
      <ContentCard
        accountName="小艾养猫记"
        title="测试"
        complianceScore={96}
        data-testid="card"
      />
    )
    expect(screen.getByText('96分')).toBeInTheDocument()
  })

  it('renders agent trace', () => {
    render(
      <ContentCard
        accountName="小艾养猫记"
        title="测试"
        agentTrace={[
          { name: 'TrendScout', duration: '0.8s', status: 'success' },
          { name: 'ContentForge', duration: '8.5s', status: 'running' },
        ]}
        data-testid="card"
      />
    )
    expect(screen.getByText('TrendScout')).toBeInTheDocument()
    expect(screen.getByText('ContentForge')).toBeInTheDocument()
  })

  it('renders AI suggestion', () => {
    render(
      <ContentCard
        accountName="小艾养猫记"
        title="测试"
        aiSuggestion="标题包含敏感词，建议修改"
        data-testid="card"
      />
    )
    expect(screen.getByText(/标题包含敏感词/)).toBeInTheDocument()
  })

  it('shows AI generating badge', () => {
    render(
      <ContentCard
        accountName="省钱狗爸"
        title="测试"
        aiGenerating
        data-testid="card"
      />
    )
    expect(screen.getByText('AI 生成中')).toBeInTheDocument()
    const card = screen.getByTestId('card')
    expect(card.className).toContain('animate-pulse-glow')
  })

  it('renders custom actions', () => {
    render(
      <ContentCard
        accountName="小艾养猫记"
        title="测试"
        actions={<button data-testid="action-btn">发布</button>}
        data-testid="card"
      />
    )
    expect(screen.getByTestId('action-btn')).toBeInTheDocument()
  })
})
