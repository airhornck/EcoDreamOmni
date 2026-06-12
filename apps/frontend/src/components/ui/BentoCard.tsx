import { cn } from '../../lib/utils'
import type { ReactNode } from 'react'

type BentoSize = 'small' | 'wide' | 'large' | 'full'

interface BentoCardProps {
  size: BentoSize
  aiHighlight?: boolean
  children: ReactNode
  className?: string
  title?: string
  badge?: ReactNode
  [key: string]: unknown
}

const sizeClasses: Record<BentoSize, string> = {
  small: 'col-span-1 aspect-square',
  wide: 'col-span-2 aspect-[2/1]',
  large: 'col-span-2 row-span-2',
  full: 'col-span-4',
}

const responsiveClasses: Record<BentoSize, string> = {
  small: 'md:col-span-1 col-span-2',
  wide: 'md:col-span-2 col-span-2',
  large: 'md:col-span-2 md:row-span-2 col-span-2 row-span-2',
  full: 'md:col-span-4 col-span-2',
}

export function BentoCard({
  size,
  aiHighlight = false,
  children,
  className,
  title,
  badge,
  ...props
}: BentoCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border bg-card p-4 flex flex-col',
        sizeClasses[size],
        responsiveClasses[size],
        aiHighlight && 'animate-pulse-glow',
        !aiHighlight && 'card-hover',
        className
      )}
      {...props}
    >
      {(title || badge) && (
        <div className="flex items-center justify-between mb-3">
          {title && (
            <span className="text-sm font-medium text-foreground">{title}</span>
          )}
          {badge && <div>{badge}</div>}
        </div>
      )}
      <div className="flex-1 min-h-0">{children}</div>
    </div>
  )
}

interface BentoGridProps {
  children: ReactNode
  className?: string
  [key: string]: unknown
}

export function BentoGrid({ children, className, ...props }: BentoGridProps) {
  return (
    <div
      className={cn(
        'grid grid-cols-2 md:grid-cols-4 gap-4',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
