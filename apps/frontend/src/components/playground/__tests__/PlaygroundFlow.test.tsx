import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { LabPage } from '../../../pages/PlaygroundPage'
import { usePlaygroundStore } from '../../../stores/playgroundStore'

// Mock fetch for parse/generate
vi.stubGlobal(
  'fetch',
  vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({}),
    })
  )
)

describe('Lab · 爆款笔记分析 E2E Flow', () => {
  beforeEach(() => {
    usePlaygroundStore.getState().reset()
  })

  it('renders all 6 zones', () => {
    render(<LabPage />)

    expect(screen.getByText('爆款输入')).toBeInTheDocument()
    expect(screen.getByText('结构解析')).toBeInTheDocument()
    expect(screen.getByText('模板生成')).toBeInTheDocument()
    expect(screen.getByText('变量替换')).toBeInTheDocument()
    expect(screen.getByText('对比预览')).toBeInTheDocument()
    expect(screen.getByText('一键生成')).toBeInTheDocument()
  })

  it('parses viral content and shows structure', async () => {
    render(<LabPage />)

    const textInput = screen.getByPlaceholderText('或直接粘贴爆款文案内容...')
    fireEvent.change(textInput, { target: { value: '我家狗狗驱虫花了好多钱...' } })

    const parseBtn = screen.getByText('AI 结构解析')
    fireEvent.click(parseBtn)

    await waitFor(() => {
      expect(screen.getByText('Hook 模式')).toBeInTheDocument()
    })
  })

  it('selects template and shows variables', async () => {
    render(<LabPage />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'tmpl_001' } })

    await waitFor(() => {
      expect(screen.getByDisplayValue('省钱狗爸')).toBeInTheDocument()
    })
  })
})
