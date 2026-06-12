import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { CommandPalette } from '../CommandPalette'

describe('CommandPalette', () => {
  const commands = [
    {
      id: 'create',
      label: '创建内容',
      description: '快速创建一篇新内容',
      group: '最近使用',
      onSelect: vi.fn(),
    },
    {
      id: 'review',
      label: '审核队列',
      description: '5 个待审任务',
      group: '最近使用',
      onSelect: vi.fn(),
    },
    {
      id: 'ai-analyze',
      label: 'AI 分析',
      group: 'AI 快捷操作',
      onSelect: vi.fn(),
    },
  ]

  it('does not render when closed', () => {
    const { container } = render(
      <CommandPalette commands={commands} open={false} onOpenChange={vi.fn()} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders when open', () => {
    render(
      <CommandPalette commands={commands} open={true} onOpenChange={vi.fn()} />
    )
    expect(screen.getByPlaceholderText('搜索命令、页面、快捷操作...')).toBeInTheDocument()
    expect(screen.getByText('创建内容')).toBeInTheDocument()
    expect(screen.getByText('审核队列')).toBeInTheDocument()
  })

  it('filters commands by query', () => {
    render(
      <CommandPalette commands={commands} open={true} onOpenChange={vi.fn()} />
    )
    const input = screen.getByPlaceholderText('搜索命令、页面、快捷操作...')
    fireEvent.change(input, { target: { value: 'AI' } })
    expect(screen.queryByText('创建内容')).not.toBeInTheDocument()
    expect(screen.getByText('AI 分析')).toBeInTheDocument()
  })

  it('executes command on click', () => {
    const onOpenChange = vi.fn()
    render(
      <CommandPalette commands={commands} open={true} onOpenChange={onOpenChange} />
    )
    const btn = screen.getByText('创建内容').closest('button')
    if (btn) fireEvent.click(btn)
    expect(commands[0].onSelect).toHaveBeenCalled()
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('shows empty state when no match', () => {
    render(
      <CommandPalette commands={commands} open={true} onOpenChange={vi.fn()} />
    )
    const input = screen.getByPlaceholderText('搜索命令、页面、快捷操作...')
    fireEvent.change(input, { target: { value: 'zzzzz' } })
    expect(screen.getByText('没有找到匹配命令')).toBeInTheDocument()
  })

  it('renders shortcut badges', () => {
    const cmds = [
      { id: 'test', label: '测试', shortcut: 'Ctrl+N', onSelect: vi.fn() },
    ]
    render(
      <CommandPalette commands={cmds} open={true} onOpenChange={vi.fn()} />
    )
    expect(screen.getByText('Ctrl+N')).toBeInTheDocument()
  })

  it('renders footer', () => {
    render(
      <CommandPalette
        commands={commands}
        open={true}
        onOpenChange={vi.fn()}
        footer={<span data-testid="footer">Custom</span>}
      />
    )
    expect(screen.getByTestId('footer')).toBeInTheDocument()
  })
})
