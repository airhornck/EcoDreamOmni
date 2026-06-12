import { create } from 'zustand'

export type LabCapability =
  | 'viral-analyzer'
  | 'title-optimizer'
  | 'cover-generator'
  | 'ab-test'
  | 'keyword-hotlist'

export interface LabCapabilityConfig {
  id: LabCapability
  name: string
  icon: string
  status: 'active' | 'locked'
  eta?: string
  description?: string
}

export const LAB_CAPABILITIES: LabCapabilityConfig[] = [
  {
    id: 'viral-analyzer',
    name: '爆款笔记分析',
    icon: '🔥',
    status: 'active',
    description: '粘贴爆款内容 → AI 深度分析 → 生成可复用模板',
  },
  {
    id: 'title-optimizer',
    name: '标题优化器',
    icon: '✍️',
    status: 'locked',
    eta: '2026-Q3',
    description: 'AI 驱动的标题 A/B 测试与优化建议',
  },
  {
    id: 'cover-generator',
    name: '封面生成器',
    icon: '🖼️',
    status: 'locked',
    eta: '2026-Q3',
    description: 'AI 封面设计与排版优化',
  },
  {
    id: 'ab-test',
    name: 'A/B 测试',
    icon: '🧪',
    status: 'locked',
    eta: '2026-Q4',
    description: '多版本内容效果预测与对比',
  },
  {
    id: 'keyword-hotlist',
    name: '关键词热榜',
    icon: '🎯',
    status: 'locked',
    eta: '2026-Q4',
    description: '实时热门关键词发现与追踪',
  },
]

interface LabState {
  activeCapability: LabCapability
  setActiveCapability: (cap: LabCapability) => void
}

export const useLabStore = create<LabState>((set) => ({
  activeCapability: 'viral-analyzer',
  setActiveCapability: (activeCapability) => set({ activeCapability }),
}))
