import { Card } from '../ui/Card'
import { cn } from '../../lib/utils'
import type { LucideIcon } from 'lucide-react'

export type StatVariant = 'default' | 'primary' | 'success' | 'warning' | 'danger'

interface StatCardProps {
  label: string
  value: string | number
  icon?: LucideIcon
  variant?: StatVariant
  className?: string
}

const iconColorStyles: Record<StatVariant, string> = {
  default: 'text-muted-foreground',
  primary: 'text-primary',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-red-600',
}

export function StatCard({ label, value, icon: Icon, variant = 'default', className }: StatCardProps) {
  return (
    <Card className={cn('p-4 text-center', className)}>
      {Icon && <Icon className={cn('w-5 h-5 mx-auto mb-2', iconColorStyles[variant])} />}
      <div className="text-2xl font-bold text-foreground tracking-tight">{value}</div>
      <div className="text-xs text-muted-foreground mt-1">{label}</div>
    </Card>
  )
}
