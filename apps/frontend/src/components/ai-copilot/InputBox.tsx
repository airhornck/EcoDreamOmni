import { useState, useRef, useCallback } from 'react'
import { Send, Square } from 'lucide-react'

interface InputBoxProps {
  onSend: (message: string) => void
  onAbort?: () => void
  status: 'idle' | 'thinking' | 'streaming' | 'completed' | 'error'
}

export function InputBox({ onSend, onAbort, status }: InputBoxProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const isBusy = status === 'thinking' || status === 'streaming'

  const handleSend = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || isBusy) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, isBusy, onSend])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    const target = e.currentTarget
    target.style.height = 'auto'
    target.style.height = `${Math.min(target.scrollHeight, 120)}px`
  }

  return (
    <div className="px-3 py-2 border-t border-border">
      <div className="relative flex items-end gap-2 bg-secondary rounded-lg px-3 py-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={isBusy ? 'AI 正在响应...' : '输入指令或问题...'}
          disabled={isBusy}
          rows={1}
          className="flex-1 bg-transparent resize-none outline-none text-sm min-h-[20px] max-h-[120px] py-0.5 disabled:opacity-50"
        />
        {isBusy ? (
          <button
            onClick={onAbort}
            className="p-1.5 rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors shrink-0"
            aria-label="停止生成"
          >
            <Square className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!value.trim()}
            className="p-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-30 disabled:hover:bg-primary transition-colors shrink-0"
            aria-label="发送"
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}
