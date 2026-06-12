import { useLabStore, LAB_CAPABILITIES } from '../stores/labStore'
import { CapabilityNav } from '../components/lab/CapabilityNav'
import { ViralAnalyzerCapability } from '../components/lab/ViralAnalyzerCapability'
import { LockedCapabilityPlaceholder } from '../components/lab/LockedCapabilityPlaceholder'
import { PageHeader } from '../components/common/PageHeader'

export function LabPage() {
  const { activeCapability } = useLabStore()

  // 上下文由 LayoutWrapper 的 useCopilotPageSync 统一注入，此处无需手动设置。

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
