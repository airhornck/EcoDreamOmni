import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { AlertStreamBanner } from './AlertStreamBanner'

class MockWebSocket {
  static instances: MockWebSocket[] = []
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  onclose: (() => void) | null = null
  sent: string[] = []

  constructor() {
    MockWebSocket.instances.push(this)
  }

  send(data: string) {
    this.sent.push(data)
  }

  close() {
    MockWebSocket.instances = MockWebSocket.instances.filter((i) => i !== this)
  }
}

describe('AlertStreamBanner', () => {
  beforeEach(() => {
    MockWebSocket.instances = []
    vi.stubGlobal('WebSocket', MockWebSocket)
    localStorage.setItem('token', 'test-token')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.removeItem('token')
  })

  it('renders connection status', () => {
    render(<AlertStreamBanner />)
    expect(screen.getByText(/实时告警/i)).toBeInTheDocument()
  })

  it('shows connected state after websocket opens', () => {
    render(<AlertStreamBanner />)
    const ws = MockWebSocket.instances[0]
    act(() => ws.onopen?.())
    expect(screen.getByText('实时告警已连接')).toBeInTheDocument()
  })

  it('displays incoming alert from websocket', () => {
    render(<AlertStreamBanner />)
    const ws = MockWebSocket.instances[0]
    act(() => ws.onopen?.())
    act(() =>
      ws.onmessage?.({
        data: JSON.stringify({
          id: 'alert_1',
          level: 'warning',
          title: '测试告警',
          message: '来自 WebSocket',
          timestamp: '2024-01-01T00:00:00Z',
          source: 'test',
        }),
      }),
    )
    expect(screen.getByText('测试告警')).toBeInTheDocument()
    expect(screen.getByText('来自 WebSocket')).toBeInTheDocument()
  })

  it('dismisses alert when clicking close', () => {
    render(<AlertStreamBanner />)
    const ws = MockWebSocket.instances[0]
    act(() => ws.onopen?.())
    act(() =>
      ws.onmessage?.({
        data: JSON.stringify({
          id: 'alert_2',
          level: 'info',
          title: '可关闭告警',
          message: '点击关闭',
          timestamp: '2024-01-01T00:00:00Z',
          source: 'test',
        }),
      }),
    )
    expect(screen.getByText('可关闭告警')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText(/关闭/i))
    expect(screen.queryByText('可关闭告警')).not.toBeInTheDocument()
  })
})
