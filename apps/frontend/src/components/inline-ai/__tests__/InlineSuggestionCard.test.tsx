import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { InlineSuggestionCard } from '../InlineSuggestionCard'
import { useInlineAIStore } from '../../../stores/inlineAIStore'

describe('InlineSuggestionCard', () => {
  beforeEach(() => {
    useInlineAIStore.setState({ suggestions: [], dismissedIds: [], selectedTargetId: null })
  })

  it('renders nothing when no suggestions for target', () => {
    const { container } = render(
      <div className="relative">
        <InlineSuggestionCard targetId="card_001" />
      </div>
    )
    expect(container.querySelector('.animate-fade-in')).not.toBeInTheDocument()
  })

  it('shows suggestion when matching targetId', () => {
    useInlineAIStore.setState({
      suggestions: [
        {
          id: 'sg_001',
          type: 'OPTIMIZE',
          title: '优化标题',
          description: '建议缩短标题',
          targetId: 'card_001',
        },
      ],
    })

    render(
      <div className="relative">
        <InlineSuggestionCard targetId="card_001" />
      </div>
    )

    expect(screen.getByText('优化标题')).toBeInTheDocument()
    expect(screen.getByText('建议缩短标题')).toBeInTheDocument()
  })

  it('applies suggestion on click', () => {
    useInlineAIStore.setState({
      suggestions: [
        {
          id: 'sg_001',
          type: 'OPTIMIZE',
          title: '优化标题',
          description: '建议缩短标题',
          targetId: 'card_001',
        },
      ],
    })

    render(
      <div className="relative">
        <InlineSuggestionCard targetId="card_001" />
      </div>
    )

    fireEvent.click(screen.getByText('应用'))
    expect(useInlineAIStore.getState().suggestions).toHaveLength(0)
  })

  it('dismisses suggestion on click', () => {
    useInlineAIStore.setState({
      suggestions: [
        {
          id: 'sg_001',
          type: 'INFO',
          title: '提示',
          description: '这是一条信息',
          targetId: 'card_001',
        },
      ],
    })

    render(
      <div className="relative">
        <InlineSuggestionCard targetId="card_001" />
      </div>
    )

    fireEvent.click(screen.getByText('知道了'))
    expect(useInlineAIStore.getState().suggestions).toHaveLength(0)
    expect(useInlineAIStore.getState().dismissedIds).toContain('sg_001')
  })
})
