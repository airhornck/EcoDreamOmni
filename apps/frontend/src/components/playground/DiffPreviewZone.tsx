import { usePlaygroundStore } from '../../stores/playgroundStore'
import { GitCompare, Check } from 'lucide-react'

export function DiffPreviewZone() {
  const { generated, isGenerating } = usePlaygroundStore()

  return (
    <div className="bg-card rounded-xl border border-border p-4 space-y-3 h-full flex flex-col">
      <div className="flex items-center gap-2">
        <GitCompare className="w-4 h-4 text-primary" />
        <h3 className="text-sm font-semibold">对比预览</h3>
      </div>

      {isGenerating ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-2">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm text-muted-foreground">生成中...</p>
          </div>
        </div>
      ) : !generated ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-muted-foreground">点击「一键生成」查看预览</p>
        </div>
      ) : (
        <div className="flex-1 space-y-3 overflow-y-auto">
          <div>
            <span className="text-xs text-muted-foreground block mb-1">标题</span>
            <p className="text-sm font-medium">{generated.title}</p>
          </div>

          <div>
            <span className="text-xs text-muted-foreground block mb-1">正文</span>
            <div className="p-2.5 rounded-lg bg-secondary text-sm leading-relaxed whitespace-pre-wrap">
              {generated.body}
            </div>
          </div>

          {generated.hashtags.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground block mb-1">话题标签</span>
              <div className="flex flex-wrap gap-1">
                {generated.hashtags.map((tag) => (
                  <span key={tag} className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs">
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center gap-1.5 pt-2 border-t border-border">
            <Check className="w-3.5 h-3.5 text-success" />
            <span className="text-xs text-success">生成完成</span>
          </div>
        </div>
      )}
    </div>
  )
}
