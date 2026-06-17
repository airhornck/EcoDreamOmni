import { useLabStore, LAB_CAPABILITIES } from '../stores/labStore'
import { usePageCopilot } from '../hooks/usePageCopilot'
import { CapabilityNav } from '../components/lab/CapabilityNav'
import { ViralAnalyzerCapability } from '../components/lab/ViralAnalyzerCapability'
import { LockedCapabilityPlaceholder } from '../components/lab/LockedCapabilityPlaceholder'
import { PageHeader } from '../components/common/PageHeader'

export function LabPage() {
  const { activeCapability, setActiveCapability } = useLabStore()

  usePageCopilot(
    [
      {
        id: 'lab-viral',
        type: 'decision',
        title: '🔥 爆款笔记分析',
        description: '粘贴爆款内容，AI 拆解结构并生成可复用模板',
        priority: 1,
        actions: [{ id: 'open_viral_analyzer', label: '打开', variant: 'primary' }],
      },
      {
        id: 'lab-title',
        type: 'info',
        title: '✍️ 标题优化器',
        description: '标题 A/B 测试与优化（计划 2026-Q3 上线）',
        priority: 2,
        actions: [{ id: 'open_title_optimizer', label: '预览', variant: 'secondary' }],
      },
      {
        id: 'lab-cover',
        type: 'info',
        title: '🖼️ 封面生成器',
        description: 'AI 封面设计与排版优化（计划 2026-Q3 上线）',
        priority: 3,
        actions: [{ id: 'open_cover_generator', label: '预览', variant: 'secondary' }],
      },
      {
        id: 'lab-ab',
        type: 'info',
        title: '🧪 A/B 测试',
        description: '多版本内容效果预测与对比（计划 2026-Q4 上线）',
        priority: 4,
        actions: [{ id: 'open_ab_test', label: '预览', variant: 'secondary' }],
      },
    ],
    async (_cardId, actionId) => {
      switch (actionId) {
        case 'open_viral_analyzer':
          setActiveCapability('viral-analyzer')
          break
        case 'open_title_optimizer':
          setActiveCapability('title-optimizer')
          break
        case 'open_cover_generator':
          setActiveCapability('cover-generator')
          break
        case 'open_ab_test':
          setActiveCapability('ab-test')
          break
      }
    }
  )

  // ─── Render Active Capability ───
  const renderCapability = () => {
    switch (activeCapability) {
      case 'viral-analyzer':
        return <ViralAnalyzerCapability />
      default: {
        const config = LAB_CAPABILITIES.find((c) => c.id === activeCapability)
        if (config) {
          return <LockedCapabilityPlaceholder config={config} />
        }
        return null
      }
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Page Header */}
      <PageHeader
        title="实验室"
        subtitle="能力沙盒与验证中心"
      />

      {/* Capability Navigator */}
      <CapabilityNav />

      {/* Capability Canvas */}
      <div className="flex-1 overflow-y-auto p-5">
        {renderCapability()}
      </div>
    </div>
  )
}
