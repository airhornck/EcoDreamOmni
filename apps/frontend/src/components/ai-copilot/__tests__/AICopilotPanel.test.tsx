import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AICopilotPanel } from '../AICopilotPanel'
import { useAICopilotStore } from '../../../stores/aiCopilotStore'

// Mock the SSE stream hook
vi.mock('../../../hooks/useSSEStream', () => ({
  useSSEStream: () => ({
    messages: [],
    status: 'idle' as const,
    error: null,
    sendMessage: vi.fn(),
    abort: vi.fn(),
    clear: vi.fn(),
  }),
}))

describe('AICopilotPanel', () => {
  beforeEach(() => {
    localStorage.clear()
    // Reset store to initial state
    useAICopilotStore.setState({
      isOpen: true,
      status: 'idle',
      messages: [],
      context: {},
      error: null,
      welcomeMessage: null,
      pageActionCards: [],
      pageActionHandler: null,
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  const renderWithRouter = (ui: React.ReactNode) => render(<MemoryRouter>{ui}</MemoryRouter>)

  it('renders panel with header and input when open', () => {
    renderWithRouter(<AICopilotPanel />)

    expect(screen.getByText('AI Copilot')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('输入指令或问题...')).toBeInTheDocument()
  })

  it('toggles panel opacity to 0 when closed', () => {
    const { container } = renderWithRouter(<AICopilotPanel />)

    const aside = container.querySelector('aside')
    expect(aside).toHaveStyle({ opacity: '1' })

    const closeBtn = screen.getByLabelText('关闭 AI Copilot')
    fireEvent.click(closeBtn)

    // After close, panel opacity should be 0
    expect(aside).toHaveStyle({ opacity: '0' })
    expect(aside).toHaveStyle({ pointerEvents: 'none' })
  })

  it('renders quick actions when open', () => {
    renderWithRouter(<AICopilotPanel />)

    expect(screen.getByText('快捷动作')).toBeInTheDocument()
    expect(screen.getByText('为@省钱狗爸生成驱虫内容')).toBeInTheDocument()
  })

  it('persists open/close state to localStorage', () => {
    renderWithRouter(<AICopilotPanel />)

    const closeBtn = screen.getByLabelText('关闭 AI Copilot')
    fireEvent.click(closeBtn)

    // Verify localStorage was updated
    const stored = localStorage.getItem('ai-copilot-store')
    expect(stored).toBeTruthy()
    const parsed = JSON.parse(stored!)
    expect(parsed.state.isOpen).toBe(false)
  })

  it('restores open/close state from localStorage on mount', () => {
    // Pre-seed localStorage with closed state
    localStorage.setItem(
      'ai-copilot-store',
      JSON.stringify({ state: { isOpen: false }, version: 0 })
    )

    // Re-initialize store to pick up persisted state
    useAICopilotStore.persist.rehydrate()

    const { container } = renderWithRouter(<AICopilotPanel />)

    // Should render closed state (opacity 0)
    const aside = container.querySelector('aside')
    expect(aside).toHaveStyle({ opacity: '0' })
    expect(aside).toHaveStyle({ pointerEvents: 'none' })
  })
})
