import { useRef, useEffect } from 'react'

export interface StepNodeCardProps {
  stepIndex: number
  isActive: boolean
  title: string
  icon: React.ReactNode
  summary: React.ReactNode
  onActivate: () => void
  onCollapse?: () => void
  children: React.ReactNode
}

export function StepNodeCard({
  stepIndex,
  isActive,
  title,
  icon,
  summary,
  onActivate,
  onCollapse,
  children,
}: StepNodeCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)

  // 激活时自动滚动到视野内
  useEffect(() => {
    if (isActive && cardRef.current && typeof cardRef.current.scrollIntoView === 'function') {
      cardRef.current.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
    }
  }, [isActive])

  return (
    <div
      ref={cardRef}
      onClick={(e) => {
        // 点击已展开节点的内部表单区域时不触发收起或切换
        if (isActive) {
          const target = e.target as HTMLElement
          if (cardRef.current?.contains(target) && target !== cardRef.current) {
            return
          }
          onCollapse?.()
          return
        }
        onActivate()
      }}
      className={`
        relative flex-shrink-0 rounded-[14px] border bg-card p-4
        transition-all duration-[350ms] ease-[cubic-bezier(0.4,0,0.2,1)]
        ${isActive
          ? 'w-full max-w-[520px] border-primary shadow-lg shadow-primary/10 ring-1 ring-primary cursor-default'
          : 'w-[240px] border-border shadow-sm cursor-pointer hover:border-primary/30'
        }
      `}
    >
      {/* 节点头部 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-5 h-5 rounded-md bg-primary/10 text-primary text-[11px] font-semibold flex items-center justify-center shrink-0">
            {stepIndex + 1}
          </span>
          <span className="text-sm font-semibold truncate">{title}</span>
          <span className="shrink-0 text-muted-foreground">{icon}</span>
        </div>
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${
            isActive ? 'bg-primary animate-pulse' : 'bg-muted-foreground/30'
          }`}
        />
      </div>

      {/* 折叠态：摘要 */}
      {!isActive && (
        <div className="text-xs text-muted-foreground space-y-1">
          {summary}
        </div>
      )}

      {/* 展开态：详情表单 */}
      {isActive && (
        <div
          className="border-t border-dashed border-border pt-3 mt-3 animate-fade-in"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="max-h-[calc(100vh-280px)] overflow-y-auto pr-1 -mr-1">
            {children}
          </div>
        </div>
      )}
    </div>
  )
}
