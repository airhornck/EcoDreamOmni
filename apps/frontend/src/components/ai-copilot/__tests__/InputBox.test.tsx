import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { InputBox } from '../InputBox'

describe('InputBox', () => {
  it('sends message on button click', () => {
    const onSend = vi.fn()
    render(<InputBox onSend={onSend} status="idle" />)

    const input = screen.getByPlaceholderText('输入指令或问题...')
    fireEvent.change(input, { target: { value: 'Hello AI' } })

    const sendBtn = screen.getByLabelText('发送')
    fireEvent.click(sendBtn)

    expect(onSend).toHaveBeenCalledWith('Hello AI')
  })

  it('sends message on Enter key', () => {
    const onSend = vi.fn()
    render(<InputBox onSend={onSend} status="idle" />)

    const input = screen.getByPlaceholderText('输入指令或问题...')
    fireEvent.change(input, { target: { value: 'Hello AI' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(onSend).toHaveBeenCalledWith('Hello AI')
  })

  it('shows abort button when busy', () => {
    const onAbort = vi.fn()
    render(<InputBox onSend={vi.fn()} onAbort={onAbort} status="thinking" />)

    const abortBtn = screen.getByLabelText('停止生成')
    fireEvent.click(abortBtn)

    expect(onAbort).toHaveBeenCalled()
  })

  it('disables send when empty', () => {
    const onSend = vi.fn()
    render(<InputBox onSend={onSend} status="idle" />)

    const sendBtn = screen.getByLabelText('发送')
    expect(sendBtn).toBeDisabled()
  })
})
