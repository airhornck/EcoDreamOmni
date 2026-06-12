import { useRef, useEffect } from 'react'
import { useAICopilotStore, type CopilotMessage } from '../../stores/aiCopilotStore'
import { User, Bot, Loader2 } from 'lucide-react'

export function MessageHistory() {
  const { messages, status, welcomeMessage } = useAICopilotStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  if (messages.length === 0) {
    return (
      <div className="shrink-0 h-32 flex items-center justify-center p-4">
        <div className="text-center space-y-2">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
            <Bot className="w-5 h-5 text-primary" />
          </div>
          <p className="text-sm text-muted-foreground">{welcomeMessage || '有什么可以帮你的？'}</p>
          <p className="text-xs text-muted-foreground">AI Copilot 可协助内容生成、数据分析和任务执行</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 min-h-0 max-h-[55%] overflow-y-auto p-3 space-y-3">
      {messages.map((msg) => (
        <MessageItem key={msg.id} message={msg} />
      ))}
      {status === 'thinking' && <ThinkingIndicator />}
      <div ref={bottomRef} />
    </div>
  )
}

function MessageItem({ message }: { message: CopilotMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div
        className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
          isUser ? 'bg-secondary' : 'bg-primary/10'
        }`}
      >
        {isUser ? (
          <User className="w-3.5 h-3.5 text-muted-foreground" />
        ) : (
          <Bot className="w-3.5 h-3.5 text-primary" />
        )}
      </div>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-secondary text-foreground'
        }`}
      >
        {message.content || (message.role === 'assistant' ? <span className="animate-pulse">▋</span> : null)}
      </div>
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div className="flex gap-2">
      <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
        <Loader2 className="w-3.5 h-3.5 text-primary animate-spin" />
      </div>
      <div className="bg-secondary rounded-lg px-3 py-2 text-sm text-muted-foreground">
        AI 思考中...
      </div>
    </div>
  )
}
