import { Lock, Plus } from 'lucide-react'
import { useLabStore, LAB_CAPABILITIES } from '../../stores/labStore'

export function CapabilityNav() {
  const { activeCapability, setActiveCapability } = useLabStore()

  return (
    <div className="shrink-0 border-b border-border bg-secondary/30">
      <div className="px-5 py-2.5 flex items-center gap-2 overflow-x-auto">
        <span className="text-[11px] text-muted-foreground font-medium mr-1 shrink-0">能力:</span>
        {LAB_CAPABILITIES.map((cap) => {
          const isActive = activeCapability === cap.id
          const isLocked = cap.status === 'locked'

          if (isLocked) {
            return (
              <button
                key={cap.id}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-muted-foreground bg-card border border-border whitespace-nowrap opacity-45 cursor-not-allowed"
                title={`即将上线 · ${cap.eta}`}
              >
                <span>{cap.icon}</span>
                <span>{cap.name}</span>
                <Lock className="w-3 h-3" />
              </button>
            )
          }

          return (
            <button
              key={cap.id}
              onClick={() => setActiveCapability(cap.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-primary text-white shadow-[0_1px_4px_rgba(124,58,237,0.25)]'
                  : 'text-muted-foreground hover:bg-secondary'
              }`}
            >
              <span>{cap.icon}</span>
              <span>{cap.name}</span>
              {isActive && <span className="w-1.5 h-1.5 bg-white/70 rounded-full ml-0.5" />}
            </button>
          )
        })}

        <div className="w-px h-4 bg-border mx-1 shrink-0" />
        <button
          className="flex items-center gap-1 px-2 py-1 rounded-full text-[11px] text-muted-foreground hover:text-primary hover:bg-primary/5 transition-colors whitespace-nowrap"
          title="提交新能力需求"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>提交需求</span>
        </button>
      </div>
    </div>
  )
}
