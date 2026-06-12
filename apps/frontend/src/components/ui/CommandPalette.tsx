import { cn } from '../../lib/utils'
import { Search } from 'lucide-react'
import {
  useState,
  useEffect,
  useRef,
  type ReactNode,
  type KeyboardEvent,
} from 'react'

export interface CommandItem {
  id: string
  label: string
  description?: string
  icon?: ReactNode
  shortcut?: string
  group?: string
  onSelect?: () => void
}

export interface CommandPaletteProps {
  commands: CommandItem[]
  open: boolean
  onOpenChange: (open: boolean) => void
  placeholder?: string
  footer?: ReactNode
}

export function CommandPalette({
  commands,
  open,
  onOpenChange,
  placeholder = '搜索命令、页面、快捷操作...',
  footer,
}: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const filtered = commands.filter(
    (cmd) =>
      cmd.label.toLowerCase().includes(query.toLowerCase()) ||
      (cmd.description?.toLowerCase().includes(query.toLowerCase()) ?? false)
  )

  const grouped = filtered.reduce<Record<string, CommandItem[]>>((acc, cmd) => {
    const group = cmd.group || '其他'
    if (!acc[group]) acc[group] = []
    acc[group].push(cmd)
    return acc
  }, {})

  const flatItems = Object.values(grouped).flat()

  // Reset state when opened
  useEffect(() => {
    if (open) {
      const id = requestAnimationFrame(() => {
        setQuery('')
        setActiveIndex(0)
      })
      const timer = setTimeout(() => inputRef.current?.focus(), 50)
      return () => {
        cancelAnimationFrame(id)
        clearTimeout(timer)
      }
    }
  }, [open])

  // Reset active index when query changes
  useEffect(() => {
    const id = requestAnimationFrame(() => setActiveIndex(0))
    return () => cancelAnimationFrame(id)
  }, [query])

  // Scroll active item into view
  useEffect(() => {
    const activeEl = listRef.current?.querySelector('[data-active="true"]')
    if (activeEl && typeof activeEl.scrollIntoView === 'function') {
      activeEl.scrollIntoView({ block: 'nearest' })
    }
  }, [activeIndex])

  // Global Ctrl+K shortcut
  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        onOpenChange(!open)
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onOpenChange])

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((prev) => (prev + 1) % flatItems.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((prev) => (prev - 1 + flatItems.length) % flatItems.length)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const item = flatItems[activeIndex]
      if (item?.onSelect) {
        item.onSelect()
        onOpenChange(false)
      }
    } else if (e.key === 'Escape') {
      onOpenChange(false)
    }
  }

  if (!open) return null

  let globalIndex = 0

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50"
        onClick={() => onOpenChange(false)}
      />
      {/* Palette */}
      <div className="fixed top-[20%] left-1/2 -translate-x-1/2 w-[640px] max-w-[90vw] bg-popover rounded-2xl shadow-xl border border-border z-50 overflow-hidden flex flex-col max-h-[70vh]">
        {/* Search */}
        <div className="flex items-center gap-2 p-3 border-b border-border">
          <Search className="w-5 h-5 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="flex-1 text-sm outline-none bg-transparent text-foreground placeholder:text-muted-foreground"
          />
          <kbd className="px-2 py-0.5 rounded text-[10px] font-mono bg-secondary text-muted-foreground border border-border">
            ESC
          </kbd>
        </div>
        {/* List */}
        <div ref={listRef} className="overflow-y-auto py-1 flex-1">
          {flatItems.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              没有找到匹配命令
            </div>
          ) : (
            Object.entries(grouped).map(([groupName, items]) => (
              <div key={groupName}>
                <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {groupName}
                </div>
                {items.map((item) => {
                  const isActive = globalIndex === activeIndex
                  const currentIndex = globalIndex++
                  return (
                    <button
                      key={item.id}
                      data-active={isActive}
                      className={cn(
                        'w-full px-3 py-2.5 flex items-center gap-3 mx-2 rounded-lg text-left transition-colors',
                        isActive ? 'bg-primary/6' : 'hover:bg-secondary'
                      )}
                      onClick={() => {
                        item.onSelect?.()
                        onOpenChange(false)
                      }}
                      onMouseEnter={() => setActiveIndex(currentIndex)}
                    >
                      {item.icon && <span className="w-5 text-center">{item.icon}</span>}
                      <div className="flex-1 min-w-0">
                        <div
                          className={cn(
                            'text-sm font-medium',
                            isActive ? 'text-primary' : 'text-foreground'
                          )}
                        >
                          {item.label}
                        </div>
                        {item.description && (
                          <div className="text-xs text-muted-foreground">{item.description}</div>
                        )}
                      </div>
                      {item.shortcut && (
                        <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-secondary text-muted-foreground border border-border whitespace-nowrap">
                          {item.shortcut}
                        </kbd>
                      )}
                    </button>
                  )
                })}
              </div>
            ))
          )}
        </div>
        {/* Footer */}
        <div className="flex items-center justify-between px-3 py-2 border-t border-border text-[10px] text-muted-foreground">
          <div className="flex gap-3">
            <span>↑↓ 导航</span>
            <span>↵ 选择</span>
            <span>ESC 关闭</span>
          </div>
          {footer ?? <span>v4.0</span>}
        </div>
      </div>
    </>
  )
}
