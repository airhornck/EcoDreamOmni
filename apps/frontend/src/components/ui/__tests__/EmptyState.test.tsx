import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { FileText } from 'lucide-react'
import { EmptyState } from '../EmptyState'

describe('EmptyState', () => {
  it('renders title', () => {
    render(<EmptyState title="暂无内容" />)
    expect(screen.getByText('暂无内容')).toBeInTheDocument()
  })

  it('renders description', () => {
    render(<EmptyState title="暂无内容" description="开始创建吧" />)
    expect(screen.getByText('开始创建吧')).toBeInTheDocument()
  })

  it('renders Lucide icon', () => {
    render(<EmptyState title="暂无" icon={FileText} data-testid="es" />)
    const es = screen.getByTestId('es')
    expect(es.querySelector('svg')).toBeInTheDocument()
  })

  it('renders emoji', () => {
    render(<EmptyState title="暂无" emoji="📝" data-testid="es" />)
    const es = screen.getByTestId('es')
    expect(es.textContent).toContain('📝')
  })

  it('renders action', () => {
    render(
      <EmptyState
        title="暂无"
        action={<button data-testid="btn">创建</button>}
      />
    )
    expect(screen.getByTestId('btn')).toBeInTheDocument()
  })

  it('renders AI suggestion', () => {
    render(
      <EmptyState
        title="暂无内容"
        aiSuggestion="根据最近热度话题生成内容"
      />
    )
    expect(screen.getByText(/根据最近热度话题生成内容/)).toBeInTheDocument()
    expect(screen.getByText(/AI 建议/)).toBeInTheDocument()
  })

  it('does not render AI suggestion when not provided', () => {
    render(<EmptyState title="暂无" />)
    expect(screen.queryByText(/AI 建议/)).not.toBeInTheDocument()
  })
})
