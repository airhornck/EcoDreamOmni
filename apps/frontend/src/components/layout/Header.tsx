import { Bell, User, PanelRightClose, PanelRightOpen } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { useAICopilotStore } from '../../stores/aiCopilotStore'

export function Header() {
  const { user } = useAuthStore()
  const { isOpen, toggle } = useAICopilotStore()

  return (
    <header className="h-14 bg-card/80 backdrop-blur border-b border-border flex items-center justify-between px-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span className="text-foreground font-medium">EcoDreamOmni</span>
        <span>/</span>
        <span>运营中心</span>
      </div>

      <div className="flex items-center gap-3">
        {/* AI Copilot Toggle Button */}
        <button
          onClick={toggle}
          className={
            isOpen
              ? "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-primary/30 bg-primary/10 text-primary transition-colors"
              : "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-border text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
          }
          aria-label={isOpen ? '关闭 AI Copilot' : '打开 AI Copilot'}
        >
          {isOpen ? <PanelRightClose className="w-3.5 h-3.5" /> : <PanelRightOpen className="w-3.5 h-3.5" />}
          <span>AI Copilot</span>
        </button>

        <button className="relative p-2 rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full" />
        </button>
        <div className="flex items-center gap-2 pl-3 border-l border-border">
          <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-primary" />
          </div>
          <span className="text-sm text-foreground hidden sm:inline">
            {user?.username ?? '用户'}
          </span>
        </div>
      </div>
    </header>
  )
}
