import { usePlaygroundStore } from '../../stores/playgroundStore'
import { Link, Image, Type, Wand2 } from 'lucide-react'

export function ViralInputZone() {
  const { input, setInput, isParsing, parseError, setIsParsing, setParsed, setParseError } =
    usePlaygroundStore()

  const handleParse = async () => {
    if (!input.url && !input.text) return
    setIsParsing(true)
    setParseError(null)
    try {
      // TODO: replace with real API call
      await new Promise((r) => setTimeout(r, 800))
      setParsed({
        hook_pattern: '痛点反问式开场',
        body_structure: '问题描述 → 解决方案 → 使用体验 → 效果对比',
        cta_pattern: '引导评论互动 + 收藏暗示',
        tone: '亲切/专业',
        keywords: ['驱虫', '狗狗', '省钱', '养宠'],
      })
    } catch (e) {
      setParseError(e instanceof Error ? e.message : '解析失败')
    } finally {
      setIsParsing(false)
    }
  }

  return (
    <div className="bg-card rounded-xl border border-border p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Wand2 className="w-4 h-4 text-primary" />
        <h3 className="text-sm font-semibold">爆款输入</h3>
      </div>

      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="粘贴爆款笔记链接..."
            value={input.url || ''}
            onChange={(e) => setInput({ url: e.target.value })}
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-secondary text-sm outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <button
          className="px-3 py-2 rounded-lg bg-secondary text-sm text-muted-foreground hover:bg-primary/10 hover:text-primary transition-colors flex items-center gap-1.5"
          onClick={() => { /* trigger file upload */ }}
        >
          <Image className="w-4 h-4" />
          截图
        </button>
      </div>

      <div className="relative">
        <Type className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
        <textarea
          placeholder="或直接粘贴爆款文案内容..."
          value={input.text || ''}
          onChange={(e) => setInput({ text: e.target.value })}
          rows={3}
          className="w-full pl-9 pr-3 py-2 rounded-lg bg-secondary text-sm outline-none focus:ring-1 focus:ring-primary resize-none"
        />
      </div>

      {parseError && <p className="text-xs text-destructive">{parseError}</p>}

      <button
        onClick={handleParse}
        disabled={isParsing || (!input.url && !input.text)}
        className="w-full py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-40 transition-colors"
      >
        {isParsing ? '解析中...' : 'AI 结构解析'}
      </button>
    </div>
  )
}
