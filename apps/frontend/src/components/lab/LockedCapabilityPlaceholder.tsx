import { Lock, Clock } from 'lucide-react'
import type { LabCapabilityConfig } from '../../stores/labStore'

interface LockedCapabilityPlaceholderProps {
  config: LabCapabilityConfig
}

const FEATURE_ROADMAP: Record<string, string[]> = {
  'title-optimizer': [
    '输入原始标题，AI 生成 5+ 个优化版本',
    '基于关键词热榜和点击率预测评分',
    '一键替换到内容生产流程',
  ],
  'cover-generator': [
    '根据笔记内容自动生成封面设计方案',
    '支持多平台尺寸（小红书 3:4 / 抖音 9:16）',
    '字体、配色、布局智能推荐',
  ],
  'ab-test': [
    '同时生成多个内容变体',
    '基于历史数据预测各版本互动表现',
    '自动推荐最优版本',
  ],
  'keyword-hotlist': [
    '跨平台热门关键词实时监控',
    '关键词热度趋势与竞争度分析',
    '智能推荐高潜力长尾词',
  ],
}

export function LockedCapabilityPlaceholder({ config }: LockedCapabilityPlaceholderProps) {
  const features = FEATURE_ROADMAP[config.id] || []

  return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="text-center space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-secondary flex items-center justify-center mx-auto">
          <Lock className="w-7 h-7 text-muted-foreground" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-foreground">{config.name}</h3>
          <p className="text-sm text-muted-foreground mt-1">{config.description}</p>
        </div>
        <div className="space-y-2 text-xs text-muted-foreground text-left inline-block">
          {features.map((feat, i) => (
            <p key={i}>• {feat}</p>
          ))}
        </div>
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-secondary text-muted-foreground text-xs">
          <Clock className="w-3 h-3" />
          预计 {config.eta} 上线
        </span>
      </div>
    </div>
  )
}
