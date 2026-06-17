import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Sparkles,
  ClipboardCheck,
  BarChart3,
  Users,
  Image,
  Bot,
  Brain,
  ClipboardList,
  BookOpen,
  Layers,
  Settings,
  type LucideIcon,
} from 'lucide-react'
import { UserMenuDropdown } from './UserMenuDropdown'

interface IconNavItem {
  path: string
  label: string
  icon: LucideIcon
}

const navItems: IconNavItem[] = [
  { path: '/', label: '工作台', icon: LayoutDashboard },
  { path: '/generate', label: '内容生产', icon: Sparkles },
  { path: '/review', label: '审核发布', icon: ClipboardCheck },
  { path: '/analytics', label: '数据报表', icon: BarChart3 },
  { path: '/accounts', label: '账号矩阵', icon: Users },
  { path: '/assets', label: '素材库', icon: Image },
  { path: '/agents', label: 'Agent 驾驶舱', icon: Bot },
  { path: '/models', label: 'AI 引擎', icon: Brain },
  { path: '/rules', label: '平台规则', icon: ClipboardList },
  { path: '/strategy-elements', label: '策略元素', icon: Layers },
  { path: '/lab', label: '实验室', icon: BookOpen },
  { path: '/settings', label: '设置', icon: Settings },
]

export function IconNav() {
  const location = useLocation()

  return (
    <nav
      className="h-screen w-12 bg-card border-r border-border flex flex-col items-center py-3 z-[100] relative group hover:w-[200px] transition-all duration-200 overflow-hidden flex-shrink-0"
      aria-label="主导航"
    >
      {/* Logo */}
      <div className="mb-4 flex items-center gap-2 px-3 w-full">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold text-sm flex-shrink-0">
          E
        </div>
        <span className="text-sm font-semibold text-foreground opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          EcoDream
        </span>
      </div>

      {/* Nav items */}
      <div className="flex-1 w-full space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive =
            location.pathname === item.path ||
            (item.path !== '/' && location.pathname.startsWith(item.path + '/'))
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`relative w-full flex items-center gap-3 px-3 py-2.5 transition-all ${
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                {item.label}
              </span>
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-5 bg-primary rounded-r-full" />
              )}
            </NavLink>
          )
        })}
      </div>

      {/* User avatar */}
      <div className="mt-auto w-full space-y-1 pb-2">
        <UserMenuDropdown
          trigger={
            <div className="w-full flex items-center gap-3 px-3 py-2.5 text-muted-foreground hover:text-foreground transition-all">
              <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center text-[10px] text-primary flex-shrink-0">
                U
              </div>
              <span className="text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                管理员
              </span>
            </div>
          }
          align="left"
          usePortal
        />
      </div>
    </nav>
  )
}
