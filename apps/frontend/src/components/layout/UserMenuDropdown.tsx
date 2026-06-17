import { useState, useRef, useEffect, useLayoutEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { createPortal } from 'react-dom'
import { LogOut, Settings, UserCircle } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'

const MENU_WIDTH = 224 // w-56

interface UserMenuDropdownProps {
  /** 触发下拉菜单的按钮内容 */
  trigger: React.ReactNode
  /** 菜单水平对齐方式：right 表示与 trigger 右对齐，left 表示左对齐 */
  align?: 'left' | 'right'
  /**
   * 是否使用 Portal + fixed 定位渲染菜单。
   * 当 trigger 位于 overflow-hidden 容器（如 IconNav）内部时应设为 true，
   * 以避免菜单被父容器裁剪。
   */
  usePortal?: boolean
  /** 菜单打开状态变化回调 */
  onOpenChange?: (open: boolean) => void
}

export function UserMenuDropdown({
  trigger,
  align = 'right',
  usePortal = false,
  onOpenChange,
}: UserMenuDropdownProps) {
  const [open, setOpenState] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const setOpen = useCallback((next: boolean) => {
    setOpenState(next)
    onOpenChange?.(next)
  }, [onOpenChange])

  useLayoutEffect(() => {
    if (open && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      const top = rect.bottom + 8
      const left = align === 'right' ? rect.right - MENU_WIDTH : rect.left
      setPosition({ top, left })
    }
  }, [open, align])

  useEffect(() => {
    if (!open) return

    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node
      const clickedTrigger = triggerRef.current?.contains(target) ?? false
      const clickedMenu = menuRef.current?.contains(target) ?? false
      if (!clickedTrigger && !clickedMenu) {
        setOpen(false)
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [open, setOpen])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const handleNavigate = (path: string) => {
    navigate(path)
    setOpen(false)
  }

  const avatarLetter = user?.username?.[0]?.toUpperCase() ?? 'U'
  const avatarUrl = user?.avatar
  const displayName = user?.username ?? '用户'
  const displayEmail = user?.email ?? ''

  const menu = (
    <div
      ref={menuRef}
      data-testid="user-menu-dropdown"
      className={
        "w-56 rounded-lg border border-border bg-card shadow-lg py-1 " +
        (usePortal
          ? ""
          : "absolute right-0 top-full mt-2 z-50")
      }
      style={
        usePortal
          ? { position: 'fixed', top: position.top, left: position.left, zIndex: 200 }
          : undefined
      }
    >
      <div className="px-3 py-2 border-b border-border" data-testid="user-menu-header">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-medium flex-shrink-0 overflow-hidden">
            {avatarUrl ? (
              <img src={avatarUrl} alt="" className="w-full h-full object-cover" />
            ) : (
              avatarLetter
            )}
          </div>
          <div className="flex flex-col min-w-0">
            <span data-testid="user-menu-username" className="text-sm font-medium truncate">{displayName}</span>
            {displayEmail && (
              <span data-testid="user-menu-email" className="text-xs text-muted-foreground truncate">{displayEmail}</span>
            )}
          </div>
        </div>
        {user?.role && (
          <span data-testid="user-menu-role" className="mt-1.5 inline-flex items-center rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium text-secondary-foreground">
            {user.role}
          </span>
        )}
      </div>

      <button
        type="button"
        data-testid="user-menu-profile"
        onClick={() => handleNavigate('/settings/profile')}
        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-secondary transition-colors"
      >
        <UserCircle className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        个人信息
      </button>

      <button
        type="button"
        data-testid="user-menu-settings"
        onClick={() => handleNavigate('/settings')}
        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-secondary transition-colors"
      >
        <Settings className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        系统设置
      </button>

      <div className="h-px bg-border my-1" />

      <button
        type="button"
        data-testid="user-menu-logout"
        onClick={handleLogout}
        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
      >
        <LogOut className="w-4 h-4 flex-shrink-0" />
        登出
      </button>
    </div>
  )

  return (
    <div className={usePortal ? undefined : 'relative'}>
      <button
        ref={triggerRef}
        type="button"
        data-testid="user-menu-trigger"
        onClick={() => setOpen(!open)}
        className="inline-flex items-center"
      >
        {trigger}
      </button>
      {open && (usePortal ? createPortal(menu, document.body) : menu)}
    </div>
  )
}
